"""Walk-forward backtesting for Lotto combination strategies."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import random
from statistics import mean, stdev

from lotto_analyzer.analysis.evaluation import lotto_result_label
from lotto_analyzer.analysis.frequency import FrequencyAnalysisError
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import (
    CombinationConstraints,
    CombinationGenerationError,
    GeneratedCombination,
    DEFAULT_RECOMMENDATION_CONSTRAINTS,
    DEFAULT_RECOMMENDATION_COUNT,
    generate_from_history,
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
    total_tickets: int
    tickets_per_draw: int
    average_best_match_count: float
    winning_draw_count: int
    random_average_match_count: float
    mean_match_difference: float
    difference_ci95: tuple[float, float] | None
    baseline_repeats: int
    seed: int
    settings: dict[str, object]
    data_hash: str

    def to_dict(self) -> dict[str, object]:
        """Convert the summary to a JSON-friendly dictionary."""
        return {
            "total_rounds": self.total_rounds,
            "match_3_count": self.match_3_count,
            "match_4_count": self.match_4_count,
            "match_5_count": self.match_5_count,
            "match_6_count": self.match_6_count,
            "average_match_count": round(self.average_match_count, 3),
            "total_tickets": self.total_tickets,
            "tickets_per_draw": self.tickets_per_draw,
            "average_best_match_count": round(self.average_best_match_count, 3),
            "winning_draw_count": self.winning_draw_count,
            "random_average_match_count": round(self.random_average_match_count, 3),
            "mean_match_difference": round(self.mean_match_difference, 3),
            "difference_ci95": self.difference_ci95,
            "baseline_repeats": self.baseline_repeats,
            "seed": self.seed,
            "settings": self.settings,
            "data_hash": self.data_hash,
        }


def run_backtest(
    draws: list[LottoDraw],
    start_draw_no: int,
    end_draw_no: int,
    strategy: str = "Hybrid",
    constraints: CombinationConstraints = DEFAULT_RECOMMENDATION_CONSTRAINTS,
    seed: int | None = 20240617,
    count: int = DEFAULT_RECOMMENDATION_COUNT,
    baseline_repeats: int = 20,
) -> BacktestSummary:
    """Run walk-forward backtesting without using future draw data."""
    ordered_draws = sorted(
        (draw for draw in draws if draw.draw_no <= end_draw_no), key=lambda draw: draw.draw_no
    )
    draw_by_no = {draw.draw_no: draw for draw in ordered_draws}
    if start_draw_no > end_draw_no:
        raise BacktestError("start_draw_no must be less than or equal to end_draw_no.")
    if start_draw_no not in draw_by_no or end_draw_no not in draw_by_no:
        raise BacktestError("Backtest range must exist in stored draws.")
    if len(draw_by_no) != len(ordered_draws):
        raise BacktestError("Duplicate draw numbers in backtest history.")
    if any(b.draw_no != a.draw_no + 1 for a, b in zip(ordered_draws, ordered_draws[1:])):
        raise BacktestError("Missing draw rounds in backtest history.")
    if not ordered_draws or ordered_draws[0].draw_no >= start_draw_no:
        raise BacktestError("At least one earlier draw is required for every target.")
    if count < 1 or count > 100 or baseline_repeats < 1:
        raise BacktestError("Use 1-100 tickets per draw and at least one baseline repeat.")
    seed = seed if seed is not None else random.SystemRandom().randrange(2**32)

    rounds: list[BacktestRound] = []
    per_draw_best: list[int] = []
    differences: list[float] = []
    baseline_means: list[float] = []
    for target_draw_no in range(start_draw_no, end_draw_no + 1):
        actual_draw = draw_by_no.get(target_draw_no)
        history = [draw for draw in ordered_draws if draw.draw_no < target_draw_no]
        try:
            combinations = generate_from_history(
                history,
                constraints=constraints,
                strategy=strategy,
                count=count,
                seed=seed + target_draw_no,
            )
        except (CombinationGenerationError, FrequencyAnalysisError) as exc:
            raise BacktestError(f"Could not generate for draw {target_draw_no}: {exc}") from exc

        actual_set = set(actual_draw.numbers)
        matches: list[int] = []
        for generated in combinations:
            match_count = len(set(generated.numbers) & actual_set)
            matches.append(match_count)
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
        # Each repeat uses the same ticket budget. Aggregate uncertainty by draw,
        # since tickets within a draw share one outcome.
        rng = random.Random((seed + target_draw_no) ^ 0xA5A5A5A5)
        random_matches = []
        for _ in range(baseline_repeats):
            tickets: set[tuple[int, ...]] = set()
            while len(tickets) < count:
                tickets.add(tuple(sorted(rng.sample(range(1, 46), 6))))
            random_matches.extend(len(set(ticket) & actual_set) for ticket in tickets)
        baseline_means.append(mean(random_matches))
        differences.append(mean(matches) - baseline_means[-1])
        per_draw_best.append(max(matches))

    if not rounds:
        raise BacktestError("No backtest rounds were executed.")

    difference = mean(differences)
    interval = None
    if len(differences) >= 30:
        margin = 1.96 * stdev(differences) / math.sqrt(len(differences))
        interval = (difference - margin, difference + margin)
    return BacktestSummary(
        rounds=rounds,
        total_rounds=len(per_draw_best),
        match_3_count=sum(1 for item in rounds if item.match_count == 3),
        match_4_count=sum(1 for item in rounds if item.match_count == 4),
        match_5_count=sum(1 for item in rounds if item.match_count == 5),
        match_6_count=sum(1 for item in rounds if item.match_count == 6),
        average_match_count=sum(item.match_count for item in rounds) / len(rounds),
        total_tickets=len(rounds),
        tickets_per_draw=count,
        average_best_match_count=mean(per_draw_best),
        winning_draw_count=sum(best >= 3 for best in per_draw_best),
        random_average_match_count=mean(baseline_means),
        mean_match_difference=difference,
        difference_ci95=interval,
        baseline_repeats=baseline_repeats,
        seed=seed,
        settings={"strategy": strategy, "constraints": asdict(constraints),
                  "exclude_historical_combinations": True},
        data_hash=sha256(json.dumps(
            [draw.to_dict() for draw in ordered_draws], sort_keys=True
        ).encode("utf-8")).hexdigest(),
    )
