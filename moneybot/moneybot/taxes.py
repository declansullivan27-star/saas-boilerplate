"""Quarterly estimated-tax calendar and the reserve math behind the nags.

This module computes *what has been set aside*, not what is owed. It is a
bookkeeping figure, always labeled an estimate, never tax advice.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from . import ledger
from .config import IRS_DIRECT_PAY, STATE_PAY_LINKS

# (label, period start (month, day), period end (month, day), due (month, day), due-year offset)
_QUARTER_SPECS = (
    ("Q1", (1, 1), (3, 31), (4, 15), 0),
    ("Q2", (4, 1), (5, 31), (6, 15), 0),
    ("Q3", (6, 1), (8, 31), (9, 15), 0),
    ("Q4", (9, 1), (12, 31), (1, 15), 1),
)

NAG_DAYS = (21, 7)


def _shift_off_weekend(d: date) -> date:
    """IRS deadlines that land on a weekend move to the following Monday."""
    if d.weekday() == 5:
        return d + timedelta(days=2)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


@dataclass(frozen=True)
class Quarter:
    label: str
    tax_year: int
    start: date
    end: date
    due: date

    @property
    def key(self) -> str:
        return f"{self.tax_year}-{self.label}"

    def days_until(self, today: date) -> int:
        return (self.due - today).days


def quarters(tax_year: int) -> list[Quarter]:
    out = []
    for label, (sm, sd), (em, ed), (dm, dd), year_offset in _QUARTER_SPECS:
        out.append(
            Quarter(
                label=label,
                tax_year=tax_year,
                start=date(tax_year, sm, sd),
                end=date(tax_year, em, ed),
                due=_shift_off_weekend(date(tax_year + year_offset, dm, dd)),
            )
        )
    return out


def all_quarters_around(today: date) -> list[Quarter]:
    return sorted(
        quarters(today.year - 1) + quarters(today.year) + quarters(today.year + 1),
        key=lambda q: q.due,
    )


def next_deadline(today: date) -> Quarter:
    """The next quarterly deadline on or after ``today``."""
    for quarter in all_quarters_around(today):
        if quarter.due >= today:
            return quarter
    raise RuntimeError("no upcoming deadline")  # pragma: no cover


def due_for_nag(today: date) -> list[tuple[Quarter, int]]:
    """Quarters that are exactly 21 or 7 days out (or due today)."""
    hits = []
    for quarter in all_quarters_around(today):
        delta = quarter.days_until(today)
        if delta in NAG_DAYS or delta == 0:
            hits.append((quarter, delta))
    return hits


def set_aside_for(conn: sqlite3.Connection, quarter: Quarter) -> int:
    """Cents allocated to the tax reserve from income earned in this quarter's
    period, less any tax payments already logged against that period."""
    start, end = quarter.start.isoformat(), quarter.end.isoformat()
    return ledger.reserve_allocated_between(conn, start, end) - ledger.tax_paid_between(conn, start, end)


def state_split_for(conn: sqlite3.Connection, quarter: Quarter) -> dict[str, int]:
    rows = conn.execute(
        "SELECT p.state_sourced AS st, COALESCE(SUM(a.amount_cents), 0) AS t "
        "FROM allocations a JOIN payments p ON p.id = a.payment_id "
        "WHERE a.bucket = 'reserve' AND p.date >= ? AND p.date <= ? GROUP BY p.state_sourced",
        (quarter.start.isoformat(), quarter.end.isoformat()),
    ).fetchall()
    return {r["st"]: int(r["t"]) for r in rows if int(r["t"])}


def pay_links(states: list[str]) -> str:
    links = [f"IRS: {IRS_DIRECT_PAY}"]
    for state in states:
        if state in STATE_PAY_LINKS:
            links.append(f"{state}: {STATE_PAY_LINKS[state]}")
    return "\n".join(links)
