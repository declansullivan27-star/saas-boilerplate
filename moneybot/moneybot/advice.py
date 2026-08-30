"""The answer to "what can I spend right now" — pure arithmetic.

Nothing here is a judgement call: every figure is a subtraction over the
deterministic ledger, and no model is involved.
"""

from __future__ import annotations

import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date

from . import ledger, taxes


HORIZON_DAYS = 30


@dataclass
class SpendPicture:
    spendable_cents: int
    committed_cents: int
    free_cents: int
    horizon_days: int
    days_left_in_month: int
    per_day_cents: int
    swing_cents: int
    savings_cents: int
    reserve_cents: int
    next_quarter_key: str
    next_quarter_due: date
    next_quarter_set_aside_cents: int
    reserve_by_state: dict[str, int]
    month_spent_cents: int
    month_income_cents: int


def days_left_in_month(on: date) -> int:
    return calendar.monthrange(on.year, on.month)[1] - on.day + 1


def month_bounds(on: date) -> tuple[str, str]:
    last = calendar.monthrange(on.year, on.month)[1]
    return date(on.year, on.month, 1).isoformat(), date(on.year, on.month, last).isoformat()


def picture(conn: sqlite3.Connection, on: date | None = None) -> SpendPicture:
    on = on or date.today()
    bal = ledger.balances(conn)
    committed = ledger.commitments_due_within(conn, on, HORIZON_DAYS)
    spendable = bal["spending"]
    free = spendable - committed
    quarter = taxes.next_deadline(on)
    start, end = month_bounds(on)
    return SpendPicture(
        spendable_cents=spendable,
        committed_cents=committed,
        free_cents=free,
        horizon_days=HORIZON_DAYS,
        days_left_in_month=days_left_in_month(on),
        per_day_cents=max(0, free) // HORIZON_DAYS,
        swing_cents=bal["swing"],
        savings_cents=bal["savings"],
        reserve_cents=bal["reserve"],
        next_quarter_key=quarter.key,
        next_quarter_due=quarter.due,
        next_quarter_set_aside_cents=taxes.set_aside_for(conn, quarter),
        reserve_by_state=ledger.reserve_by_state(conn),
        month_spent_cents=ledger.spending_between(conn, start, end),
        month_income_cents=ledger.income_between(conn, start, end),
    )
