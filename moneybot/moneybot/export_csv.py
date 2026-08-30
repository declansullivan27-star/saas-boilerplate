"""April in one command: a clean CSV his EA can actually work from."""

from __future__ import annotations

import csv
import io
import os
import sqlite3

from . import ledger
from .money import fmt


def _dollars(cents: int) -> str:
    return f"{cents / 100:.2f}"


def expenses_csv(conn: sqlite3.Connection, year: int) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["date", "vendor", "amount", "schedule_c_category", "deductible", "state", "reason",
         "receipt", "logged_by"]
    )
    rows = conn.execute(
        "SELECT * FROM expenses WHERE date >= ? AND date <= ? ORDER BY date, id",
        (f"{year}-01-01", f"{year}-12-31"),
    ).fetchall()
    for row in rows:
        writer.writerow(
            [
                row["date"],
                row["vendor"],
                _dollars(row["amount_cents"]),
                row["category"],
                "yes" if row["deductible"] else "no",
                row["state_sourced"] or "",
                row["reason"] or "",
                row["receipt_url"] or "",
                row["extracted_by"],
            ]
        )
    return out.getvalue()


def payments_csv(conn: sqlite3.Connection, year: int) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["date", "source", "type", "amount", "state_sourced", "tax_reserved", "note"])
    rows = conn.execute(
        "SELECT p.*, (SELECT COALESCE(SUM(amount_cents),0) FROM allocations a "
        "  WHERE a.payment_id = p.id AND a.bucket = 'reserve') AS reserved "
        "FROM payments p WHERE p.date >= ? AND p.date <= ? ORDER BY p.date, p.id",
        (f"{year}-01-01", f"{year}-12-31"),
    ).fetchall()
    for row in rows:
        writer.writerow(
            [
                row["date"],
                row["source"],
                row["source_type"],
                _dollars(row["amount_cents"]),
                row["state_sourced"],
                _dollars(row["reserved"]),
                row["note"] or "",
            ]
        )
    return out.getvalue()


def summary_csv(conn: sqlite3.Connection, year: int) -> str:
    start, end = f"{year}-01-01", f"{year}-12-31"
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["line", "amount", "note"])
    writer.writerow(["Gross 1099 income", _dollars(ledger.income_between(conn, start, end)), ""])
    writer.writerow(["Deductible expenses", _dollars(ledger.deductions_between(conn, start, end)), ""])
    writer.writerow(["Estimated tax paid", _dollars(ledger.tax_paid_between(conn, start, end)), ""])
    writer.writerow([])
    writer.writerow(["Income by state", "", ""])
    for row in conn.execute(
        "SELECT state_sourced, COALESCE(SUM(amount_cents),0) AS t FROM payments "
        "WHERE date >= ? AND date <= ? GROUP BY state_sourced ORDER BY state_sourced",
        (start, end),
    ).fetchall():
        writer.writerow([row["state_sourced"], _dollars(row["t"]), "sourced at intake"])
    writer.writerow([])
    writer.writerow(["Deductions by Schedule C category", "", ""])
    for category, cents in ledger.category_totals(conn, start, end):
        writer.writerow([category, _dollars(cents), ""])
    writer.writerow([])
    writer.writerow(["", "", "Bookkeeping export. Every figure is an estimate - confirm with the EA."])
    return out.getvalue()


def write_bundle(conn: sqlite3.Connection, year: int, directory: str) -> list[str]:
    """Write the three CSVs to disk and return their paths."""
    os.makedirs(directory, exist_ok=True)
    written = []
    for name, body in (
        (f"expenses-{year}.csv", expenses_csv(conn, year)),
        (f"payments-{year}.csv", payments_csv(conn, year)),
        (f"summary-{year}.csv", summary_csv(conn, year)),
    ):
        path = os.path.join(directory, name)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            handle.write(body)
        written.append(path)
    return written


def totals_line(conn: sqlite3.Connection, year: int) -> str:
    start, end = f"{year}-01-01", f"{year}-12-31"
    income = ledger.income_between(conn, start, end)
    deductions = ledger.deductions_between(conn, start, end)
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM expenses WHERE deductible = 1 AND date >= ? AND date <= ?",
        (start, end),
    ).fetchone()["c"]
    plural = "deduction" if count == 1 else "deductions"
    return f"{year}: {fmt(income)} income, {count} {plural} worth {fmt(deductions)}."
