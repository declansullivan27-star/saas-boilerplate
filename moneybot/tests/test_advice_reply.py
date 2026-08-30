from datetime import date

from moneybot import advice, ledger, reply


def test_days_left_in_month():
    assert advice.days_left_in_month(date(2026, 8, 30)) == 2
    assert advice.days_left_in_month(date(2026, 2, 1)) == 28


def test_month_bounds():
    assert advice.month_bounds(date(2026, 8, 30)) == ("2026-08-01", "2026-08-31")


def test_free_money_is_spendable_minus_bills(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="a", state_sourced="MO", date="2026-08-05")
    ledger.add_commitment(conn, name="rent", amount_cents=120_000, day_of_month=1)
    picture = advice.picture(conn, date(2026, 8, 30))
    assert picture.spendable_cents == 380_000
    assert picture.committed_cents == 120_000
    assert picture.free_cents == 260_000
    assert picture.per_day_cents == 260_000 // 30


def test_per_day_never_goes_negative(conn):
    ledger.add_commitment(conn, name="rent", amount_cents=120_000, day_of_month=1)
    picture = advice.picture(conn, date(2026, 8, 30))
    assert picture.free_cents < 0
    assert picture.per_day_cents == 0
    assert "Nothing free" in reply.spend_reply(picture)


def test_ordinals():
    assert [reply.ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22)] == [
        "1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd"
    ]


def test_every_reply_is_gsm_safe_ascii(conn):
    ledger.record_payment(conn, amount_cents=1_000_000, source="a", state_sourced="KS", date="2026-08-05")
    picture = advice.picture(conn, date(2026, 8, 30))
    for text in (
        reply.spend_reply(picture),
        reply.month_reply(picture, 21_450, date(2026, 8, 30)),
        reply.HELP,
        reply.WELCOME,
        reply.UNKNOWN,
    ):
        assert text.isascii(), text


def test_curly_punctuation_is_flattened():
    assert reply.ascii_safe("Personal — not deductible ‘x’") == "Personal - not deductible 'x'"


def test_clip_keeps_messages_inside_the_cap():
    assert len(reply.clip("x" * 900)) == 480
    assert reply.clip("short").endswith("short")
