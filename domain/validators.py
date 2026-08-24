"""Validation helpers for Lotto draw data."""

from __future__ import annotations

from datetime import date
from typing import Iterable


class DrawValidationError(ValueError):
    """Raised when Lotto draw data does not match domain rules."""


def validate_draw_no(draw_no: int) -> None:
    """Validate that a draw number is a positive integer."""
    if not isinstance(draw_no, int):
        raise DrawValidationError("Draw number must be an integer.")
    if draw_no < 1:
        raise DrawValidationError("Draw number must be greater than 0.")


def validate_draw_date(draw_date: date) -> None:
    """Validate that a draw date is a date object."""
    if not isinstance(draw_date, date):
        raise DrawValidationError("Draw date must be a date value.")


def validate_lotto_numbers(numbers: Iterable[int]) -> tuple[int, ...]:
    """Validate six unique winning numbers in the 1-45 range."""
    normalized = tuple(numbers)
    if len(normalized) != 6:
        raise DrawValidationError("Exactly six winning numbers are required.")

    if any(not isinstance(number, int) for number in normalized):
        raise DrawValidationError("Winning numbers must be integers.")

    if any(number < 1 or number > 45 for number in normalized):
        raise DrawValidationError("Winning numbers must be between 1 and 45.")

    if len(set(normalized)) != 6:
        raise DrawValidationError("Winning numbers must not contain duplicates.")

    return normalized


def validate_bonus_number(bonus: int, numbers: Iterable[int]) -> None:
    """Validate that the bonus number is in range and not duplicated."""
    if not isinstance(bonus, int):
        raise DrawValidationError("Bonus number must be an integer.")
    if bonus < 1 or bonus > 45:
        raise DrawValidationError("Bonus number must be between 1 and 45.")
    if bonus in set(numbers):
        raise DrawValidationError("Bonus number must not duplicate a winning number.")


def validate_draw_values(
    draw_no: int,
    draw_date: date,
    numbers: Iterable[int],
    bonus: int,
) -> tuple[int, ...]:
    """Validate all fields for one Lotto draw and return normalized numbers."""
    validate_draw_no(draw_no)
    validate_draw_date(draw_date)
    normalized_numbers = validate_lotto_numbers(numbers)
    validate_bonus_number(bonus, normalized_numbers)
    return normalized_numbers
