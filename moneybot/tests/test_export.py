import csv
import io

from moneybot import export_csv, ledger


def _rows(text):
    return list(csv.reader(io.StringIO(text)))


def test_expenses_csv_has_what_an_ea_needs(conn):
    ledger.record_expense(
        conn, vendor="Marriott Dallas", amount_cents=21_450, category="Travel",
        date="2026-08-20", deductible=True, reason="camp appearance", state_sourced="KS",
    )
    rows = _rows(export_csv.expenses_csv(conn, 2026))
    assert rows[0][:5] == ["date", "vendor", "amount", "schedule_c_category", "deductible"]
    assert rows[1][:6] == ["2026-08-20", "Marriott Dallas", "214.50", "Travel", "yes", "KS"]


def test_expenses_csv_is_scoped_to_the_year(conn):
    ledger.record_expense(conn, vendor="old", amount_cents=100, date="2025-12-31")
    ledger.record_expense(conn, vendor="new", amount_cents=100, date="2026-01-01")
    assert len(_rows(export_csv.expenses_csv(conn, 2026))) == 2


def test_payments_csv_carries_the_state_and_the_reserve(conn):
    ledger.record_payment(
        conn, amount_cents=1_000_000, source="collective", source_type="collective",
        state_sourced="KS", date="2026-08-05",
    )
    rows = _rows(export_csv.payments_csv(conn, 2026))
    assert rows[1] == ["2026-08-05", "collective", "collective", "10000.00", "KS", "3700.00", ""]


def test_summary_totals(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="a", state_sourced="KS", date="2026-02-01")
    ledger.record_payment(conn, amount_cents=500_000, source="b", state_sourced="MO", date="2026-03-01")
    ledger.record_expense(
        conn, vendor="Marriott", amount_cents=21_450, category="Travel",
        date="2026-04-01", deductible=True,
    )
    body = export_csv.summary_csv(conn, 2026)
    assert "15000.00" in body
    assert "214.50" in body
    assert "KS,10000.00" in body and "MO,5000.00" in body
    assert "confirm with the EA" in body


def test_bundle_writes_three_files(conn, tmp_path):
    paths = export_csv.write_bundle(conn, 2026, str(tmp_path / "out"))
    assert len(paths) == 3
    assert all(p.endswith(".csv") for p in paths)


def test_totals_line_pluralizes(conn):
    ledger.record_expense(conn, vendor="a", amount_cents=100, date="2026-01-01", deductible=True)
    assert "1 deduction worth" in export_csv.totals_line(conn, 2026)
    ledger.record_expense(conn, vendor="b", amount_cents=100, date="2026-01-02", deductible=True)
    assert "2 deductions worth" in export_csv.totals_line(conn, 2026)
