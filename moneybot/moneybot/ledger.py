"""The deterministic ledger: writes, balances, and the answer to
"what can I spend right now".

Nothing in this module calls a model.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date as _date

from .allocator import allocate, ratios_from_db
from .config import BUCKET_ORDER, SUPPORTED_STATES

INCOME_TYPES = ("collective", "nil_brand", "appearance", "autograph", "camp", "royalty", "other")


def today() -> str:
    return _date.today().isoformat()


def normalize_state(state: str | None, default: str) -> str:
    if not state:
        return default
    s = state.strip().upper()
    return s if s in SUPPORTED_STATES else (s[:2] if len(s) >= 2 else default)


@dataclass
class PaymentResult:
    payment_id: int
    amount_cents: int
    source: str
    state_sourced: str
    allocations: dict[str, int]


@dataclass
class ExpenseResult:
    expense_id: int
    vendor: str
    amount_cents: int
    category: str
    deductible: bool
    reason: str | None
    bucket: str
    spendable_after_cents: int


# --- writes ---------------------------------------------------------------

def record_payment(
    conn: sqlite3.Connection,
    *,
    amount_cents: int,
    source: str,
    source_type: str = "other",
    date: str | None = None,
    state_sourced: str = "MO",
    note: str | None = None,
    raw_text: str | None = None,
) -> PaymentResult:
    if amount_cents == 0:
        raise ValueError("a payment of $0 is not a payment")
    ratios = ratios_from_db(conn)
    parts = allocate(amount_cents, ratios)
    cur = conn.execute(
        "INSERT INTO payments (amount_cents, source, source_type, date, state_sourced, note, raw_text) "
        "VALUES (?,?,?,?,?,?,?)",
        (amount_cents, source, source_type, date or today(), state_sourced, note, raw_text),
    )
    payment_id = int(cur.lastrowid)
    conn.executemany(
        "INSERT INTO allocations (payment_id, bucket, amount_cents) VALUES (?,?,?)",
        [(payment_id, bucket, cents) for bucket, cents in parts.items()],
    )
    conn.commit()
    return PaymentResult(payment_id, amount_cents, source, state_sourced, parts)


def record_expense(
    conn: sqlite3.Connection,
    *,
    vendor: str,
    amount_cents: int,
    category: str = "Uncategorized",
    date: str | None = None,
    deductible: bool = False,
    reason: str | None = None,
    receipt_url: str | None = None,
    bucket: str = "spending",
    state_sourced: str | None = None,
    extracted_by: str = "manual",
    raw_text: str | None = None,
) -> ExpenseResult:
    if amount_cents <= 0:
        raise ValueError("an expense must be a positive amount")
    if bucket not in BUCKET_ORDER:
        raise ValueError(f"unknown bucket {bucket!r}")
    cur = conn.execute(
        "INSERT INTO expenses (vendor, amount_cents, category, date, deductible, reason, receipt_url,"
        " bucket, state_sourced, extracted_by, raw_text) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            vendor,
            amount_cents,
            category,
            date or today(),
            1 if deductible else 0,
            reason,
            receipt_url,
            bucket,
            state_sourced,
            extracted_by,
            raw_text,
        ),
    )
    conn.commit()
    return ExpenseResult(
        expense_id=int(cur.lastrowid),
        vendor=vendor,
        amount_cents=amount_cents,
        category=category,
        deductible=deductible,
        reason=reason,
        bucket=bucket,
        spendable_after_cents=bucket_balance(conn, bucket),
    )


def record_adjustment(
    conn: sqlite3.Connection, *, bucket: str, amount_cents: int, reason: str, date: str | None = None
) -> int:
    if bucket not in BUCKET_ORDER:
        raise ValueError(f"unknown bucket {bucket!r}")
    cur = conn.execute(
        "INSERT INTO adjustments (bucket, amount_cents, reason, date) VALUES (?,?,?,?)",
        (bucket, amount_cents, reason, date or today()),
    )
    conn.commit()
    return int(cur.lastrowid)


def move_between_buckets(
    conn: sqlite3.Connection, *, src: str, dst: str, amount_cents: int, reason: str = "manual move"
) -> tuple[int, int]:
    """Move money between buckets. Bookkeeping only — the bot never moves real money."""
    if src == dst:
        raise ValueError("source and destination are the same bucket")
    if amount_cents <= 0:
        raise ValueError("move must be a positive amount")
    available = bucket_balance(conn, src)
    if amount_cents > available:
        raise ValueError(f"only {available} cents in {src}")
    record_adjustment(conn, bucket=src, amount_cents=-amount_cents, reason=f"{reason} -> {dst}")
    record_adjustment(conn, bucket=dst, amount_cents=amount_cents, reason=f"{reason} <- {src}")
    return bucket_balance(conn, src), bucket_balance(conn, dst)


def undo_last(conn: sqlite3.Connection) -> str | None:
    """Delete the most recently created payment or expense. Returns a description."""
    pay = conn.execute(
        "SELECT id, created_at, amount_cents, source FROM payments ORDER BY created_at DESC, id DESC LIMIT 1"
    ).fetchone()
    exp = conn.execute(
        "SELECT id, created_at, amount_cents, vendor FROM expenses ORDER BY created_at DESC, id DESC LIMIT 1"
    ).fetchone()
    if not pay and not exp:
        return None
    take_expense = bool(exp) and (not pay or exp["created_at"] >= pay["created_at"])
    if take_expense:
        conn.execute("DELETE FROM expenses WHERE id = ?", (exp["id"],))
        conn.commit()
        return f"expense:{exp['id']}:{exp['vendor']}:{exp['amount_cents']}"
    conn.execute("DELETE FROM allocations WHERE payment_id = ?", (pay["id"],))
    conn.execute("DELETE FROM payments WHERE id = ?", (pay["id"],))
    conn.commit()
    return f"payment:{pay['id']}:{pay['source']}:{pay['amount_cents']}"


# --- reads ----------------------------------------------------------------

def bucket_balance(conn: sqlite3.Connection, bucket: str) -> int:
    allocated = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM allocations WHERE bucket = ?", (bucket,)
    ).fetchone()["t"]
    spent = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM expenses WHERE bucket = ?", (bucket,)
    ).fetchone()["t"]
    adjusted = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM adjustments WHERE bucket = ?", (bucket,)
    ).fetchone()["t"]
    return int(allocated) - int(spent) + int(adjusted)


def balances(conn: sqlite3.Connection) -> dict[str, int]:
    return {bucket: bucket_balance(conn, bucket) for bucket in BUCKET_ORDER}


def reserve_by_state(conn: sqlite3.Connection) -> dict[str, int]:
    """Tax reserve broken out by the state the income was sourced to."""
    rows = conn.execute(
        "SELECT p.state_sourced AS st, COALESCE(SUM(a.amount_cents), 0) AS t "
        "FROM allocations a JOIN payments p ON p.id = a.payment_id "
        "WHERE a.bucket = 'reserve' GROUP BY p.state_sourced"
    ).fetchall()
    out = {r["st"]: int(r["t"]) for r in rows}
    paid = conn.execute(
        "SELECT COALESCE(state_sourced, '?') AS st, COALESCE(SUM(amount_cents), 0) AS t "
        "FROM expenses WHERE bucket = 'reserve' GROUP BY state_sourced"
    ).fetchall()
    for row in paid:
        out[row["st"]] = out.get(row["st"], 0) - int(row["t"])
    return {k: v for k, v in sorted(out.items()) if v}


def income_between(conn: sqlite3.Connection, start: str, end: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM payments WHERE date >= ? AND date <= ?",
        (start, end),
    ).fetchone()
    return int(row["t"])


def spending_between(conn: sqlite3.Connection, start: str, end: str, bucket: str | None = None) -> int:
    sql = "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM expenses WHERE date >= ? AND date <= ?"
    args: list = [start, end]
    if bucket:
        sql += " AND bucket = ?"
        args.append(bucket)
    return int(conn.execute(sql, args).fetchone()["t"])


def reserve_allocated_between(conn: sqlite3.Connection, start: str, end: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(a.amount_cents), 0) AS t FROM allocations a "
        "JOIN payments p ON p.id = a.payment_id "
        "WHERE a.bucket = 'reserve' AND p.date >= ? AND p.date <= ?",
        (start, end),
    ).fetchone()
    return int(row["t"])


def tax_paid_between(conn: sqlite3.Connection, start: str, end: str) -> int:
    """Actual tax payments only.

    Deliberately narrower than "everything that came out of the reserve": if
    he raids the reserve for something that is not a tax payment, the amount
    he still owes does not go down, and the nag needs to say so.
    """
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM expenses "
        "WHERE bucket = 'reserve' AND category = 'Taxes and licenses' "
        "AND date >= ? AND date <= ?",
        (start, end),
    ).fetchone()
    return int(row["t"])


def deductions_between(conn: sqlite3.Connection, start: str, end: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM expenses "
        "WHERE deductible = 1 AND date >= ? AND date <= ?",
        (start, end),
    ).fetchone()
    return int(row["t"])


def recent_expenses(conn: sqlite3.Connection, limit: int = 5) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT ?", (limit,)
    ).fetchall()


def category_totals(conn: sqlite3.Connection, start: str, end: str) -> list[tuple[str, int]]:
    rows = conn.execute(
        "SELECT category, COALESCE(SUM(amount_cents), 0) AS t FROM expenses "
        "WHERE deductible = 1 AND date >= ? AND date <= ? GROUP BY category ORDER BY t DESC",
        (start, end),
    ).fetchall()
    return [(r["category"], int(r["t"])) for r in rows]


def all_ledger_amounts(conn: sqlite3.Connection) -> set[int]:
    """Every dollar figure the ledger can vouch for.

    :mod:`moneybot.guardrails` uses this to verify any model-written prose
    before it is sent: a number that is not in here does not go out.
    """
    amounts: set[int] = set(balances(conn).values())
    amounts |= {abs(v) for v in reserve_by_state(conn).values()}
    for table, column in (("payments", "amount_cents"), ("expenses", "amount_cents"),
                          ("allocations", "amount_cents")):
        amounts |= {
            int(r[0]) for r in conn.execute(f"SELECT DISTINCT {column} FROM {table}").fetchall()
        }
    return {a for a in amounts if a}


# --- recurring commitments ("what he's spending") -------------------------

def add_commitment(conn: sqlite3.Connection, *, name: str, amount_cents: int, day_of_month: int = 1) -> int:
    if amount_cents <= 0:
        raise ValueError("a bill must be a positive amount")
    day_of_month = max(1, min(28, int(day_of_month)))
    existing = conn.execute(
        "SELECT id FROM commitments WHERE active = 1 AND lower(name) = lower(?)", (name,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE commitments SET amount_cents = ?, day_of_month = ? WHERE id = ?",
            (amount_cents, day_of_month, existing["id"]),
        )
        conn.commit()
        return int(existing["id"])
    cur = conn.execute(
        "INSERT INTO commitments (name, amount_cents, day_of_month) VALUES (?,?,?)",
        (name, amount_cents, day_of_month),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_commitments(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM commitments WHERE active = 1 ORDER BY day_of_month, id"
    ).fetchall()


def remove_commitment(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "UPDATE commitments SET active = 0 WHERE active = 1 AND lower(name) = lower(?)", (name,)
    )
    conn.commit()
    return cur.rowcount > 0


def monthly_commitments_total(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM commitments WHERE active = 1"
    ).fetchone()
    return int(row["t"])


def next_due_date(day_of_month: int, on: _date) -> _date:
    """The next time a monthly bill lands, counting from ``on``."""
    day = max(1, min(28, int(day_of_month)))
    if day >= on.day:
        return _date(on.year, on.month, day)
    year, month = (on.year + 1, 1) if on.month == 12 else (on.year, on.month + 1)
    return _date(year, month, day)


def commitments_due_within(conn: sqlite3.Connection, on: _date | None = None, days: int = 30) -> int:
    """Bills that land in the next ``days`` days.

    A rolling window, not a calendar month: on the 30th, next month's rent is
    two days away and is absolutely not spendable money.
    """
    on = on or _date.today()
    total = 0
    for row in list_commitments(conn):
        if (next_due_date(row["day_of_month"], on) - on).days < days:
            total += int(row["amount_cents"])
    return total


def commitments_remaining_this_month(conn: sqlite3.Connection, on: _date | None = None) -> int:
    """Bills whose due day has not arrived yet this calendar month."""
    on = on or _date.today()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS t FROM commitments WHERE active = 1 AND day_of_month >= ?",
        (on.day,),
    ).fetchone()
    return int(row["t"])
