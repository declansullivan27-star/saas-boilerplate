"""The line between what the model may do and what only code may do.

Enforced twice: in the system prompt (see :mod:`moneybot.prompts`) and here,
in code, on every inbound request and every outbound model-written sentence.
The prompt is a request; this module is the enforcement.
"""

from __future__ import annotations

import re

from .config import ESTIMATE_DISCLAIMER

MONEY_IN_TEXT = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)")

# Outbound: sentences a money bot must never send.
PROHIBITED_OUTPUT = (
    (re.compile(r"\byou (?:should|ought to|need to|can) (?:buy|invest|purchase|put money)", re.I),
     "investment recommendation"),
    (re.compile(r"\b(?:invest|allocate) (?:in|into) (?:an? )?(?:etf|index fund|stock|crypto|bitcoin|roth|ira|401)", re.I),
     "investment recommendation"),
    (re.compile(r"\byou (?:owe|will owe|don't owe|do not owe) \$", re.I), "tax advice"),
    (re.compile(r"\b(?:this|that) (?:is|would be) (?:fully )?(?:deductible|tax[- ]free|non-?taxable)\b(?! per)", re.I),
     "tax determination stated as fact"),
    (re.compile(r"\byou (?:don't|do not) (?:have to|need to) (?:pay|file|report)\b", re.I), "tax advice"),
    (re.compile(r"\b(?:i|i'?ll|we) (?:have )?(?:transferred|moved|sent|paid|wired)\b", re.I),
     "claims to have moved money"),
    (re.compile(r"\b(?:this deal|the deal|it) (?:is|looks) (?:fine|good|great|fair|safe)\b", re.I),
     "endorses a deal"),
    (re.compile(r"\byou should sign\b", re.I), "endorses a deal"),
)

# Inbound: questions the bot declines, with the line it sends instead.
INBOUND_REFUSALS = (
    (re.compile(r"\b(should i|can i|do i|would you) (invest|buy stock|buy crypto|put .* in the market)", re.I),
     "I don't do investments — not what I'm for. I track what's yours and what's the IRS's. "
     "Investment questions go to a fiduciary advisor, not me."),
    (re.compile(r"\b(how much (tax|taxes) do i owe|what do i owe the irs|is this deductible for sure|"
                r"will i get audited|can i write off my (car|house|rent) entirely)\b", re.I),
     "I can't answer that one — it's tax advice and I'm not qualified. I can tell you what you've set "
     "aside and what you've logged. Everything else is your EA's call. Text TAX for your reserve."),
    (re.compile(r"\b(transfer|move|send|wire|pay) .*(to my|from my)? ?(bank|account|venmo|cash app|zelle)\b", re.I),
     "I never move money — I only keep the books. I'll tell you the number to move and you do it yourself."),
)

DISCLAIMER_TRIGGERS = re.compile(r"\b(estimate|estimated|quarterly|reserve|owe|deduct|deductible|write[- ]off)\b", re.I)


def check_inbound(text: str) -> str | None:
    """If the inbound text asks for something out of bounds, return the reply to send."""
    for pattern, reply in INBOUND_REFUSALS:
        if pattern.search(text or ""):
            return reply
    return None


def amounts_in(text: str) -> list[int]:
    """Every dollar figure in a block of text, as integer cents."""
    out = []
    for match in MONEY_IN_TEXT.finditer(text or ""):
        raw = match.group(1).replace(",", "")
        if "." in raw:
            dollars, _, frac = raw.partition(".")
            out.append(int(dollars) * 100 + int(frac.ljust(2, "0")[:2]))
        else:
            out.append(int(raw) * 100)
    return out


def unverified_amounts(text: str, allowed_cents: set[int]) -> list[int]:
    """Dollar figures in model-written prose that the ledger cannot vouch for."""
    return [cents for cents in amounts_in(text) if cents not in allowed_cents]


def prohibited_in(text: str) -> list[str]:
    return [reason for pattern, reason in PROHIBITED_OUTPUT if pattern.search(text or "")]


def with_disclaimer(text: str) -> str:
    """Append the estimate label to anything that talks about tax figures."""
    if DISCLAIMER_TRIGGERS.search(text or "") and ESTIMATE_DISCLAIMER.lower() not in (text or "").lower():
        return f"{text}\n{ESTIMATE_DISCLAIMER}"
    return text


def vet_llm_text(text: str, allowed_cents: set[int], *, fallback: str) -> tuple[str, list[str]]:
    """Gate for every model-written sentence that reaches his phone.

    Returns ``(text_to_send, violations)``. If the model asserted a dollar
    figure the ledger cannot confirm, or crossed a guardrail, the model's text
    is dropped entirely and ``fallback`` (written by code) is sent instead.
    """
    violations = prohibited_in(text)
    stray = unverified_amounts(text, allowed_cents)
    if stray:
        violations.append(
            "unverified amounts: " + ", ".join(f"${c / 100:,.2f}" for c in stray)
        )
    if violations:
        return fallback, violations
    return with_disclaimer(text), []
