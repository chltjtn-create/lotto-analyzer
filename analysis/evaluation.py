"""Evaluation of saved recommendations against announced draw results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import GeneratedCombination


@dataclass(frozen=True, slots=True)
class RecommendationRecord:
    """Store a generated combination for a target draw."""

    recommendation_id: str
    target_draw_no: int
    created_date: date
    combination: GeneratedCombination

    def to_dict(self) -> dict[str, object]:
        """Convert the recommendation record to a report-friendly dictionary."""
        row = {
            "recommendation_id": self.recommendation_id,
            "target_draw_no": self.target_draw_no,
            "created_date": self.created_date.isoformat(),
        }
        row.update(self.combination.to_dict())
        return row


@dataclass(frozen=True, slots=True)
class RecommendationEvaluation:
    """Store comparison result between a recommendation and actual draw."""

    recommendation_id: str
    target_draw_no: int
    recommended_numbers: tuple[int, ...]
    actual_numbers: tuple[int, ...]
    bonus: int
    matched_numbers: tuple[int, ...]
    match_count: int
    bonus_matched: bool
    result_label: str

    def to_dict(self) -> dict[str, object]:
        """Convert the evaluation to a report-friendly dictionary."""
        return {
            "recommendation_id": self.recommendation_id,
            "target_draw_no": self.target_draw_no,
            "recommended_numbers": list(self.recommended_numbers),
            "actual_numbers": list(self.actual_numbers),
            "bonus": self.bonus,
            "matched_numbers": list(self.matched_numbers),
            "match_count": self.match_count,
            "bonus_matched": self.bonus_matched,
            "result_label": self.result_label,
        }


def evaluate_recommendation(
    record: RecommendationRecord,
    actual_draw: LottoDraw,
) -> RecommendationEvaluation:
    """Compare one saved recommendation with an announced draw result."""
    if record.target_draw_no != actual_draw.draw_no:
        raise ValueError("Recommendation target draw does not match actual draw number.")

    recommended = tuple(record.combination.numbers)
    actual_set = set(actual_draw.numbers)
    matched = tuple(number for number in recommended if number in actual_set)
    bonus_matched = actual_draw.bonus in recommended
    return RecommendationEvaluation(
        recommendation_id=record.recommendation_id,
        target_draw_no=record.target_draw_no,
        recommended_numbers=recommended,
        actual_numbers=actual_draw.numbers,
        bonus=actual_draw.bonus,
        matched_numbers=matched,
        match_count=len(matched),
        bonus_matched=bonus_matched,
        result_label=lotto_result_label(len(matched), bonus_matched),
    )


def lotto_result_label(match_count: int, bonus_matched: bool) -> str:
    """Return a Lotto 6/45 rank label from match count and bonus match status."""
    if match_count == 6:
        return "1등"
    if match_count == 5 and bonus_matched:
        return "2등"
    if match_count == 5:
        return "3등"
    if match_count == 4:
        return "4등"
    if match_count == 3:
        return "5등"
    return "미당첨"
