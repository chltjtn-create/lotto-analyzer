"""Analysis package for Lotto draw statistics."""

from lotto_analyzer.analysis.frequency import (
    FrequencyAnalysisError,
    NumberFrequencyStats,
    analyze_number_frequency,
)
from lotto_analyzer.analysis.pattern import (
    DrawPattern,
    PatternAnalysisError,
    PatternSummary,
    analyze_draw_pattern,
    analyze_patterns,
)
from lotto_analyzer.analysis.scoring import (
    NumberScore,
    ScoreWeights,
    ScoringError,
    calculate_number_scores,
    category_groups,
)

__all__ = [
    "DrawPattern",
    "FrequencyAnalysisError",
    "NumberFrequencyStats",
    "NumberScore",
    "PatternAnalysisError",
    "PatternSummary",
    "ScoreWeights",
    "ScoringError",
    "analyze_draw_pattern",
    "analyze_number_frequency",
    "analyze_patterns",
    "calculate_number_scores",
    "category_groups",
]
