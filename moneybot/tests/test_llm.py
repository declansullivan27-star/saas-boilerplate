import pytest

from moneybot.config import Config
from moneybot.llm import LLM, keyword_extract


@pytest.mark.parametrize(
    "text,category,deductible",
    [
        ("Marriott Dallas camp appearance", "Travel", True),
        ("spent 42 on gas", "Car and truck expenses", True),
        ("agent fee for the collective deal", "Commissions and fees", True),
        ("new cleats", "Equipment", True),
        ("groceries at walmart", "Personal - not deductible", False),
        ("paid 3700 estimated tax", "Taxes and licenses", False),
    ],
)
def test_the_keyword_floor_classifies_without_a_model(text, category, deductible):
    result = keyword_extract(text, 1000)
    assert result.category.replace("—", "-") == category
    assert result.deductible is deductible
    assert result.extracted_by == "keyword"


def test_unknown_text_is_left_uncategorized():
    result = keyword_extract("zzz qqq", 1000)
    assert result.category == "Uncategorized"
    assert result.deductible is False
    assert "CAT" in result.reason


def test_no_api_key_means_the_model_is_never_called():
    assert LLM(Config(anthropic_api_key="")).available is False


def test_extraction_falls_back_to_keywords_with_no_key():
    llm = LLM(Config(anthropic_api_key=""))
    result = llm.extract_expense(text="Marriott Dallas", fallback_amount_cents=21_450)
    assert result.extracted_by == "keyword"
    assert result.amount_cents == 21_450


def test_deal_screening_returns_nothing_rather_than_guessing():
    assert LLM(Config(anthropic_api_key="")).screen_deal("a contract") is None


class _Boom:
    class messages:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("network is down")


def test_an_api_failure_still_logs_the_expense(monkeypatch):
    llm = LLM(Config(anthropic_api_key="sk-test"))
    monkeypatch.setattr(llm, "_get_client", lambda: _Boom())
    monkeypatch.setattr(type(llm), "available", property(lambda self: True))
    result = llm.extract_expense(text="spent 42 on gas", fallback_amount_cents=4_200)
    assert result.extracted_by == "keyword"
    assert result.amount_cents == 4_200


class _Fake:
    def __init__(self, payload):
        self.payload = payload
        self.messages = self

    def create(self, **kwargs):
        import json
        from types import SimpleNamespace

        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def _llm_with(monkeypatch, payload):
    llm = LLM(Config(anthropic_api_key="sk-test"))
    monkeypatch.setattr(llm, "_get_client", lambda: _Fake(payload))
    monkeypatch.setattr(type(llm), "available", property(lambda self: True))
    return llm


PAYLOAD = {
    "vendor": "Marriott Dallas", "amount": "214.50", "date": "2026-08-20",
    "category": "Travel", "deductible": True, "reason": "Hotel for a camp appearance.",
    "confidence": "high",
}


def test_a_structured_extraction_is_parsed(monkeypatch):
    result = _llm_with(monkeypatch, PAYLOAD).extract_expense(image_bytes=b"jpeg")
    assert result.vendor == "Marriott Dallas"
    assert result.amount_cents == 21_450
    assert result.date == "2026-08-20"
    assert result.extracted_by == "llm"


def test_an_absurd_extracted_amount_is_discarded(monkeypatch):
    llm = _llm_with(monkeypatch, {**PAYLOAD, "amount": "99999999"})
    result = llm.extract_expense(image_bytes=b"jpeg", fallback_amount_cents=21_450)
    assert result.amount_cents == 21_450


def test_an_unparseable_extracted_amount_falls_back(monkeypatch):
    llm = _llm_with(monkeypatch, {**PAYLOAD, "amount": "about twenty bucks"})
    result = llm.extract_expense(image_bytes=b"jpeg", fallback_amount_cents=2_000)
    assert result.amount_cents == 2_000


def test_a_refusal_degrades_to_keywords(monkeypatch):
    from types import SimpleNamespace

    class _Refuses:
        def __init__(self):
            self.messages = self

        def create(self, **kwargs):
            return SimpleNamespace(stop_reason="refusal", content=[], stop_details=None)

    llm = LLM(Config(anthropic_api_key="sk-test"))
    monkeypatch.setattr(llm, "_get_client", lambda: _Refuses())
    monkeypatch.setattr(type(llm), "available", property(lambda self: True))
    result = llm.extract_expense(text="hotel in dallas", fallback_amount_cents=100)
    assert result.extracted_by == "keyword"
