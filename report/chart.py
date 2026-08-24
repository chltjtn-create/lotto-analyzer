"""Matplotlib chart exports for Lotto analysis results."""

from __future__ import annotations

from pathlib import Path

from lotto_analyzer.analysis.frequency import NumberFrequencyStats
from lotto_analyzer.analysis.pattern import PatternSummary
from lotto_analyzer.analysis.scoring import NumberScore
from lotto_analyzer.config import REPORT_OUTPUT_DIR


class ChartExportError(Exception):
    """Raised when a chart cannot be exported."""


def export_frequency_chart(
    stats_by_number: dict[int, NumberFrequencyStats],
    output_path: Path | str = REPORT_OUTPUT_DIR / "frequency.png",
) -> Path:
    """Export a bar chart of total appearances by number."""
    labels = list(range(1, 46))
    values = [stats_by_number[number].total_count for number in labels]
    return _export_bar_chart(labels, values, "번호별 출현 빈도", "번호", "출현 횟수", output_path)


def export_missing_chart(
    stats_by_number: dict[int, NumberFrequencyStats],
    output_path: Path | str = REPORT_OUTPUT_DIR / "missing.png",
) -> Path:
    """Export a bar chart of missing draw counts by number."""
    labels = list(range(1, 46))
    values = [stats_by_number[number].missing_draws for number in labels]
    return _export_bar_chart(labels, values, "번호별 미출현 회차 수", "번호", "미출현 회차", output_path)


def export_hot_chart(
    scores_by_number: dict[int, NumberScore],
    output_path: Path | str = REPORT_OUTPUT_DIR / "hot_numbers.png",
) -> Path:
    """Export a bar chart of top-scored numbers."""
    top_scores = sorted(scores_by_number.values(), key=lambda item: (-item.final_score, item.number))[:15]
    labels = [score.number for score in top_scores]
    values = [score.final_score for score in top_scores]
    return _export_bar_chart(labels, values, "Hot Number 순위", "번호", "점수", output_path)


def export_section_chart(
    summary: PatternSummary,
    output_path: Path | str = REPORT_OUTPUT_DIR / "sections.png",
) -> Path:
    """Export a bar chart of number section totals."""
    labels = list(summary.section_totals)
    values = [summary.section_totals[label] for label in labels]
    return _export_bar_chart(labels, values, "구간별 분포", "구간", "출현 개수", output_path)


def export_all_charts(
    stats_by_number: dict[int, NumberFrequencyStats],
    scores_by_number: dict[int, NumberScore],
    pattern_summary: PatternSummary,
    output_dir: Path | str = REPORT_OUTPUT_DIR,
) -> list[Path]:
    """Export all MVP charts and return their paths."""
    output = Path(output_dir)
    return [
        export_frequency_chart(stats_by_number, output / "frequency.png"),
        export_missing_chart(stats_by_number, output / "missing.png"),
        export_hot_chart(scores_by_number, output / "hot_numbers.png"),
        export_section_chart(pattern_summary, output / "sections.png"),
    ]


_FONT_READY = False

# Chart titles and axis labels are Korean. Matplotlib's default font (DejaVu Sans)
# has no Hangul glyphs, so every label renders as empty boxes. Pick whichever
# Korean font this machine actually has: Windows ships Malgun Gothic, and the
# GitHub Actions runner installs fonts-nanum in the workflow.
_KOREAN_FONTS = (
    "Malgun Gothic",      # Windows
    "AppleGothic",        # macOS
    "NanumGothic",        # Linux (fonts-nanum)
    "NanumBarunGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR",
)


def _apply_korean_font(matplotlib, plt) -> None:
    """Select an installed Korean font once per process."""
    global _FONT_READY
    if _FONT_READY:
        return
    _FONT_READY = True

    from matplotlib import font_manager

    available = {font.name for font in font_manager.fontManager.ttflist}

    chosen = next((name for name in _KOREAN_FONTS if name in available), None)

    # Nothing matched by exact name. Fall back to any installed font whose name
    # marks it as Korean or CJK - the Noto CJK family is unified, so the JP build
    # carries Hangul too.
    if chosen is None:
        chosen = next(
            (
                name
                for name in sorted(available)
                if any(key in name for key in ("Nanum", "Malgun", "CJK", "Gothic", "Gulim", "Dotum", "Batang"))
            ),
            None,
        )

    if chosen:
        plt.rcParams["font.family"] = chosen
    # Korean fonts render the minus sign as a missing glyph unless this is off.
    plt.rcParams["axes.unicode_minus"] = False


def _export_bar_chart(
    labels: list[object],
    values: list[float | int],
    title: str,
    xlabel: str,
    ylabel: str,
    output_path: Path | str,
) -> Path:
    """Export a simple bar chart to PNG."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ChartExportError("matplotlib is required to export charts.") from exc

    _apply_korean_font(matplotlib, plt)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar([str(label) for label in labels], values)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", labelrotation=90 if len(labels) > 20 else 0)
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
    except OSError as exc:
        raise ChartExportError(f"Failed to save chart: {exc}") from exc
    return path
