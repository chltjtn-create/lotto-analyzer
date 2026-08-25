"""End-to-end weekly Lotto update workflow."""

from __future__ import annotations

import json
import os
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from lotto_analyzer.analysis.evaluation import RecommendationEvaluation, RecommendationRecord, evaluate_recommendation
from lotto_analyzer.analysis.frequency import analyze_number_frequency
from lotto_analyzer.analysis.pattern import analyze_patterns
from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.collector import LottoCrawler, LottoCrawlerError
from lotto_analyzer.collector.crawler import estimate_latest_draw_no
from lotto_analyzer.config import BASE_DIR, LOG_DIR, ensure_project_directories
from lotto_analyzer.database import LottoDatabaseManager
from lotto_analyzer.generator import CombinationConstraints, GeneratedCombination, generate_combinations
from lotto_analyzer.report import ChartExportError, export_all_charts, export_excel_report

DISCLAIMER = "본 결과는 통계 분석 기반 참고자료이며\n당첨을 보장하지 않습니다."

# Per-step wall-clock limits (seconds). A step that exceeds its limit is abandoned
# so the run can still finish and record the problem in its log.
STEP_TIMEOUTS = {
    "collect": 300,
    "backup": 120,
    "analyze": 180,
    "charts": 180,
    "excel": 300,
}


class StepTimeoutError(Exception):
    """Raised when one workflow step exceeds its wall-clock limit."""


class RunLogger:
    """Append-only step log flushed to disk immediately after every line.

    The weekly job runs unattended under Windows Task Scheduler. If the process is
    killed (for example by ExecutionTimeLimit) nothing buffered survives, so every
    line is flushed and fsynced as soon as it is written.
    """

    def __init__(self, started_at: datetime) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.path = LOG_DIR / f"weekly_run_{started_at.strftime('%Y%m%d_%H%M%S')}.log"
        self._lock = threading.Lock()
        self.write(f"RUN START pid={os.getpid()} base={BASE_DIR}")

    def write(self, message: str) -> None:
        """Write one timestamped line and force it to disk."""
        line = f"{datetime.now().isoformat(timespec='seconds')} | {message}\n"
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
        print(line.rstrip(), flush=True)


def _run_step(logger: RunLogger, name: str, func, timeout: float | None = None):
    """Run one workflow step with logging and a wall-clock limit.

    The worker runs in a daemon thread so a hung third-party call (matplotlib font
    scan, network fetch, synced-folder write) cannot pin the whole run forever.
    """
    limit = timeout if timeout is not None else STEP_TIMEOUTS.get(name)
    logger.write(f"STEP START {name} (timeout={limit}s)")
    started = datetime.now()
    box: dict[str, object] = {}

    def worker() -> None:
        try:
            box["value"] = func()
        except BaseException as exc:  # noqa: BLE001 - re-raised on the calling thread
            box["error"] = exc

    thread = threading.Thread(target=worker, name=f"step-{name}", daemon=True)
    thread.start()
    thread.join(limit)
    elapsed = (datetime.now() - started).total_seconds()

    if thread.is_alive():
        logger.write(f"STEP TIMEOUT {name} after {elapsed:.1f}s")
        raise StepTimeoutError(f"Step '{name}' exceeded {limit}s and was abandoned.")
    if "error" in box:
        error = box["error"]
        logger.write(f"STEP FAIL {name} after {elapsed:.1f}s: {type(error).__name__}: {error}")
        raise error
    logger.write(f"STEP OK {name} in {elapsed:.1f}s")
    return box.get("value")


@dataclass(slots=True)
class WeeklyUpdateResult:
    """Store the outcome of one weekly automation run."""

    started_at: datetime
    finished_at: datetime | None = None
    latest_before: int | None = None
    latest_after: int | None = None
    fetched_draws: list[int] = field(default_factory=list)
    evaluated_recommendations: int = 0
    generated_recommendations: int = 0
    report_path: Path | None = None
    chart_paths: list[Path] = field(default_factory=list)
    csv_path: Path | None = None
    json_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    step_log_path: Path | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert the result to a JSON-friendly dictionary."""
        return {
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "finished_at": self.finished_at.isoformat(timespec="seconds") if self.finished_at else None,
            "latest_before": self.latest_before,
            "latest_after": self.latest_after,
            "fetched_draws": self.fetched_draws,
            "evaluated_recommendations": self.evaluated_recommendations,
            "generated_recommendations": self.generated_recommendations,
            "report_path": str(self.report_path) if self.report_path else None,
            "chart_paths": [str(path) for path in self.chart_paths],
            "csv_path": str(self.csv_path) if self.csv_path else None,
            "json_path": str(self.json_path) if self.json_path else None,
            "step_log_path": str(self.step_log_path) if self.step_log_path else None,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def run_weekly_update(
    recommendation_count: int | None = None,
    strategy: str | None = None,
) -> WeeklyUpdateResult:
    """Run collection, backup, analysis, recommendation, and report workflow."""
    load_dotenv(BASE_DIR / ".env")
    ensure_project_directories()

    result = WeeklyUpdateResult(started_at=datetime.now())
    logger = RunLogger(result.started_at)
    result.step_log_path = logger.path
    database = LottoDatabaseManager()
    crawler = LottoCrawler()

    try:
        database.initialize_database()
        result.latest_before = database.get_latest_draw_no()
        logger.write(f"latest_before={result.latest_before}")

        new_draws = _run_step(logger, "collect", lambda: _fetch_new_draws(database, crawler, result))
        if new_draws:
            database.save_draws(new_draws)
            logger.write(f"saved draws: {result.fetched_draws}")

        csv_path, json_path = _run_step(logger, "backup", database.export_backups)
        result.csv_path = csv_path
        result.json_path = json_path
        result.latest_after = database.get_latest_draw_no()
        logger.write(f"latest_after={result.latest_after}")

        draws = database.list_draws()
        if not draws:
            raise RuntimeError("No draw data is available after update.")

        evaluations = _run_step(logger, "evaluate", lambda: _evaluate_due_recommendations(database, draws), 120)
        result.evaluated_recommendations = len(evaluations)

        generated_records = _run_step(
            logger,
            "recommend",
            lambda: _generate_next_recommendations(
                database,
                draws,
                recommendation_count or int(os.getenv("LOTTO_RECOMMENDATION_COUNT", "5")),
                strategy or os.getenv("LOTTO_RECOMMENDATION_STRATEGY", "Hybrid"),
            ),
            180,
        )
        result.generated_recommendations = len(generated_records)

        stats, patterns, scores = _run_step(
            logger,
            "analyze",
            lambda: (analyze_number_frequency(draws), analyze_patterns(draws), calculate_number_scores(draws)),
        )

        # Charts and the Excel report are presentation only. A failure here must not
        # cost us the run log, so each is isolated.
        try:
            result.chart_paths = _run_step(logger, "charts", lambda: export_all_charts(stats, scores, patterns))
        except (ChartExportError, StepTimeoutError, Exception) as exc:
            result.warnings.append(f"Chart export skipped: {type(exc).__name__}: {exc}")

        try:
            result.report_path = _run_step(
                logger,
                "excel",
                lambda: export_excel_report(
                    draws,
                    stats,
                    patterns,
                    scores,
                    recommendations=database.list_recommendations(),
                    evaluations=database.list_evaluations(),
                ),
            )
        except Exception as exc:  # noqa: BLE001 - report is optional, run must finish
            result.warnings.append(f"Excel report skipped: {type(exc).__name__}: {exc}")

    except Exception as exc:
        logger.write(f"RUN ERROR {type(exc).__name__}: {exc}")
        result.errors.append(f"{type(exc).__name__}: {exc}")
        result.errors.append(traceback.format_exc())
    finally:
        result.finished_at = datetime.now()
        log_path = _write_run_log(result)
        logger.write(f"RUN END errors={len(result.errors)} warnings={len(result.warnings)} json={log_path}")

    return result


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE pairs from a local .env file without extra dependencies."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _fetch_new_draws(
    database: LottoDatabaseManager,
    crawler: LottoCrawler,
    result: WeeklyUpdateResult,
) -> list:
    """Fetch draw numbers that are newer than the current database."""
    latest_stored = database.get_latest_draw_no() or 0
    estimated_latest = estimate_latest_draw_no()
    new_draws = []

    for draw_no in range(latest_stored + 1, estimated_latest + 1):
        try:
            draw = crawler.fetch_draw(draw_no)
        except LottoCrawlerError as exc:
            result.warnings.append(f"Could not fetch draw {draw_no}: {exc}")
            break
        new_draws.append(draw)
        result.fetched_draws.append(draw.draw_no)

    if not new_draws and latest_stored >= estimated_latest:
        result.warnings.append("No new draw is expected yet based on the calendar.")
    return new_draws


def _evaluate_due_recommendations(
    database: LottoDatabaseManager,
    draws: list,
) -> list[RecommendationEvaluation]:
    """Evaluate saved recommendations whose target draw is already stored."""
    draw_by_no = {draw.draw_no: draw for draw in draws}
    existing_ids = {evaluation.recommendation_id for evaluation in database.list_evaluations()}
    evaluations = []
    for record in database.list_recommendations():
        if record.recommendation_id in existing_ids:
            continue
        actual_draw = draw_by_no.get(record.target_draw_no)
        if actual_draw is None:
            continue
        evaluations.append(evaluate_recommendation(record, actual_draw))
    database.save_evaluations(evaluations)
    return evaluations


def _generate_next_recommendations(
    database: LottoDatabaseManager,
    draws: list,
    count: int,
    strategy: str,
) -> list[RecommendationRecord]:
    """Generate and save recommendations for the next draw after the current latest."""
    latest_draw = draws[-1]
    target_draw_no = latest_draw.draw_no + 1
    existing = database.list_recommendations(target_draw_no)
    if existing:
        return existing

    scores = calculate_number_scores(draws)
    combinations = generate_combinations(
        scores,
        latest_draw=latest_draw,
        constraints=CombinationConstraints(exclude_latest_draw_numbers=True),
        strategy=strategy,
        count=count,
        excluded_combinations=[draw.numbers for draw in draws],
    )
    records = [
        RecommendationRecord(
            recommendation_id=_recommendation_id(target_draw_no, strategy, index),
            target_draw_no=target_draw_no,
            created_date=datetime.now().date(),
            combination=combination,
        )
        for index, combination in enumerate(combinations, start=1)
    ]
    database.save_recommendations(records)
    return records


def _write_run_log(result: WeeklyUpdateResult) -> Path:
    """Write a JSON run log for traceability."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"weekly_update_{result.started_at.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _recommendation_id(target_draw_no: int, strategy: str, index: int) -> str:
    """Build a stable recommendation id for one target draw and strategy."""
    strategy_key = strategy.lower().replace(" ", "_")
    return f"{target_draw_no}-{strategy_key}-{index:03d}"
