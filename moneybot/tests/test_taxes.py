from datetime import date

from moneybot import ledger, taxes


def test_quarter_periods_and_due_dates():
    q1, q2, q3, q4 = taxes.quarters(2026)
    assert (q1.start, q1.end, q1.due) == (date(2026, 1, 1), date(2026, 3, 31), date(2026, 4, 15))
    assert (q2.start, q2.end, q2.due) == (date(2026, 4, 1), date(2026, 5, 31), date(2026, 6, 15))
    assert (q3.start, q3.end, q3.due) == (date(2026, 6, 1), date(2026, 8, 31), date(2026, 9, 15))
    assert (q4.start, q4.end, q4.due) == (date(2026, 9, 1), date(2026, 12, 31), date(2027, 1, 15))


def test_a_weekend_deadline_moves_to_monday():
    # 2028-04-15 is a Saturday.
    assert taxes.quarters(2028)[0].due == date(2028, 4, 17)
    # 2029-04-15 is a Sunday.
    assert taxes.quarters(2029)[0].due == date(2029, 4, 16)


def test_next_deadline_includes_today():
    assert taxes.next_deadline(date(2026, 9, 15)).key == "2026-Q3"
    assert taxes.next_deadline(date(2026, 9, 16)).key == "2026-Q4"


def test_nags_fire_at_twentyone_seven_and_zero():
    assert [d for _, d in taxes.due_for_nag(date(2026, 8, 25))] == [21]
    assert [d for _, d in taxes.due_for_nag(date(2026, 9, 8))] == [7]
    assert [d for _, d in taxes.due_for_nag(date(2026, 9, 15))] == [0]
    assert taxes.due_for_nag(date(2026, 9, 10)) == []


def test_set_aside_counts_only_income_from_that_period(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="a", state_sourced="KS", date="2026-07-05")
    ledger.record_payment(conn, amount_cents=500_000, source="b", state_sourced="MO", date="2026-09-05")
    q3 = taxes.quarters(2026)[2]
    assert taxes.set_aside_for(conn, q3) == 370_000
    assert taxes.state_split_for(conn, q3) == {"KS": 370_000}


def test_tax_already_paid_reduces_what_is_set_aside(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="a", state_sourced="KS", date="2026-07-05")
    ledger.record_expense(
        conn, vendor="IRS", amount_cents=100_000, category="Taxes and licenses",
        bucket="reserve", date="2026-08-01",
    )
    assert taxes.set_aside_for(conn, taxes.quarters(2026)[2]) == 270_000


def test_pay_links_include_the_states_that_have_income():
    links = taxes.pay_links(["KS", "MO"])
    assert "irs.gov" in links and "kdor.ks.gov" in links and "mytax.mo.gov" in links
