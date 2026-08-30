"""The nag. Cron-driven, deterministic, no LLM.

Deadlines are the other half of the product. A deduction he forgets costs him
a few hundred dollars; a quarterly payment he forgets costs him a penalty and
a letter from the IRS.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from . import advice, ledger, reply as fmt_reply, taxes
from .config import ESTIMATE_DISCLAIMER
from .money import fmt


@dataclass
class Nag:
    kind: str
    key: str
    text: str


def _already_sent(conn: sqlite3.Connection, kind: str, key: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM nag_log WHERE kind = ? AND key = ?", (kind, key)
    ).fetchone() is not None


def mark_sent(conn: sqlite3.Connection, kind: str, key: str) -> None:
    conn.execute("INSERT OR IGNORE INTO nag_log (kind, key) VALUES (?,?)", (kind, key))
    conn.commit()


def monthly_nag(conn: sqlite3.Connection, on: date) -> Nag | None:
    """First of the month: last month's numbers, this month's runway."""
    if on.day != 1:
        return None
    key = on.strftime("%Y-%m")
    if _already_sent(conn, "monthly", key):
        return None
    previous_end = date(on.year, on.month, 1).toordinal() - 1
    previous = date.fromordinal(previous_end)
    start, end = advice.month_bounds(previous)
    income = ledger.income_between(conn, start, end)
    spent = ledger.spending_between(conn, start, end)
    deductions = ledger.deductions_between(conn, start, end)
    picture = advice.picture(conn, on)
    lines = [
        f"{previous.strftime('%B')} closed out: {fmt(income)} in, {fmt(spent)} out.",
        f"Deductions logged: {fmt(deductions)}.",
        f"Today you have {fmt(picture.spendable_cents)} spendable"
        + (f", {fmt(picture.committed_cents)} of it spoken for by bills." if picture.committed_cents else "."),
        f"Swing {fmt(picture.swing_cents)}. Savings {fmt(picture.savings_cents)}.",
    ]
    if deductions == 0:
        lines.append("No receipts logged last month. That is money you are leaving on the table.")
    return Nag("monthly", key, fmt_reply.clip("\n".join(lines)))


def quarterly_nags(conn: sqlite3.Connection, on: date) -> list[Nag]:
    """21 days out, 7 days out, and the morning it's due."""
    out = []
    for quarter, days in taxes.due_for_nag(on):
        key = f"{quarter.key}:{days}"
        if _already_sent(conn, "quarterly", key):
            continue
        set_aside = taxes.set_aside_for(conn, quarter)
        split = taxes.state_split_for(conn, quarter)
        reserve = ledger.bucket_balance(conn, "reserve")
        when = "today" if days == 0 else f"in {days} days"
        lines = [
            f"{quarter.key} estimated tax is due {quarter.due.strftime('%a %b')} {quarter.due.day} - {when}.",
            f"Set aside from {quarter.label} income: {fmt(set_aside)}.",
        ]
        if split:
            lines.append("Sourced: " + ", ".join(f"{st} {fmt(c)}" for st, c in sorted(split.items())))
        if reserve < set_aside:
            lines.append(
                f"Heads up: the reserve is at {fmt(reserve)}, less than that. Something came out of it."
            )
        lines.append(taxes.pay_links(sorted(split)))
        lines.append(ESTIMATE_DISCLAIMER)
        lines.append("Text me the amount when you pay it: 'paid 3700 estimated tax'")
        out.append(Nag("quarterly", key, fmt_reply.clip("\n".join(lines), limit=800)))
    return out


def due_nags(conn: sqlite3.Connection, on: date | None = None) -> list[Nag]:
    on = on or date.today()
    nags = []
    monthly = monthly_nag(conn, on)
    if monthly:
        nags.append(monthly)
    nags.extend(quarterly_nags(conn, on))
    return nags


def run(config, send, on: date | None = None) -> list[Nag]:
    """Called by cron. ``send`` is ``callable(text) -> bool``.

    A nag is only marked sent once the channel confirms it went out, so a
    failed send is retried on the next cron tick instead of vanishing.
    """
    from . import db

    conn = db.connect(config.db_path)
    try:
        db.init(conn, config.ratios)
        sent = []
        for nag in due_nags(conn, on):
            if send(nag.text):
                mark_sent(conn, nag.kind, nag.key)
                db.log_message(conn, "out", "nag", nag.kind, nag.text)
                sent.append(nag)
        return sent
    finally:
        conn.close()
