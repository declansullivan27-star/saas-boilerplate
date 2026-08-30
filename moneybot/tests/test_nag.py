from datetime import date

from moneybot import ledger, nag


def _income(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="collective", state_sourced="KS", date="2026-07-05")
    ledger.record_payment(conn, amount_cents=500_000, source="camp", state_sourced="MO", date="2026-08-11")


def test_quarterly_nag_at_twentyone_days(conn):
    _income(conn)
    nags = nag.due_nags(conn, date(2026, 8, 25))
    assert len(nags) == 1
    text = nags[0].text
    assert "in 21 days" in text
    assert "$5,550" in text
    assert "KS $3,700" in text and "MO $1,850" in text
    assert "irs.gov/payments/direct-pay" in text
    assert "confirm with your EA" in text


def test_quarterly_nag_on_the_due_date(conn):
    _income(conn)
    assert "- today." in nag.due_nags(conn, date(2026, 9, 15))[0].text


def test_no_nag_on_a_quiet_day(conn):
    _income(conn)
    assert nag.due_nags(conn, date(2026, 9, 10)) == []


def test_a_nag_is_never_sent_twice(conn):
    _income(conn)
    first = nag.due_nags(conn, date(2026, 8, 25))
    for item in first:
        nag.mark_sent(conn, item.kind, item.key)
    assert nag.due_nags(conn, date(2026, 8, 25)) == []


def test_monthly_nag_only_on_the_first(conn):
    _income(conn)
    assert nag.monthly_nag(conn, date(2026, 9, 2)) is None
    monthly = nag.monthly_nag(conn, date(2026, 9, 1))
    assert monthly is not None
    assert "August closed out" in monthly.text
    assert "$5,000 in" in monthly.text


def test_monthly_nag_calls_out_a_month_with_no_receipts(conn):
    _income(conn)
    assert "leaving on the table" in nag.monthly_nag(conn, date(2026, 9, 1)).text


def test_monthly_nag_crossing_the_year_boundary(conn):
    ledger.record_payment(conn, amount_cents=100_000, source="a", state_sourced="MO", date="2026-12-10")
    monthly = nag.monthly_nag(conn, date(2027, 1, 1))
    assert "December closed out" in monthly.text
    assert "$1,000 in" in monthly.text


def test_the_reserve_being_short_is_flagged(conn):
    _income(conn)
    ledger.record_expense(
        conn, vendor="impulse", amount_cents=100_000, bucket="reserve", date="2026-08-20",
        category="Personal - not deductible",
    )
    assert "Heads up" in nag.quarterly_nags(conn, date(2026, 8, 25))[0].text


def test_run_marks_sent_only_when_the_send_succeeds(config):
    from moneybot import db

    conn = db.connect(config.db_path)
    db.init(conn, config.ratios)
    _income(conn)
    conn.close()

    attempts = []

    def failing(text):
        attempts.append(text)
        return False

    assert nag.run(config, failing, date(2026, 8, 25)) == []
    assert len(attempts) == 1
    # The failure is retried on the next tick rather than lost.
    sent = nag.run(config, lambda text: True, date(2026, 8, 25))
    assert len(sent) == 1
    assert nag.run(config, lambda text: True, date(2026, 8, 25)) == []
