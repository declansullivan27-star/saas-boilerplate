import pytest

from moneybot import guardrails
from moneybot.config import ESTIMATE_DISCLAIMER


@pytest.mark.parametrize(
    "text",
    [
        "should i invest in bitcoin",
        "how much tax do i owe",
        "can i write off my car entirely",
        "transfer 500 to my bank account",
    ],
)
def test_out_of_bounds_questions_get_a_canned_answer(text):
    assert guardrails.check_inbound(text)


def test_ordinary_messages_pass_through():
    assert guardrails.check_inbound("spent 42 on gas") is None
    assert guardrails.check_inbound("?") is None


def test_amounts_are_read_out_of_prose():
    assert guardrails.amounts_in("You have $3,700 and $214.50 left") == [370_000, 21_450]
    assert guardrails.amounts_in("no money here") == []


def test_a_figure_the_ledger_cannot_confirm_is_caught():
    assert guardrails.unverified_amounts("You have $3,700", {370_000}) == []
    assert guardrails.unverified_amounts("You have $9,999", {370_000}) == [999_900]


@pytest.mark.parametrize(
    "text",
    [
        "You should invest in an index fund.",
        "You owe $4,000 to the IRS.",
        "You don't have to file this year.",
        "I transferred $200 to your savings.",
        "This deal is fine.",
        "You should sign it.",
    ],
)
def test_prohibited_sentences_are_detected(text):
    assert guardrails.prohibited_in(text)


def test_vet_replaces_bad_output_with_the_code_written_fallback():
    out, violations = guardrails.vet_llm_text(
        "You owe $4,000 and should invest the rest.", {370_000}, fallback="SAFE"
    )
    assert out == "SAFE"
    assert len(violations) >= 2


def test_vet_lets_good_output_through_and_labels_the_estimate():
    out, violations = guardrails.vet_llm_text(
        "Travel, likely deductible for a camp appearance.", {21_450}, fallback="SAFE"
    )
    assert violations == []
    assert ESTIMATE_DISCLAIMER in out


def test_the_disclaimer_is_not_doubled_up():
    text = f"Quarterly reserve. {ESTIMATE_DISCLAIMER}"
    assert guardrails.with_disclaimer(text).count("confirm with your EA") == 1
