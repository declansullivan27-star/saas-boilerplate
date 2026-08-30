"""Deterministic intent parsing for free-text SMS.

Regex first, model second. Anything that decides an amount, a direction
(money in vs money out) or a bucket is resolved here in code; the model is
only ever asked to categorize and explain what code already parsed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from .money import MoneyError, to_cents

AMOUNT_RE = re.compile(r"(?<![\w.])(-|\+)?\$?\s?(\d[\d,]*(?:\.\d{1,2})?)\s?(k\b)?", re.I)

INCOME_WORDS = (
    "got", "received", "receive", "deposit", "deposited", "earned", "income",
    "check for", "check from", "cashed", "payout", "paid me", "sent me", "wired",
    "hit my account", "came in",
)
EXPENSE_WORDS = (
    "spent", "bought", "paid for", "paid", "cost", "charge", "charged", "bill for",
    "gas", "dinner", "lunch", "hotel", "flight", "uber", "lyft", "meal",
)
HAVE_WORDS = ("i have", "have about", "in checking", "in the bank", "bank balance", "starting with")

SOURCE_TYPES = {
    "collective": ("collective", "booster", "nil collective"),
    "nil_brand": ("brand", "nil deal", "sponsor", "sponsorship", "endorsement", "ad deal"),
    "appearance": ("appearance", "speaking", "event"),
    "autograph": ("autograph", "signing", "memorabilia"),
    "camp": ("camp", "clinic", "lesson"),
    "royalty": ("royalty", "royalties", "jersey", "merch"),
}

STATE_PATTERNS = {
    "KS": (r"\bks\b", r"\bkansas\b", r"\blawrence\b", r"\boverland park\b", r"\btopeka\b", r"\bwichita\b"),
    "MO": (r"\bmo\b", r"\bmissouri\b", r"\bcolumbia\b", r"\bst\.? louis\b", r"\bspringfield mo\b"),
}

# Commands map to a canonical intent. Both "/bal" and "bal" work — nobody
# types a slash on a phone keyboard.
COMMANDS = {
    "start": "start", "help": "help", "?": "spend", "h": "help",
    "spend": "spend", "spendable": "spend", "balance": "spend", "bal": "spend",
    "status": "spend", "cash": "spend",
    "month": "month", "monthly": "month", "summary": "month",
    "tax": "quarter", "taxes": "quarter", "quarter": "quarter", "q": "quarter",
    "export": "export", "csv": "export",
    "undo": "undo", "oops": "undo",
    "bills": "bills", "bill": "bills", "recurring": "bills",
    "cat": "recat", "category": "recat",
    "deal": "deal", "contract": "deal",
    "swing": "swing",
    "set": "set", "settings": "set", "config": "set",
    "move": "move",
    "have": "have",
    "deductions": "deductions", "writeoffs": "deductions",
}

INTENTS = (
    "start", "help", "spend", "month", "quarter", "export", "undo", "bills", "bill_add",
    "deal", "swing", "set", "move", "have", "deductions", "recat", "income", "expense", "unknown",
)


@dataclass
class Parsed:
    intent: str
    amount_cents: int | None = None
    text: str = ""
    label: str = ""
    source_type: str = "other"
    state: str | None = None
    date: str | None = None
    day_of_month: int | None = None
    already_taxed: bool = False
    args: list[str] = field(default_factory=list)
    raw: str = ""
    confidence: str = "high"


def _find_amount(text: str) -> tuple[int | None, tuple[int, int] | None, bool]:
    """Return (cents, span, negative_sign). Skips things that are clearly not money."""
    for match in AMOUNT_RE.finditer(text):
        sign, digits, kilo = match.group(1), match.group(2), match.group(3)
        # A bare small integer immediately followed by '%' or ':' is not money.
        tail = text[match.end():match.end() + 1]
        if tail in ("%", ":"):
            continue
        raw = digits + ("k" if kilo else "")
        try:
            cents = to_cents(raw)
        except MoneyError:  # pragma: no cover - AMOUNT_RE already constrains this
            continue
        if cents == 0:
            continue
        return cents, match.span(), sign == "-"
    return None, None, False


def _detect_state(text: str) -> str | None:
    lowered = text.lower()
    for state, patterns in STATE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, lowered):
                return state
    return None


def _detect_source_type(text: str) -> str:
    lowered = text.lower()
    for source_type, words in SOURCE_TYPES.items():
        if any(word in lowered for word in words):
            return source_type
    return "other"


def _detect_date(text: str, today: date) -> str | None:
    lowered = text.lower()
    if "yesterday" in lowered:
        return (today - timedelta(days=1)).isoformat()
    if "today" in lowered:
        return today.isoformat()
    match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
    if match:
        month, day, year = int(match.group(1)), int(match.group(2)), match.group(3)
        if 1 <= month <= 12 and 1 <= day <= 31:
            if year is None:
                resolved = today.year
            else:
                resolved = int(year) + 2000 if len(year) == 2 else int(year)
            try:
                return date(resolved, month, day).isoformat()
            except ValueError:
                return None
    return None


def _clean_label(text: str, span: tuple[int, int] | None) -> str:
    if span:
        text = text[: span[0]] + " " + text[span[1] :]
    text = re.sub(
        r"\b(got|received|receive|deposited|deposit|earned|spent|bought|paid|for|from|at|to|on|"
        r"i|me|my|the|a|an|just|and|in|of|dollars?|bucks?|yesterday|today)\b",
        " ",
        text,
        flags=re.I,
    )
    text = re.sub(r"\b(ks|kansas|mo|missouri)\b", " ", text, flags=re.I)
    text = re.sub(r"[^\w\s&'./-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _starts_with_command(lowered: str) -> tuple[str, str] | None:
    stripped = lowered.lstrip("/").strip()
    if not stripped:
        return None
    head, _, rest = stripped.partition(" ")
    if head not in COMMANDS:
        head = head.strip(".,!")
    if head in COMMANDS:
        return COMMANDS[head], rest.strip()
    return None


def parse(message: str, *, today: date | None = None, default_state: str = "MO") -> Parsed:
    """Turn one inbound text into a structured intent."""
    today = today or date.today()
    raw = (message or "").strip()
    if not raw:
        return Parsed(intent="unknown", raw=raw)
    lowered = raw.lower()

    command = _starts_with_command(lowered)
    if command:
        intent, rest = command
        parsed = _parse_command(intent, rest, raw, today, default_state)
        if parsed is not None:
            return parsed

    amount, span, negative = _find_amount(raw)
    state = _detect_state(raw) or None
    when = _detect_date(raw, today)

    # "rent 1200 monthly" / "1200 a month for rent" -> a recurring commitment
    if amount and re.search(r"\b(each|every|per|a)\s+month\b|\bmonthly\b|/mo\b|\bmo\.?\b(?!\w)", lowered) \
            and not any(word in lowered for word in INCOME_WORDS):
        day_match = re.search(r"\bon the (\d{1,2})(?:st|nd|rd|th)?\b", lowered)
        stripped_raw = re.sub(r"on the \d{1,2}(?:st|nd|rd|th)?", " ", raw, flags=re.I)
        stripped_raw = re.sub(r"monthly|each month|every month|per month|a month|/mo", " ", stripped_raw, flags=re.I)
        return Parsed(
            intent="bill_add",
            amount_cents=amount,
            label=_clean_label(stripped_raw, span) or "bill",
            day_of_month=int(day_match.group(1)) if day_match else 1,
            raw=raw,
        )

    if any(word in lowered for word in HAVE_WORDS) and amount:
        return Parsed(
            intent="have",
            amount_cents=amount,
            label="cash on hand",
            already_taxed=bool(re.search(r"\btaxed\b|after tax|post.?tax", lowered)),
            state=state,
            raw=raw,
        )

    if amount is not None:
        income_hit = any(word in lowered for word in INCOME_WORDS) or raw.lstrip().startswith("+")
        expense_hit = negative or any(word in lowered for word in EXPENSE_WORDS)
        # "paid me" is income even though "paid" is an expense word.
        if "paid me" in lowered or "paid out to me" in lowered:
            income_hit, expense_hit = True, False
        if income_hit and not expense_hit:
            return Parsed(
                intent="income",
                amount_cents=amount,
                label=_clean_label(raw, span) or "payment",
                source_type=_detect_source_type(raw),
                state=state or default_state,
                date=when,
                raw=raw,
            )
        if expense_hit:
            return Parsed(
                intent="expense",
                amount_cents=amount,
                label=_clean_label(raw, span) or "expense",
                state=state,
                date=when,
                raw=raw,
            )
        # A vendor and an amount with no verb: "Marriott Dallas 214.50 camp appearance".
        return Parsed(
            intent="expense",
            amount_cents=amount,
            label=_clean_label(raw, span) or "expense",
            state=state,
            date=when,
            raw=raw,
            confidence="low",
        )

    return Parsed(intent="unknown", raw=raw, text=raw)


def _parse_command(intent: str, rest: str, raw: str, today: date, default_state: str) -> Parsed | None:
    amount, span, _ = _find_amount(rest)
    if intent == "have":
        if amount is None:
            return Parsed(intent="unknown", raw=raw, text=raw)
        return Parsed(
            intent="have",
            amount_cents=amount,
            label="cash on hand",
            already_taxed=bool(re.search(r"\btaxed\b|after tax|post.?tax", rest, re.I)),
            raw=raw,
        )
    if intent in ("set", "move", "deal", "export", "bills"):
        return Parsed(intent=intent, args=rest.split(), text=rest, amount_cents=amount, raw=raw)
    if intent == "swing" and amount is not None:
        # "swing 200 concert tickets" spends out of the swing bucket
        return Parsed(
            intent="expense",
            amount_cents=amount,
            label=_clean_label(rest, span) or "swing",
            text="swing",
            date=_detect_date(rest, today),
            raw=raw,
        )
    return Parsed(intent=intent, text=rest, args=rest.split(), raw=raw)
