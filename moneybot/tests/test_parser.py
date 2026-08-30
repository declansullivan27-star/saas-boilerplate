from datetime import date

import pytest

from moneybot.parser import parse

TODAY = date(2026, 8, 30)


def p(text):
    return parse(text, today=TODAY, default_state="MO")


@pytest.mark.parametrize(
    "text",
    [
        "got 10000 from the booster collective",
        "+10,000 collective",
        "received 2500 for a camp",
        "the collective deposited 4000",
        "paid me 2500 for an autograph signing",
    ],
)
def test_money_in_is_read_as_income(text):
    assert p(text).intent == "income"


@pytest.mark.parametrize(
    "text",
    [
        "spent 42.18 on gas",
        "paid 214.50 for the hotel",
        "bought cleats 129.99",
        "-42.18 gas",
        "Marriott Dallas 214.50 camp appearance",
    ],
)
def test_money_out_is_read_as_an_expense(text):
    assert p(text).intent == "expense"


def test_a_bare_vendor_and_amount_is_flagged_low_confidence():
    parsed = p("Marriott Dallas 214.50 camp appearance")
    assert parsed.confidence == "low"
    assert parsed.amount_cents == 21_450
    assert "Marriott" in parsed.label


def test_paid_me_beats_paid():
    assert p("the collective paid me 5000").intent == "income"


def test_state_is_tagged_at_intake():
    assert p("got 10000 from the collective in KS").state == "KS"
    assert p("got 10000 from a camp in Missouri").state == "MO"
    assert p("spent 40 on gas in lawrence").state == "KS"
    assert p("got 10000 from the collective").state == "MO"  # falls back to home state


def test_the_state_token_does_not_leak_into_the_label():
    assert p("got 10000 from the booster collective in KS").label == "booster collective"


def test_source_type_is_classified():
    assert p("got 10000 from the booster collective").source_type == "collective"
    assert p("got 5000 for an autograph signing").source_type == "autograph"
    assert p("got 800 from a youth camp").source_type == "camp"
    assert p("got 20000 for a brand sponsorship").source_type == "nil_brand"


def test_dates_are_understood():
    assert p("spent 40 on gas yesterday").date == "2026-08-29"
    assert p("spent 40 on gas 8/12").date == "2026-08-12"
    assert p("spent 40 on gas 8/12/25").date == "2025-08-12"


@pytest.mark.parametrize(
    "text,intent",
    [
        ("?", "spend"), ("balance", "spend"), ("SPEND", "spend"), ("bal", "spend"),
        ("help", "help"), ("start", "start"), ("tax", "quarter"), ("month", "month"),
        ("export", "export"), ("undo", "undo"), ("bills", "bills"), ("deductions", "deductions"),
        ("/set savings 20", "set"), ("cat Travel", "recat"), ("deal", "deal"),
    ],
)
def test_commands(text, intent):
    assert p(text).intent == intent


def test_slash_prefix_is_optional():
    assert p("/balance").intent == p("balance").intent


def test_recurring_bills():
    parsed = p("rent 1200 monthly on the 1st")
    assert parsed.intent == "bill_add"
    assert parsed.amount_cents == 120_000
    assert parsed.day_of_month == 1
    assert parsed.label == "rent"
    assert p("phone 85 a month").intent == "bill_add"


def test_starting_balance():
    parsed = p("i have 4200 in checking")
    assert parsed.intent == "have"
    assert parsed.amount_cents == 420_000
    assert parsed.already_taxed is False
    assert p("i have 4200 in checking, already taxed").already_taxed is True


def test_swing_spending_is_routed_to_the_swing_bucket():
    parsed = p("swing 200 concert tickets")
    assert parsed.intent == "expense"
    assert parsed.text == "swing"


def test_nonsense_is_not_guessed_at():
    assert p("how's it going").intent == "unknown"
    assert p("").intent == "unknown"
