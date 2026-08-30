"""SQLite storage. Single file, trivial to back up, no ORM.

Balances are never stored — they are always derived from allocations,
expenses and adjustments. Stored balances drift; derived ones cannot.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents   INTEGER NOT NULL,
    source         TEXT    NOT NULL,
    source_type    TEXT    NOT NULL DEFAULT 'other',
    date           TEXT    NOT NULL,
    state_sourced  TEXT    NOT NULL,
    note           TEXT,
    raw_text       TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS allocations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id   INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    bucket       TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor       TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL,
    category     TEXT    NOT NULL DEFAULT 'Uncategorized',
    date         TEXT    NOT NULL,
    deductible   INTEGER NOT NULL DEFAULT 0,
    reason       TEXT,
    receipt_url  TEXT,
    bucket       TEXT    NOT NULL DEFAULT 'spending',
    state_sourced TEXT,
    extracted_by TEXT    NOT NULL DEFAULT 'manual',
    raw_text     TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS buckets (
    name       TEXT PRIMARY KEY,
    label      TEXT NOT NULL,
    target_pct REAL NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS deals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    counterparty TEXT,
    term         TEXT,
    fee_pct      REAL,
    deal_type    TEXT,
    flags        TEXT,
    pdf_url      TEXT,
    screen_json  TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS adjustments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket       TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL,
    reason       TEXT,
    date         TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS commitments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL DEFAULT 1,
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS message_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    direction  TEXT NOT NULL,
    channel    TEXT NOT NULL,
    party      TEXT,
    body       TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nag_log (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    kind    TEXT NOT NULL,
    key     TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (kind, key)
);

CREATE INDEX IF NOT EXISTS idx_payments_date   ON payments(date);
CREATE INDEX IF NOT EXISTS idx_expenses_date   ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_alloc_bucket    ON allocations(bucket);
CREATE INDEX IF NOT EXISTS idx_expenses_bucket ON expenses(bucket);
"""


def connect(path: str) -> sqlite3.Connection:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init(conn: sqlite3.Connection, ratios: dict[str, float] | None = None) -> None:
    conn.executescript(SCHEMA)
    from .config import BUCKET_LABELS, BUCKET_ORDER, DEFAULT_RATIOS

    ratios = ratios or DEFAULT_RATIOS
    for order, name in enumerate(BUCKET_ORDER):
        conn.execute(
            "INSERT INTO buckets (name, label, target_pct, sort_order) VALUES (?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET label=excluded.label, sort_order=excluded.sort_order",
            (name, BUCKET_LABELS[name], float(ratios.get(name, 0.0)), order),
        )
    conn.commit()


@contextmanager
def session(path: str, ratios: dict[str, float] | None = None):
    conn = connect(path)
    try:
        init(conn, ratios)
        yield conn
    finally:
        conn.close()


# --- settings kv ----------------------------------------------------------

def get_setting(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str | None) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def log_message(conn: sqlite3.Connection, direction: str, channel: str, party: str, body: str) -> None:
    conn.execute(
        "INSERT INTO message_log (direction, channel, party, body) VALUES (?,?,?,?)",
        (direction, channel, party, body),
    )
    conn.commit()
