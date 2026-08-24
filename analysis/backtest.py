"""Walk-forward backtesting for Lotto combination strategies."""

from __future__ import annotations

from dataclasses import dataclass

from lotto_analyzer.analysis.evaluation import lotto_result_label
from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import (
    CombinationConstraints,
    CombinationGenerationError,
    GeneratedCombination,
    generate_combinations,
)


class BacktestError(Exception):
    """Raised when backtesting cannot be performed."""


@dataclass(frozen=True, slots=True)
class BacktestRound:
    """Store one walk-forward backtest result."""

    target_draw_no: int
    generated: GeneratedCombination
    actual_numbers: tuple[int, ...]
    bonus: int
    match_count: int
    bonus_matched: bool
    result_label: str

    def to_dict(self) -> dict[str, object]:
        """Convert the backtest round to a report-friendly dictionary."""
        return {
            "target_draw_no": self.target_draw_no,
            "generated_numbers": list(self.generated.numbers),
            "actual_numbers": list(self.actual_numbers),
            "bonus": self.bonus,
            "match_count": self.match_count,
            "bonus_matched": self.bonus_matched,
            "result_label": self.result_label,
            "strategy": self.generated.strategy,
            "combination_score": round(self.generated.score, 2),
        }


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    """Store aggregate backtest results."""

    rounds: list[BacktestRound]
    total_rounds: int
    match_3_count: int
    match_4_count: int
    match_5_count: int
    match_6_count: int
    average_match_count: float

    def to_dict(self) -> dict[str, object]:
        """Convert the summary to a JSON-friendly dictionary."""
        return {
            "total_rounds": self.total_rounds,
            "match_3_count": self.match_3_count,
            "match_4_count": self.match_4_count,
            "match_5_count": self.match_5_count,
            "match_6_count": self.match_6_count,
            "average_match_count": round(self.average_match_count, 3),
        }


def run_backtest(
    draws: list[LottoDraw],
    start_draw_no: int,
    end_draw_no: int,
    strategy: str = "Hybrid",
    constraints: CombinationConstraints = CombinationConstraints(),
    seed: int | None = 20240617,
) -> BacktestSummary:
    """Run walk-forward backtesting without using future draw data."""
    ordered_draws = sorted(draws, key=lambda draw: draw.draw_no)
    draw_by_no = {draw.draw_no: draw for draw in ordered_draws}
    if start_draw_no > end_draw_no:
        raise BacktestError("start_draw_no must be less than or equal to end_draw_no.")
    if start_draw_no not in draw_by_no or end_draw_no not in draw_by_no:
        raise BacktestError("Backtest range must exist in stored draws.")

    rounds: list[BacktestRound] = []
    for target_draw_no in range(start_draw_no, end_draw_no + 1):
        actual_draw = draw_by_no.get(target_draw_no)
        history = [draw for draw in ordered_draws if draw.draw_no < target_draw_no]
        if actual_draw is None:
            continue
        if not history:
            continue

        try:
            scores = calculate_number_scores(history)
            generated = generate_combinations(
                scores,
                latest_draw=history[-1],
                constraints=constraints,
                strategy=strategy,
                count=1,
                seed=(seed or 0) + target_draw_no,
            )[0]
        except CombinationGenerationError as exc:
            raise BacktestError(f"Could not generate for draw {target_draw_no}: {exc}") from exc

        actual_set = set(actual_draw.numbers)
        match_count = sum(1 for number in generated.numbers if number in actual_set)
        bonus_matched = actual_draw.bonus in generated.numbers
        rounds.append(
            BacktestRound(
                target_draw_no=target_draw_no,
                generated=generated,
                actual_numbers=actual_draw.numbers,
                bonus=actual_draw.bonus,
                match_count=match_count,
                bonus_matched=bonus_matched,
                result_label=lotto_result_label(match_count, bonus_matched),
            )
        )

    if not rounds:
        raise BacktestError("No backtest rounds were executed.")

    return BacktestSummary(
        rounds=rounds,
        total_rounds=len(rounds),
        match_3_count=sum(1 for item in rounds if item.match_count == 3),
        match_4_count=sum(1 for item in rounds if item.match_count == 4),
        match_5_count=sum(1 for item in rounds if item.match_count == 5),
        match_6_count=sum(1 for item in rounds if item.match_count == 6),
        average_match_count=sum(item.match_count for item in rounds) / len(rounds),
    )
