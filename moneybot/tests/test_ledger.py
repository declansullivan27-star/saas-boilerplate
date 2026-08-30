from datetime import date

import pytest

from moneybot import ledger


def test_payment_creates_four_allocations(conn):
    result = ledger.record_payment(
        conn, amount_cents=1_000_000, source="collective", state_sourced="KS", date="2026-08-05"
    )
    rows = conn.execute(
        "SELECT bucket, amount_cents FROM allocations WHERE payment_id = ?", (result.payment_id,)
    ).fetchall()
    assert len(rows) == 4
    assert sum(r["amount_cents"] for r in rows) == 1_000_000


def test_balances_derive_from_the_ledger(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="MO")
    ledger.record_expense(conn, vendor="Marriott", amount_cents=21_450, category="Travel")
    balances = ledger.balances(conn)
    assert balances["spending"] == 380_000 - 21_450
    assert balances["reserve"] == 370_000


def test_a_zero_payment_is_refused(conn):
    with pytest.raises(ValueError):
        ledger.record_payment(conn, amount_cents=0, source="nothing", state_sourced="MO")


def test_a_negative_expense_is_refused(conn):
    with pytest.raises(ValueError):
        ledger.record_expense(conn, vendor="x", amount_cents=-5)


def test_tax_payments_draw_down_the_reserve(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="KS")
    ledger.record_expense(
        conn, vendor="IRS", amount_cents=370_000, category="Taxes and licenses", bucket="reserve"
    )
    assert ledger.bucket_balance(conn, "reserve") == 0
    assert ledger.bucket_balance(conn, "spending") == 380_000


def test_reserve_splits_by_the_state_income_was_sourced_to(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="KS")
    ledger.record_payment(conn, amount_cents=500_000, source="camp", state_sourced="MO")
    assert ledger.reserve_by_state(conn) == {"KS": 370_000, "MO": 185_000}


def test_undo_removes_the_payment_and_its_allocations(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="MO")
    assert ledger.undo_last(conn).startswith("payment:")
    assert ledger.balances(conn) == {"reserve": 0, "savings": 0, "swing": 0, "spending": 0}
    assert conn.execute("SELECT COUNT(*) AS c FROM allocations").fetchone()["c"] == 0


def test_undo_takes_the_most_recent_entry(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="MO")
    ledger.record_expense(conn, vendor="gas", amount_cents=4_218)
    assert ledger.undo_last(conn).startswith("expense:")
    assert ledger.bucket_balance(conn, "spending") == 380_000


def test_undo_with_an_empty_ledger(conn):
    assert ledger.undo_last(conn) is None


def test_move_between_buckets_is_zero_sum(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="MO")
    before = sum(ledger.balances(conn).values())
    ledger.move_between_buckets(conn, src="swing", dst="spending", amount_cents=20_000)
    assert ledger.bucket_balance(conn, "swing") == 80_000
    assert ledger.bucket_balance(conn, "spending") == 400_000
    assert sum(ledger.balances(conn).values()) == before


def test_move_refuses_to_overdraw(conn):
    ledger.record_payment(conn, amount_cents=100_000, source="collective", state_sourced="MO")
    with pytest.raises(ValueError, match="only"):
        ledger.move_between_buckets(conn, src="swing", dst="spending", amount_cents=999_999)


def test_next_due_date_wraps_into_next_month():
    assert ledger.next_due_date(1, date(2026, 8, 30)) == date(2026, 9, 1)
    assert ledger.next_due_date(15, date(2026, 8, 5)) == date(2026, 8, 15)
    assert ledger.next_due_date(1, date(2026, 12, 30)) == date(2027, 1, 1)


def test_commitments_look_forward_thirty_days(conn):
    ledger.add_commitment(conn, name="rent", amount_cents=120_000, day_of_month=1)
    # Rent is two days out even though it is not "left in August".
    assert ledger.commitments_due_within(conn, date(2026, 8, 30), 30) == 120_000
    assert ledger.commitments_remaining_this_month(conn, date(2026, 8, 30)) == 0


def test_adding_the_same_bill_twice_updates_it(conn):
    ledger.add_commitment(conn, name="rent", amount_cents=120_000, day_of_month=1)
    ledger.add_commitment(conn, name="Rent", amount_cents=130_000, day_of_month=3)
    rows = ledger.list_commitments(conn)
    assert len(rows) == 1
    assert rows[0]["amount_cents"] == 130_000
    assert rows[0]["day_of_month"] == 3


def test_removing_a_bill(conn):
    ledger.add_commitment(conn, name="rent", amount_cents=120_000)
    assert ledger.remove_commitment(conn, "RENT") is True
    assert ledger.list_commitments(conn) == []
    assert ledger.remove_commitment(conn, "rent") is False


def test_all_ledger_amounts_feeds_the_guardrail(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="MO")
    amounts = ledger.all_ledger_amounts(conn)
    assert 1_000_000 in amounts and 370_000 in amounts and 380_000 in amounts
    assert 999_999 not in amounts
