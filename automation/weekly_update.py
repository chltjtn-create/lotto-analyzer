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
from lotto_analyzer.report import ChartExportError, build_weekly_email_html, export_all_charts, export_excel_report

from lotto_analyzer.automation.email_sender import EmailConfigError, EmailSettings, send_email_report

DISCLAIMER = "본 결과는 통계 분석 기반 참고자료이며\n당첨을 보장하지 않습니다."

# Per-step wall-clock limits (seconds). A step that exceeds its limit is abandoned
# so the run can still finish, write its log, and report the problem by email.
STEP_TIMEOUTS = {
    "collect": 300,
    "backup": 120,
    "analyze": 180,
    "charts": 180,
    "excel": 300,
    "email": 180,
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
    scan, SMTP socket, synced-folder write) cannot pin the whole run forever.
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
    email_sent: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    html_body: str | None = None
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
            "email_sent": self.email_sent,
            "step_log_path": str(self.step_log_path) if self.step_log_path else None,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def run_weekly_update(
    recommendation_count: int | None = None,
    strategy: str | None = None,
    send_mail: bool = True,
) -> WeeklyUpdateResult:
    """Run collection, backup, analysis, recommendation, report, and email workflow."""
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
        # cost us the run log or the email, so each is isolated.
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

        latest_draw = draws[-1]
        latest_evaluations = [
            evaluation
            for evaluation in database.list_evaluations()
            if evaluation.target_draw_no == latest_draw.draw_no
        ]
        result.html_body = build_weekly_email_html(
            latest_draw=latest_draw,
            evaluations=latest_evaluations,
            next_target_draw_no=latest_draw.draw_no + 1,
            next_recommendations=generated_records,
        )

        if send_mail:
            _run_step(logger, "email", lambda: _send_weekly_email(result))
    except Exception as exc:
        logger.write(f"RUN ERROR {type(exc).__name__}: {exc}")
        result.errors.append(f"{type(exc).__name__}: {exc}")
        result.errors.append(traceback.format_exc())
        try:
            if send_mail:
                _run_step(logger, "email", lambda: _send_weekly_email(result))
        except Exception as mail_exc:
            result.warnings.append(f"Failure email skipped: {mail_exc}")
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


def _send_weekly_email(result: WeeklyUpdateResult) -> None:
    """Send a weekly summary email when SMTP settings are configured."""
    settings = EmailSettings.from_environment()
    if not settings.enabled:
        result.warnings.append("Email delivery skipped because LOTTO_EMAIL_ENABLED is false.")
        return

    subject = _email_subject(result)
    body = _email_body(result)
    attachments = [path for path in [result.report_path, result.csv_path, result.json_path] if path]
    send_email_report(subject, body, attachments, settings, html_body=result.html_body)
    result.email_sent = True


def _email_subject(result: WeeklyUpdateResult) -> str:
    """Build the weekly email subject."""
    status = "성공" if not result.errors else "확인 필요"
    latest = result.latest_after or result.latest_before or "미확인"
    return f"[로또 자동분석] {status} - 최신 {latest}회"


def _email_body(result: WeeklyUpdateResult) -> str:
    """Build the weekly email body."""
    lines = [
        "로또 6/45 주간 자동 분석 결과입니다.",
        "",
        f"시작: {result.started_at.isoformat(timespec='seconds')}",
        f"종료: {result.finished_at.isoformat(timespec='seconds') if result.finished_at else '진행 중'}",
        f"기존 최신 회차: {result.latest_before}",
        f"갱신 후 최신 회차: {result.latest_after}",
        f"새로 저장한 회차: {result.fetched_draws or '없음'}",
        f"평가한 추천 조합: {result.evaluated_recommendations}건",
        f"새 추천 조합: {result.generated_recommendations}건",
        f"엑셀 리포트: {result.report_path}",
        f"단계 로그: {result.step_log_path}",
        "",
        DISCLAIMER,
    ]
    if result.warnings:
        lines.extend(["", "주의/알림:", *[f"- {warning}" for warning in result.warnings]])
    if result.errors:
        lines.extend(["", "오류:", *[f"- {error}" for error in result.errors[:2]]])
    return "\n".join(lines)


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
