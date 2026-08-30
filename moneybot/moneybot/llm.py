"""The two LLM jobs: receipt extraction and deal screening.

Both return structured JSON via the Messages API's structured outputs. Neither
is allowed to produce a number that lands in the ledger unchecked — the caller
in :mod:`moneybot.router` re-parses every amount with
:func:`moneybot.money.to_cents` and echoes it back for a one-word correction.

If there is no API key, or the API call fails, both jobs degrade to a
deterministic keyword classifier. Logging an expense must never depend on a
network call succeeding.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass

from .config import Config
from .money import MoneyError, to_cents
from .prompts import DEAL_SCHEMA, DEAL_SYSTEM, RECEIPT_SCHEMA, RECEIPT_SYSTEM

log = logging.getLogger("moneybot.llm")

# Deterministic fallback: (keywords, Schedule C category, deductible-by-default)
KEYWORD_RULES: tuple[tuple[tuple[str, ...], str, bool], ...] = (
    (("hotel", "marriott", "hilton", "hyatt", "motel", "airbnb", "inn"), "Travel", True),
    (("flight", "airline", "southwest", "delta", "united", "american air", "baggage"), "Travel", True),
    (("uber", "lyft", "taxi", "rental car", "hertz", "enterprise rent"), "Travel", True),
    (("gas", "shell", "bp ", "quiktrip", "casey's", "fuel", "mileage"), "Car and truck expenses", True),
    (("agent fee", "commission", "management fee"), "Commissions and fees", True),
    (("lawyer", "attorney", "legal", "cpa", "accountant", "ea fee", "tax prep"), "Legal and professional services", True),
    (("trainer", "training", "coach", "lesson", "camp fee", "gym", "recovery"), "Training and coaching", True),
    (("cleats", "shoes", "gear", "equipment", "pads", "glove", "bat", "helmet"), "Equipment", True),
    (("jersey", "uniform", "apparel print", "team gear"), "Uniforms and gear", True),
    (("phone", "verizon", "at&t", "t-mobile", "internet", "wifi"), "Utilities", True),
    (("photographer", "editor", "videographer", "content", "ad spend", "boost"), "Advertising", True),
    (("printer", "laptop", "ipad", "software", "subscription", "canva", "adobe"), "Office expense", True),
    (("bank fee", "wire fee", "stripe fee", "venmo fee", "atm"), "Bank and payment fees", True),
    (("irs", "estimated tax", "state tax", "quarterly payment"), "Taxes and licenses", False),
    (("groceries", "walmart", "target", "amazon", "netflix", "spotify", "steam", "nike"), "Personal — not deductible", False),
    (("dinner", "lunch", "restaurant", "chipotle", "starbucks", "coffee", "meal"), "Meals", False),
)


@dataclass
class ExpenseExtraction:
    vendor: str
    amount_cents: int | None
    date: str | None
    category: str
    deductible: bool
    reason: str
    confidence: str
    extracted_by: str  # "llm" or "keyword"


def keyword_extract(text: str, amount_cents: int | None = None, vendor: str | None = None) -> ExpenseExtraction:
    """The floor. Runs with no network, no key, no model."""
    lowered = (text or "").lower()
    for keywords, category, deductible in KEYWORD_RULES:
        if any(word in lowered for word in keywords):
            reason = (
                f"Matched '{category}' on a keyword. Confirm with your EA."
                if deductible
                else "Logged as personal unless you tell me otherwise."
            )
            return ExpenseExtraction(
                vendor=vendor or (text.strip()[:40] or "expense"),
                amount_cents=amount_cents,
                date=None,
                category=category,
                deductible=deductible,
                reason=reason,
                confidence="low",
                extracted_by="keyword",
            )
    return ExpenseExtraction(
        vendor=vendor or (text.strip()[:40] or "expense"),
        amount_cents=amount_cents,
        date=None,
        category="Uncategorized",
        deductible=False,
        reason="Couldn't tell what this was — reply CAT <category> to fix it.",
        confidence="low",
        extracted_by="keyword",
    )


class LLM:
    """Thin wrapper over the Messages API. Fails soft, always."""

    def __init__(self, config: Config):
        self.config = config
        self._client = None

    @property
    def available(self) -> bool:
        if not self.config.anthropic_api_key:
            return False
        return self._get_client() is not None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:  # pragma: no cover - depends on install
                log.warning("anthropic SDK not installed; falling back to keyword rules")
                return None
            self._client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        return self._client

    def _structured(self, *, system: str, content: list, schema: dict, effort: str, max_tokens: int) -> dict:
        client = self._get_client()
        if client is None:
            raise RuntimeError("no anthropic client")
        response = client.messages.create(
            model=self.config.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}],
            output_config={
                "effort": effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        )
        if getattr(response, "stop_reason", None) == "refusal":
            raise RuntimeError("model declined the request")
        text = next(block.text for block in response.content if block.type == "text")
        return json.loads(text)

    # --- job 1: receipts ---------------------------------------------------

    def extract_expense(
        self,
        *,
        text: str = "",
        image_bytes: bytes | None = None,
        media_type: str = "image/jpeg",
        fallback_amount_cents: int | None = None,
        fallback_vendor: str | None = None,
    ) -> ExpenseExtraction:
        if not self.available:
            return keyword_extract(text, fallback_amount_cents, fallback_vendor)

        content: list = []
        if image_bytes:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
                    },
                }
            )
        content.append(
            {
                "type": "text",
                "text": (
                    f"Receipt note from him: {text!r}\n"
                    "Extract the expense. If a photo is attached, the printed total on the photo wins."
                    if text
                    else "Extract the expense from this receipt photo."
                ),
            }
        )
        try:
            data = self._structured(
                system=RECEIPT_SYSTEM,
                content=content,
                schema=RECEIPT_SCHEMA,
                effort="low",
                max_tokens=2000,
            )
        except Exception as exc:  # network, refusal, malformed — all degrade the same way
            log.warning("receipt extraction fell back to keywords: %s", exc)
            return keyword_extract(text, fallback_amount_cents, fallback_vendor)

        try:
            amount_cents = to_cents(data["amount"])
        except (MoneyError, KeyError, TypeError):
            amount_cents = fallback_amount_cents
        # A model-read total that is wildly out of range is treated as unread.
        if amount_cents is not None and not (0 < amount_cents <= 5_000_000):
            log.warning("discarding out-of-range extracted amount: %s", amount_cents)
            amount_cents = fallback_amount_cents
        return ExpenseExtraction(
            vendor=(data.get("vendor") or fallback_vendor or "expense")[:60],
            amount_cents=amount_cents,
            date=data.get("date"),
            category=data.get("category") or "Uncategorized",
            deductible=bool(data.get("deductible")),
            reason=(data.get("reason") or "")[:160],
            confidence=data.get("confidence") or "low",
            extracted_by="llm",
        )

    # --- job 2: deal screening --------------------------------------------

    def screen_deal(self, contract_text: str) -> dict | None:
        if not self.available:
            return None
        try:
            return self._structured(
                system=DEAL_SYSTEM,
                content=[{"type": "text", "text": contract_text[:400_000]}],
                schema=DEAL_SCHEMA,
                effort="high",
                max_tokens=8000,
            )
        except Exception as exc:
            log.warning("deal screen failed: %s", exc)
            return None
