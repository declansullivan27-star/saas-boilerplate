from datetime import date

import pytest

from moneybot import ledger
from moneybot.llm import ExpenseExtraction
from moneybot.router import Inbound, Media, Router

TODAY = date(2026, 8, 30)


class StubLLM:
    """Stands in for the model so the tests never touch the network."""

    def __init__(self, extraction=None, screen=None):
        self.extraction = extraction
        self.screen = screen
        self.calls = []

    available = True

    def extract_expense(self, **kwargs):
        self.calls.append(kwargs)
        return self.extraction

    def screen_deal(self, text):
        self.calls.append({"deal": text})
        return self.screen


def test_the_split_reply_is_the_headline(bot):
    out = bot("got 10000 from the booster collective in KS")
    assert "$10,000 in from booster collective (KS)" in out
    assert "$3,700 to tax" in out
    assert "$1,500 to savings" in out
    assert "$1,000 to swing" in out
    assert "$3,800 yours" in out


def test_what_can_i_spend_right_now(bot):
    bot("got 10000 from the collective")
    bot("rent 1200 monthly on the 1st")
    out = bot("?")
    assert "Spendable: $3,800" in out
    assert "$1,200 of bills" in out
    assert "$2,600 free" in out
    assert "Tax reserve $3,700 - not yours" in out


def test_swing_is_reported_and_never_commented_on(bot):
    bot("got 10000 from the collective")
    out = bot("?")
    assert "Swing: $1,000 - yours, no questions." in out
    spend = bot("swing 200 concert tickets")
    assert "Out of swing" in spend
    assert "$800 left there" in spend


def test_an_expense_comes_out_of_spendable(bot):
    bot("got 10000 from the collective")
    out = bot("spent 42.18 on gas")
    assert "$42.18" in out
    assert "Spendable now $3,757.82" in out


def test_a_bare_vendor_line_is_logged_with_a_correction_offer(bot):
    bot("got 10000 from the collective")
    out = bot("Marriott Dallas 214.50 camp appearance")
    assert "Read that as money OUT" in out
    assert "Reply UNDO" in out


def test_undo_puts_the_money_back(bot):
    bot("got 10000 from the collective")
    bot("spent 42.18 on gas")
    out = bot("undo")
    assert "Removed that expense" in out
    assert "$3,800" in out


def test_a_tax_payment_draws_down_the_reserve_not_spending(bot):
    bot("got 10000 from the collective")
    bot("paid 3700 estimated tax")
    conn = bot.router.connect()
    try:
        assert ledger.bucket_balance(conn, "reserve") == 0
        assert ledger.bucket_balance(conn, "spending") == 380_000
    finally:
        conn.close()


def test_starting_balance_is_split_and_reversible(bot):
    out = bot("i have 4200 in checking")
    assert "$1,554 tax" in out
    assert "HAVE 4200 TAXED" in out
    taxed = bot("have 4200 taxed")
    assert "already taxed" in taxed


def test_bills_change_what_is_free(bot):
    bot("got 10000 from the collective")
    assert "$3,800 free" not in bot("bills")
    out = bot("rent 1200 monthly on the 1st")
    assert "$2,600 free" in out
    listing = bot("bills")
    assert "rent $1,200 on the 1st" in listing
    assert "Stopped tracking rent" in bot("bill remove rent")


def test_quarterly_status_shows_the_state_split(bot):
    bot("got 10000 from the collective in KS")
    bot("got 5000 from a camp in Missouri")
    out = bot("tax")
    assert "2026-Q3" in out
    assert "KS $3,700" in out and "MO $1,850" in out
    assert "irs.gov" in out
    assert "confirm with your EA" in out


def test_month_summary(bot):
    bot("got 10000 from the collective")
    bot("spent 42.18 on gas")
    out = bot("month")
    assert "August: $10,000 in, $42.18 out" in out
    assert "Deductions logged this month: $42.18" in out


def test_settings_can_be_changed_by_text(bot):
    assert "savings is now 20%" in bot("set savings 20")
    out = bot("got 10000 from the collective")
    assert "$2,000 to savings" in out
    assert "Home state set to KS" in bot("set state KS")
    assert bot("got 1000 from a camp").count("(KS)") == 1


def test_settings_refuse_an_impossible_split(bot):
    assert "nothing spendable" in bot("set savings 70")


def test_move_is_bookkeeping_only(bot):
    bot("got 10000 from the collective")
    out = bot("move 200 swing to spending")
    assert "bookkeeping only" in out
    assert "Swing $800" in out


def test_export_reports_the_year(bot):
    bot("got 10000 from the collective")
    out = bot("export")
    assert "2026: $10,000 income" in out


def test_export_links_are_given_when_a_public_url_is_configured(config):
    config.public_base_url = "https://bot.example.com"
    router = Router(config)
    router.handle(Inbound(channel="t", party="p", text="got 10000 from the collective", today=TODAY))
    out = router.handle(Inbound(channel="t", party="p", text="export", today=TODAY))
    assert "https://bot.example.com/export/" in out
    assert "summary-2026.csv" in out


def test_out_of_bounds_questions_never_reach_the_ledger(bot):
    assert "fiduciary advisor" in bot("should i invest in bitcoin")
    assert "not qualified" in bot("how much tax do i owe")
    assert "never move money" in bot("transfer 500 to my bank account")


def test_only_the_owner_is_answered(bot):
    bot("got 10000 from the collective", party="+15550001111")
    out = bot("?", party="+15559999999")
    assert "not them" in out


def test_an_allowlist_locks_it_down(config):
    config.allowed_senders = ("+15550001111",)
    router = Router(config)
    assert "not them" in router.handle(Inbound(channel="t", party="+1555000222", text="?"))
    assert "Spendable" in router.handle(Inbound(channel="t", party="+15550001111", text="?"))


def test_unknown_text_gets_a_nudge_not_a_guess(bot):
    out = bot("how's it going")
    assert "Didn't catch that" in out


def test_replies_stay_inside_one_sms_burst(bot):
    bot("got 10000 from the collective in KS")
    bot("rent 1200 monthly on the 1st")
    for message in ("?", "month", "spent 42 on gas", "got 5000 from a camp"):
        out = bot(message)
        assert len(out) <= 480, message
        assert out.isascii(), message


# --- receipts ------------------------------------------------------------

def _photo():
    return Media(data=b"\xff\xd8\xff-not-a-real-jpeg", media_type="image/jpeg")


def test_a_receipt_photo_is_extracted_and_stored(config):
    stub = StubLLM(
        ExpenseExtraction(
            vendor="Marriott Dallas", amount_cents=21_450, date="2026-08-20", category="Travel",
            deductible=True, reason="Hotel for a camp appearance.", confidence="high",
            extracted_by="llm",
        )
    )
    router = Router(config, llm=stub)
    out = router.handle(
        Inbound(channel="sms", party="p", text="camp appearance", media=[_photo()], today=TODAY)
    )
    assert "Marriott Dallas $214.50 - Travel, likely deductible" in out
    conn = router.connect()
    try:
        row = conn.execute("SELECT * FROM expenses").fetchone()
        assert row["receipt_url"] and row["extracted_by"] == "llm"
        assert row["date"] == "2026-08-20"
    finally:
        conn.close()


def test_an_unreadable_receipt_asks_for_the_number(config):
    stub = StubLLM(
        ExpenseExtraction(
            vendor="?", amount_cents=None, date=None, category="Uncategorized", deductible=False,
            reason="", confidence="low", extracted_by="llm",
        )
    )
    router = Router(config, llm=stub)
    out = router.handle(Inbound(channel="sms", party="p", text="", media=[_photo()], today=TODAY))
    assert "couldn't read a total" in out
    conn = router.connect()
    try:
        assert conn.execute("SELECT COUNT(*) AS c FROM expenses").fetchone()["c"] == 0
    finally:
        conn.close()


def test_the_model_may_not_change_the_amount_he_typed(config):
    """He texts 42.18; the model claims 9999.99. The ledger keeps his number."""
    stub = StubLLM(
        ExpenseExtraction(
            vendor="Shell", amount_cents=999_999, date=None, category="Car and truck expenses",
            deductible=True, reason="Fuel.", confidence="high", extracted_by="llm",
        )
    )
    router = Router(config, llm=stub)
    router.handle(Inbound(channel="sms", party="p", text="spent 42.18 on gas", today=TODAY))
    conn = router.connect()
    try:
        assert conn.execute("SELECT amount_cents FROM expenses").fetchone()[0] == 4_218
    finally:
        conn.close()


def test_model_prose_with_an_invented_figure_is_dropped(config):
    stub = StubLLM(
        ExpenseExtraction(
            vendor="Shell", amount_cents=4_218, date=None, category="Car and truck expenses",
            deductible=True, reason="You owe $4,000 in tax on this.", confidence="high",
            extracted_by="llm",
        )
    )
    router = Router(config, llm=stub)
    out = router.handle(Inbound(channel="sms", party="p", text="spent 42.18 on gas", today=TODAY))
    assert "$4,000" not in out
    conn = router.connect()
    try:
        assert conn.execute("SELECT reason FROM expenses").fetchone()[0] == ""
    finally:
        conn.close()


def test_recategorizing_the_last_expense(bot):
    bot("got 10000 from the collective")
    bot("spent 42.18 on gas")
    out = bot("cat Personal - not deductible")
    assert "not deductible" in out


# --- deal screening ------------------------------------------------------

SCREEN = {
    "counterparty": "Sunflower Collective",
    "deal_type": "collective",
    "term": "24 months",
    "exclusivity": "All beverage brands",
    "nil_rights_after_term": "Perpetual license to existing footage",
    "auto_renewal": "Renews unless cancelled 60 days out",
    "agent_fee_pct": 20,
    "flags": ["One-way termination right"],
    "questions": ["Q1?", "Q2?", "Q3?", "Q4?"],
}


def test_a_short_message_gets_instructions_not_a_screen(bot):
    out = bot("deal")
    assert "Forward me the contract" in out


def test_the_deal_screen_benchmarks_the_fee_in_code(config):
    router = Router(config, llm=StubLLM(screen=SCREEN))
    out = router.handle(
        Inbound(channel="sms", party="p", text="deal " + ("contract text " * 40), today=TODAY)
    )
    assert "Term: 24 months" in out
    assert "Perpetual license" in out
    assert "Fee: 20%. Typical for collective money is 3-5%. This is above that range." in out
    assert "Four questions before you sign:" in out
    assert "not telling you this deal is fine" in out


def test_the_deal_is_saved(config):
    router = Router(config, llm=StubLLM(screen=SCREEN))
    router.handle(Inbound(channel="sms", party="p", text="deal " + ("x " * 200), today=TODAY))
    conn = router.connect()
    try:
        row = conn.execute("SELECT * FROM deals").fetchone()
        assert row["counterparty"] == "Sunflower Collective"
        assert row["fee_pct"] == 20
    finally:
        conn.close()


def test_a_failed_screen_says_so_rather_than_guessing(config):
    router = Router(config, llm=StubLLM(screen=None))
    out = router.handle(Inbound(channel="sms", party="p", text="deal " + ("x " * 200), today=TODAY))
    assert "Don't sign anything today" in out


@pytest.mark.parametrize("message", ["", "   ", "\n"])
def test_empty_messages_do_not_crash(bot, message):
    assert bot(message)
