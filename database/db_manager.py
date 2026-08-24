"""SQLite storage and backup export utilities for Lotto draw data."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from lotto_analyzer.analysis.evaluation import RecommendationEvaluation, RecommendationRecord
from lotto_analyzer.config import LOTTO_CSV_PATH, LOTTO_DB_PATH, LOTTO_JSON_PATH
from lotto_analyzer.domain.models import LottoDraw
from lotto_analyzer.generator.combination import GeneratedCombination


class LottoDatabaseError(Exception):
    """Raised when database or backup file work fails."""


class LottoDatabaseManager:
    """Manage SQLite persistence and CSV/JSON backups for LottoDraw objects."""

    FIELD_NAMES = [
        "draw_no",
        "draw_date",
        "num1",
        "num2",
        "num3",
        "num4",
        "num5",
        "num6",
        "bonus",
    ]

    def __init__(self, db_path: Path | str = LOTTO_DB_PATH) -> None:
        """Create a manager for a specific SQLite database path."""
        self.db_path = Path(db_path)

    def initialize_database(self) -> None:
        """Create the database file and draws table if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS draws (
                        draw_no INTEGER PRIMARY KEY,
                        draw_date TEXT NOT NULL,
                        num1 INTEGER NOT NULL,
                        num2 INTEGER NOT NULL,
                        num3 INTEGER NOT NULL,
                        num4 INTEGER NOT NULL,
                        num5 INTEGER NOT NULL,
                        num6 INTEGER NOT NULL,
                        bonus INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_draws_draw_date ON draws(draw_date)"
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recommendations (
                        recommendation_id TEXT PRIMARY KEY,
                        target_draw_no INTEGER NOT NULL,
                        created_date TEXT NOT NULL,
                        numbers_json TEXT NOT NULL,
                        score REAL NOT NULL,
                        odd_even TEXT NOT NULL,
                        high_low TEXT NOT NULL,
                        total_sum INTEGER NOT NULL,
                        hot_count INTEGER NOT NULL,
                        warm_count INTEGER NOT NULL,
                        cold_count INTEGER NOT NULL,
                        strategy TEXT NOT NULL,
                        disclaimer TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recommendation_evaluations (
                        recommendation_id TEXT PRIMARY KEY,
                        target_draw_no INTEGER NOT NULL,
                        recommended_numbers_json TEXT NOT NULL,
                        actual_numbers_json TEXT NOT NULL,
                        bonus INTEGER NOT NULL,
                        matched_numbers_json TEXT NOT NULL,
                        match_count INTEGER NOT NULL,
                        bonus_matched INTEGER NOT NULL,
                        result_label TEXT NOT NULL,
                        evaluated_at TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to initialize database: {exc}") from exc

    def save_draw(self, draw: LottoDraw) -> None:
        """Insert or update one verified Lotto draw."""
        self.initialize_database()
        now = self._utc_now()
        values = draw.to_dict()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO draws (
                        draw_no, draw_date, num1, num2, num3, num4, num5, num6,
                        bonus, created_at, updated_at
                    )
                    VALUES (
                        :draw_no, :draw_date, :num1, :num2, :num3, :num4, :num5,
                        :num6, :bonus, :created_at, :updated_at
                    )
                    ON CONFLICT(draw_no) DO UPDATE SET
                        draw_date = excluded.draw_date,
                        num1 = excluded.num1,
                        num2 = excluded.num2,
                        num3 = excluded.num3,
                        num4 = excluded.num4,
                        num5 = excluded.num5,
                        num6 = excluded.num6,
                        bonus = excluded.bonus,
                        updated_at = excluded.updated_at
                    """,
                    {
                        **values,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to save draw {draw.draw_no}: {exc}") from exc

    def save_draws(self, draws: Iterable[LottoDraw]) -> int:
        """Save many verified Lotto draws and return the processed count."""
        processed_count = 0
        for draw in draws:
            self.save_draw(draw)
            processed_count += 1
        return processed_count

    def get_draw(self, draw_no: int) -> LottoDraw | None:
        """Return one draw by draw number, or None when it is missing."""
        self.initialize_database()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus
                    FROM draws
                    WHERE draw_no = ?
                    """,
                    (draw_no,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to load draw {draw_no}: {exc}") from exc

        if row is None:
            return None
        return self._row_to_draw(row)

    def list_draws(self) -> list[LottoDraw]:
        """Return all stored draws sorted by draw number."""
        self.initialize_database()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus
                    FROM draws
                    ORDER BY draw_no ASC
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to list draws: {exc}") from exc

        return [self._row_to_draw(row) for row in rows]

    def count_draws(self) -> int:
        """Return the number of stored draws."""
        self.initialize_database()
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT COUNT(*) AS total FROM draws").fetchone()
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to count draws: {exc}") from exc
        return int(row["total"])

    def get_latest_draw_no(self) -> int | None:
        """Return the highest stored draw number, or None when empty."""
        self.initialize_database()
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT MAX(draw_no) AS latest FROM draws").fetchone()
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to find latest draw: {exc}") from exc

        if row["latest"] is None:
            return None
        return int(row["latest"])

    def export_to_csv(self, csv_path: Path | str = LOTTO_CSV_PATH) -> Path:
        """Export stored draws to a CSV backup file and return the path."""
        export_path = Path(csv_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        rows = [draw.to_dict() for draw in self.list_draws()]

        try:
            with export_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=self.FIELD_NAMES)
                writer.writeheader()
                writer.writerows(rows)
        except OSError as exc:
            raise LottoDatabaseError(f"Failed to export CSV backup: {exc}") from exc

        return export_path

    def export_to_json(self, json_path: Path | str = LOTTO_JSON_PATH) -> Path:
        """Export stored draws to a JSON backup file and return the path."""
        export_path = Path(json_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        rows = [draw.to_dict() for draw in self.list_draws()]

        try:
            with export_path.open("w", encoding="utf-8") as json_file:
                json.dump(rows, json_file, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise LottoDatabaseError(f"Failed to export JSON backup: {exc}") from exc

        return export_path

    def export_backups(
        self,
        csv_path: Path | str = LOTTO_CSV_PATH,
        json_path: Path | str = LOTTO_JSON_PATH,
    ) -> tuple[Path, Path]:
        """Export both CSV and JSON backups and return their paths."""
        return self.export_to_csv(csv_path), self.export_to_json(json_path)

    def save_recommendation(self, record: RecommendationRecord) -> None:
        """Insert or update one generated recommendation record."""
        self.initialize_database()
        now = self._utc_now()
        combination = record.combination
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO recommendations (
                        recommendation_id, target_draw_no, created_date, numbers_json,
                        score, odd_even, high_low, total_sum, hot_count, warm_count,
                        cold_count, strategy, disclaimer, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(recommendation_id) DO UPDATE SET
                        target_draw_no = excluded.target_draw_no,
                        created_date = excluded.created_date,
                        numbers_json = excluded.numbers_json,
                        score = excluded.score,
                        odd_even = excluded.odd_even,
                        high_low = excluded.high_low,
                        total_sum = excluded.total_sum,
                        hot_count = excluded.hot_count,
                        warm_count = excluded.warm_count,
                        cold_count = excluded.cold_count,
                        strategy = excluded.strategy,
                        disclaimer = excluded.disclaimer,
                        updated_at = excluded.updated_at
                    """,
                    (
                        record.recommendation_id,
                        record.target_draw_no,
                        record.created_date.isoformat(),
                        json.dumps(list(combination.numbers), ensure_ascii=False),
                        combination.score,
                        combination.odd_even,
                        combination.high_low,
                        combination.total_sum,
                        combination.hot_count,
                        combination.warm_count,
                        combination.cold_count,
                        combination.strategy,
                        combination.disclaimer,
                        now,
                        now,
                    ),
                )
        except sqlite3.Error as exc:
            raise LottoDatabaseError(
                f"Failed to save recommendation {record.recommendation_id}: {exc}"
            ) from exc

    def save_recommendations(self, records: Iterable[RecommendationRecord]) -> int:
        """Save many recommendation records and return the processed count."""
        processed_count = 0
        for record in records:
            self.save_recommendation(record)
            processed_count += 1
        return processed_count

    def list_recommendations(self, target_draw_no: int | None = None) -> list[RecommendationRecord]:
        """Return saved recommendations, optionally filtered by target draw number."""
        self.initialize_database()
        try:
            with self._connect() as connection:
                if target_draw_no is None:
                    rows = connection.execute(
                        """
                        SELECT *
                        FROM recommendations
                        ORDER BY target_draw_no ASC, recommendation_id ASC
                        """
                    ).fetchall()
                else:
                    rows = connection.execute(
                        """
                        SELECT *
                        FROM recommendations
                        WHERE target_draw_no = ?
                        ORDER BY recommendation_id ASC
                        """,
                        (target_draw_no,),
                    ).fetchall()
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to list recommendations: {exc}") from exc
        return [self._row_to_recommendation(row) for row in rows]

    def save_evaluation(self, evaluation: RecommendationEvaluation) -> None:
        """Insert or update one recommendation evaluation result."""
        self.initialize_database()
        now = self._utc_now()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO recommendation_evaluations (
                        recommendation_id, target_draw_no, recommended_numbers_json,
                        actual_numbers_json, bonus, matched_numbers_json, match_count,
                        bonus_matched, result_label, evaluated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(recommendation_id) DO UPDATE SET
                        target_draw_no = excluded.target_draw_no,
                        recommended_numbers_json = excluded.recommended_numbers_json,
                        actual_numbers_json = excluded.actual_numbers_json,
                        bonus = excluded.bonus,
                        matched_numbers_json = excluded.matched_numbers_json,
                        match_count = excluded.match_count,
                        bonus_matched = excluded.bonus_matched,
                        result_label = excluded.result_label,
                        evaluated_at = excluded.evaluated_at
                    """,
                    (
                        evaluation.recommendation_id,
                        evaluation.target_draw_no,
                        json.dumps(list(evaluation.recommended_numbers), ensure_ascii=False),
                        json.dumps(list(evaluation.actual_numbers), ensure_ascii=False),
                        evaluation.bonus,
                        json.dumps(list(evaluation.matched_numbers), ensure_ascii=False),
                        evaluation.match_count,
                        int(evaluation.bonus_matched),
                        evaluation.result_label,
                        now,
                    ),
                )
        except sqlite3.Error as exc:
            raise LottoDatabaseError(
                f"Failed to save evaluation {evaluation.recommendation_id}: {exc}"
            ) from exc

    def save_evaluations(self, evaluations: Iterable[RecommendationEvaluation]) -> int:
        """Save many evaluation results and return the processed count."""
        processed_count = 0
        for evaluation in evaluations:
            self.save_evaluation(evaluation)
            processed_count += 1
        return processed_count

    def list_evaluations(self) -> list[RecommendationEvaluation]:
        """Return saved recommendation evaluations."""
        self.initialize_database()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM recommendation_evaluations
                    ORDER BY target_draw_no ASC, recommendation_id ASC
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise LottoDatabaseError(f"Failed to list evaluations: {exc}") from exc
        return [self._row_to_evaluation(row) for row in rows]

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open and always close a SQLite connection."""
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _row_to_draw(row: sqlite3.Row) -> LottoDraw:
        """Convert a SQLite row into a validated LottoDraw."""
        return LottoDraw(
            draw_no=int(row["draw_no"]),
            draw_date=datetime.strptime(str(row["draw_date"]), "%Y-%m-%d").date(),
            numbers=(
                int(row["num1"]),
                int(row["num2"]),
                int(row["num3"]),
                int(row["num4"]),
                int(row["num5"]),
                int(row["num6"]),
            ),
            bonus=int(row["bonus"]),
        )

    @staticmethod
    def _row_to_recommendation(row: sqlite3.Row) -> RecommendationRecord:
        """Convert a SQLite row into a RecommendationRecord."""
        combination = GeneratedCombination(
            numbers=tuple(json.loads(row["numbers_json"])),
            score=float(row["score"]),
            odd_even=str(row["odd_even"]),
            high_low=str(row["high_low"]),
            total_sum=int(row["total_sum"]),
            hot_count=int(row["hot_count"]),
            warm_count=int(row["warm_count"]),
            cold_count=int(row["cold_count"]),
            strategy=str(row["strategy"]),
            disclaimer=str(row["disclaimer"]),
        )
        return RecommendationRecord(
            recommendation_id=str(row["recommendation_id"]),
            target_draw_no=int(row["target_draw_no"]),
            created_date=datetime.strptime(str(row["created_date"]), "%Y-%m-%d").date(),
            combination=combination,
        )

    @staticmethod
    def _row_to_evaluation(row: sqlite3.Row) -> RecommendationEvaluation:
        """Convert a SQLite row into a RecommendationEvaluation."""
        return RecommendationEvaluation(
            recommendation_id=str(row["recommendation_id"]),
            target_draw_no=int(row["target_draw_no"]),
            recommended_numbers=tuple(json.loads(row["recommended_numbers_json"])),
            actual_numbers=tuple(json.loads(row["actual_numbers_json"])),
            bonus=int(row["bonus"]),
            matched_numbers=tuple(json.loads(row["matched_numbers_json"])),
            match_count=int(row["match_count"]),
            bonus_matched=bool(row["bonus_matched"]),
            result_label=str(row["result_label"]),
        )

    @staticmethod
    def _utc_now() -> str:
        """Return the current UTC timestamp as an ISO string."""
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
