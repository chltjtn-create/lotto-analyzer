"""Command line entry point for the Lotto analyzer."""

from __future__ import annotations

import argparse
import json
from datetime import date
from typing import Sequence

from lotto_analyzer.analysis.backtest import BacktestError, run_backtest
from lotto_analyzer.analysis.evaluation import evaluate_recommendation
from lotto_analyzer.analysis.frequency import (
    FrequencyAnalysisError,
    analyze_number_frequency,
    format_number_stats,
    stats_to_rows,
)
from lotto_analyzer.analysis.pattern import PatternAnalysisError, analyze_patterns
from lotto_analyzer.analysis.scoring import (
    ScoringError,
    calculate_number_scores,
    category_groups,
    score_rows,
)
from lotto_analyzer.collector import LottoCrawler, LottoCrawlerError
from lotto_analyzer.collector.local_loader import LocalDataLoadError, load_draws_from_excel
from lotto_analyzer.config import DEFAULT_LOCAL_EXCEL_PATH, ensure_project_directories
from lotto_analyzer.database import LottoDatabaseError, LottoDatabaseManager
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator import (
    CombinationConstraints,
    CombinationGenerationError,
    generate_combinations,
)
from lotto_analyzer.analysis.evaluation import RecommendationRecord
from lotto_analyzer.report import (
    ChartExportError,
    ExcelExportError,
    export_all_charts,
    export_excel_report,
)


def draw_to_pretty_json(draw: LottoDraw) -> str:
    """Serialize one draw as formatted JSON for command line output."""
    return json.dumps(draw.to_dict(), ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser for collection and storage commands."""
    parser = argparse.ArgumentParser(description="Lotto 6/45 analysis tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create the SQLite database schema")

    import_excel_parser = subparsers.add_parser(
        "import-excel",
        help="Import local Excel draw data into SQLite",
    )
    import_excel_parser.add_argument(
        "path",
        nargs="?",
        default=str(DEFAULT_LOCAL_EXCEL_PATH),
        help="Excel file path. Defaults to the workspace Lotto Excel file.",
    )
    import_excel_parser.add_argument(
        "--export",
        action="store_true",
        help="Export CSV and JSON backups after import",
    )

    draw_parser = subparsers.add_parser("collect-draw", help="Collect one draw")
    draw_parser.add_argument("draw_no", type=int, help="Draw number to collect")

    range_parser = subparsers.add_parser("collect-range", help="Collect a draw range")
    range_parser.add_argument("start_draw", type=int, help="First draw number")
    range_parser.add_argument("end_draw", type=int, help="Last draw number")

    latest_parser = subparsers.add_parser(
        "collect-latest",
        help="Collect from a start draw through the latest available draw",
    )
    latest_parser.add_argument("--start", type=int, default=1, help="First draw number")

    save_draw_parser = subparsers.add_parser("save-draw", help="Collect and save one draw")
    save_draw_parser.add_argument("draw_no", type=int, help="Draw number to save")

    save_range_parser = subparsers.add_parser(
        "save-range",
        help="Collect and save a draw range",
    )
    save_range_parser.add_argument("start_draw", type=int, help="First draw number")
    save_range_parser.add_argument("end_draw", type=int, help="Last draw number")

    add_draw_parser = subparsers.add_parser(
        "add-draw",
        help="Manually save one draw without crawling (use when the site is blocked)",
    )
    add_draw_parser.add_argument("draw_no", type=int, help="Draw number")
    add_draw_parser.add_argument("draw_date", type=date.fromisoformat, help="Draw date (YYYY-MM-DD)")
    add_draw_parser.add_argument("numbers", type=int, nargs=6, help="Six winning numbers")
    add_draw_parser.add_argument("bonus", type=int, help="Bonus number")

    subparsers.add_parser("export-data", help="Export SQLite data to CSV and JSON")

    frequency_parser = subparsers.add_parser(
        "analyze-frequency",
        help="Analyze number frequency from stored draws",
    )
    frequency_parser.add_argument(
        "--number",
        type=int,
        choices=range(1, 46),
        metavar="1-45",
        help="Show a simple text report for one number",
    )

    subparsers.add_parser("analyze-patterns", help="Analyze draw patterns from stored data")

    subparsers.add_parser("score-numbers", help="Calculate Hot/Warm/Cold number scores")

    generate_parser = subparsers.add_parser(
        "generate-combinations",
        help="Generate reference combinations without saving them",
    )
    _add_generation_arguments(generate_parser)

    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Generate and save recommendations for the next draw",
    )
    _add_generation_arguments(recommend_parser)

    evaluate_parser = subparsers.add_parser(
        "evaluate-recommendations",
        help="Evaluate saved recommendations against a stored actual draw",
    )
    evaluate_parser.add_argument(
        "target_draw_no",
        type=int,
        nargs="?",
        help="Target draw number. Defaults to the latest stored draw.",
    )

    backtest_parser = subparsers.add_parser("backtest", help="Run walk-forward backtesting")
    backtest_parser.add_argument("start_draw", type=int, help="First target draw number")
    backtest_parser.add_argument("end_draw", type=int, help="Last target draw number")
    backtest_parser.add_argument("--strategy", default="Hybrid", help="Generation strategy")

    subparsers.add_parser("export-charts", help="Export MVP charts as PNG files")
    subparsers.add_parser("export-report", help="Export the Excel report")

    return parser


def run_command(args: argparse.Namespace) -> int:
    """Execute the selected command and print validated draw data."""
    ensure_project_directories()
    crawler = LottoCrawler()
    database = LottoDatabaseManager()

    if args.command == "init-db":
        database.initialize_database()
        print(f"Database initialized: {database.db_path}")
        return 0

    if args.command == "import-excel":
        draws = load_draws_from_excel(args.path)
        saved_count = database.save_draws(draws)
        print(f"Imported {saved_count} draws from {args.path}")
        if args.export:
            csv_path, json_path = database.export_backups()
            print(f"CSV backup: {csv_path}")
            print(f"JSON backup: {json_path}")
        return 0

    if args.command == "collect-draw":
        print(draw_to_pretty_json(crawler.fetch_draw(args.draw_no)))
        return 0

    if args.command == "collect-range":
        draws = crawler.fetch_range(args.start_draw, args.end_draw)
        print(json.dumps([draw.to_dict() for draw in draws], ensure_ascii=False, indent=2))
        return 0

    if args.command == "collect-latest":
        draws = crawler.collect_until_latest(args.start)
        print(json.dumps([draw.to_dict() for draw in draws], ensure_ascii=False, indent=2))
        return 0

    if args.command == "save-draw":
        draw = crawler.fetch_draw(args.draw_no)
        database.save_draw(draw)
        print(f"Saved draw {draw.draw_no}: {draw.to_dict()}")
        return 0

    if args.command == "save-range":
        draws = crawler.fetch_range(args.start_draw, args.end_draw)
        saved_count = database.save_draws(draws)
        print(f"Saved {saved_count} draws.")
        return 0

    if args.command == "add-draw":
        draw = LottoDraw(
            draw_no=args.draw_no,
            draw_date=args.draw_date,
            numbers=tuple(args.numbers),
            bonus=args.bonus,
        )
        database.save_draw(draw)
        print(f"Saved draw {draw.draw_no}: {draw.to_dict()}")
        return 0

    if args.command == "export-data":
        csv_path, json_path = database.export_backups()
        print(f"CSV backup: {csv_path}")
        print(f"JSON backup: {json_path}")
        return 0

    if args.command == "analyze-frequency":
        draws = database.list_draws()
        stats_by_number = analyze_number_frequency(draws)
        if args.number is not None:
            print(format_number_stats(stats_by_number[args.number]))
        else:
            print(json.dumps(stats_to_rows(stats_by_number), ensure_ascii=False, indent=2))
        return 0

    if args.command == "analyze-patterns":
        draws = _require_draws(database)
        summary = analyze_patterns(draws)
        print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "score-numbers":
        draws = _require_draws(database)
        scores = calculate_number_scores(draws)
        print(json.dumps({"groups": category_groups(scores), "scores": score_rows(scores)}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "generate-combinations":
        draws = _require_draws(database)
        combinations = _generate_from_draws(draws, args)
        print(json.dumps([item.to_dict() for item in combinations], ensure_ascii=False, indent=2))
        return 0

    if args.command == "recommend":
        draws = _require_draws(database)
        combinations = _generate_from_draws(draws, args)
        target_draw_no = draws[-1].draw_no + 1
        records = [
            RecommendationRecord(
                recommendation_id=_recommendation_id(target_draw_no, args.strategy, index),
                target_draw_no=target_draw_no,
                created_date=date.today(),
                combination=combination,
            )
            for index, combination in enumerate(combinations, start=1)
        ]
        database.save_recommendations(records)
        print(json.dumps([record.to_dict() for record in records], ensure_ascii=False, indent=2))
        return 0

    if args.command == "evaluate-recommendations":
        target_draw_no = args.target_draw_no or database.get_latest_draw_no()
        if target_draw_no is None:
            raise LottoDatabaseError("No stored draws are available for evaluation.")
        actual_draw = database.get_draw(target_draw_no)
        if actual_draw is None:
            raise LottoDatabaseError(f"Draw {target_draw_no} is not stored.")
        records = database.list_recommendations(target_draw_no)
        if not records:
            raise LottoDatabaseError(f"No recommendations found for draw {target_draw_no}.")
        evaluations = [evaluate_recommendation(record, actual_draw) for record in records]
        database.save_evaluations(evaluations)
        print(json.dumps([item.to_dict() for item in evaluations], ensure_ascii=False, indent=2))
        return 0

    if args.command == "backtest":
        draws = _require_draws(database)
        summary = run_backtest(draws, args.start_draw, args.end_draw, strategy=args.strategy)
        print(
            json.dumps(
                {"summary": summary.to_dict(), "rounds": [item.to_dict() for item in summary.rounds]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "export-charts":
        draws = _require_draws(database)
        stats = analyze_number_frequency(draws)
        patterns = analyze_patterns(draws)
        scores = calculate_number_scores(draws)
        paths = export_all_charts(stats, scores, patterns)
        print(json.dumps([str(path) for path in paths], ensure_ascii=False, indent=2))
        return 0

    if args.command == "export-report":
        draws = _require_draws(database)
        stats = analyze_number_frequency(draws)
        patterns = analyze_patterns(draws)
        scores = calculate_number_scores(draws)
        path = export_excel_report(
            draws,
            stats,
            patterns,
            scores,
            recommendations=database.list_recommendations(),
            evaluations=database.list_evaluations(),
        )
        print(f"Excel report: {path}")
        return 0

    raise LottoCrawlerError(f"Unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line application and convert errors to exit codes."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return run_command(args)
    except (
        LottoCrawlerError,
        LocalDataLoadError,
        LottoDatabaseError,
        FrequencyAnalysisError,
        PatternAnalysisError,
        ScoringError,
        CombinationGenerationError,
        BacktestError,
        ChartExportError,
        ExcelExportError,
        ValueError,
    ) as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")


def _add_generation_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared command line arguments for combination generation commands."""
    parser.add_argument("--count", type=int, default=5, help="Number of combinations")
    parser.add_argument("--strategy", default="Hybrid", help="Random, Balanced, Hot Mix, Cold Mix, Hybrid")
    parser.add_argument("--sum-min", type=int, default=100, help="Minimum combination sum")
    parser.add_argument("--sum-max", type=int, default=180, help="Maximum combination sum")
    parser.add_argument("--exclude-latest", action="store_true", help="Exclude latest draw numbers")


def _require_draws(database: LottoDatabaseManager) -> list[LottoDraw]:
    """Load stored draws or raise a user-facing error when none are available."""
    draws = database.list_draws()
    if not draws:
        raise LottoDatabaseError("No stored draws found. Save draw data first.")
    return draws


def _constraints_from_args(args: argparse.Namespace) -> CombinationConstraints:
    """Build generation constraints from command line arguments."""
    return CombinationConstraints(
        sum_min=args.sum_min,
        sum_max=args.sum_max,
        exclude_latest_draw_numbers=args.exclude_latest,
    )


def _generate_from_draws(draws: list[LottoDraw], args: argparse.Namespace):
    """Calculate scores and generate combinations from stored draws."""
    scores = calculate_number_scores(draws)
    return generate_combinations(
        scores,
        latest_draw=draws[-1],
        constraints=_constraints_from_args(args),
        strategy=args.strategy,
        count=args.count,
        excluded_combinations=[draw.numbers for draw in draws],
    )


def _recommendation_id(target_draw_no: int, strategy: str, index: int) -> str:
    """Build a stable recommendation id for one target draw and strategy."""
    strategy_key = strategy.lower().replace(" ", "_")
    return f"{target_draw_no}-{strategy_key}-{index:03d}"


if __name__ == "__main__":
    raise SystemExit(main())
