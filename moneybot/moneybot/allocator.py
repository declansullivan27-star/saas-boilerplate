"""The split. Deterministic, no LLM, ever.

A model is never allowed near a number that decides what he sets aside.
This module is pure arithmetic over integer cents.
"""

from __future__ import annotations

import sqlite3

from .config import BUCKET_ORDER
from .money import split_by_ratio


def ratios_from_db(conn: sqlite3.Connection) -> dict[str, float]:
    rows = conn.execute("SELECT name, target_pct FROM buckets ORDER BY sort_order").fetchall()
    ratios = {r["name"]: float(r["target_pct"]) for r in rows}
    for name in BUCKET_ORDER:
        ratios.setdefault(name, 0.0)
    ratios["spending"] = 0.0  # always the remainder
    return ratios


def validate_ratios(ratios: dict[str, float]) -> None:
    fixed = sum(v for k, v in ratios.items() if k != "spending")
    if fixed >= 1.0:
        raise ValueError(
            f"reserve+savings+swing = {fixed:.0%}; that leaves nothing spendable. Lower one of them."
        )
    if any(v < 0 for v in ratios.values()):
        raise ValueError("percentages cannot be negative")


def allocate(amount_cents: int, ratios: dict[str, float]) -> dict[str, int]:
    """Split a payment across the four buckets. Parts always sum to the whole."""
    validate_ratios(ratios)
    parts = split_by_ratio(amount_cents, ratios, remainder_key="spending")
    assert sum(parts.values()) == amount_cents, "allocation must be lossless"
    return {name: parts[name] for name in BUCKET_ORDER}
