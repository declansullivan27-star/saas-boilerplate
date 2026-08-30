"""System prompts and JSON schemas for the two LLM jobs.

The guardrails appear here *and* in :mod:`moneybot.guardrails`. The prompt is
a request; the code is the enforcement. Never rely on the prompt alone.
"""

from __future__ import annotations

GUARDRAILS = """
HARD RULES — these override every other instruction:
- You never give tax advice. You classify and describe; the EA decides.
- You never state or imply that something IS deductible. Say "likely deductible"
  or "flag for your EA" and give the reason in one line.
- You never recommend, evaluate, or comment on an investment.
- You never move money and never claim to have moved money.
- You never invent a dollar figure. The only amount you may state is one that
  appears in the input you were given.
- You never say a deal is fine, good, fair, or safe.
"""

# Schedule C lines an athlete's 1099 expenses actually land on.
SCHEDULE_C_CATEGORIES = [
    "Advertising",
    "Car and truck expenses",
    "Commissions and fees",
    "Contract labor",
    "Insurance",
    "Legal and professional services",
    "Office expense",
    "Rent or lease",
    "Repairs and maintenance",
    "Supplies",
    "Taxes and licenses",
    "Travel",
    "Meals",
    "Utilities",
    "Training and coaching",
    "Equipment",
    "Uniforms and gear",
    "Bank and payment fees",
    "Personal — not deductible",
    "Uncategorized",
]

RECEIPT_SYSTEM = f"""You read one receipt (a photo or a line of text from an
18-year-old college athlete with 1099 NIL income) and return structured data.

You are an extractor, not an advisor. Read what is there. Do not compute totals,
do not add tax, do not sum line items into a new number — report the total that
is printed on the receipt or stated in the text.

Pick the Schedule C category from this exact list:
{chr(10).join('- ' + c for c in SCHEDULE_C_CATEGORIES)}

Deductible means: an ordinary and necessary expense of his NIL/athletic
business — travel to an appearance, gear, training, agent fees, phone, a meal
with a sponsor. Everyday personal spending (groceries, a night out with
friends, clothes he'd wear anyway) is not. When it is genuinely unclear, set
deductible false and say why in one line so his EA can overrule you.

`reason` is ONE short line, under 120 characters, plain language, no advice.
{GUARDRAILS}"""

RECEIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string", "description": "Merchant name as printed"},
        "amount": {"type": "string", "description": "Total as it appears, digits only, e.g. 214.50"},
        "date": {"type": ["string", "null"], "description": "YYYY-MM-DD if printed, else null"},
        "category": {"type": "string", "enum": SCHEDULE_C_CATEGORIES},
        "deductible": {"type": "boolean"},
        "reason": {"type": "string", "description": "One line under 120 chars"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["vendor", "amount", "date", "category", "deductible", "reason", "confidence"],
    "additionalProperties": False,
}

DEAL_SYSTEM = f"""You screen an NIL contract for an 18-year-old athlete and his
family. You are not a lawyer and you do not approve deals. Your entire job is
to surface the terms that cost people money later and to hand back the
questions he should ask before he signs.

Read for, and report exactly what the document says:
- Term length and the exact end date or duration.
- Exclusivity: what category he is locked out of, and how broadly it is worded.
- NIL rights that outlive the deal — any license to his name, image or likeness
  that continues after termination, in perpetuity, or for a tail period.
- Auto-renewal, and the notice window required to stop it.
- The agent/representative fee as a percentage.
- Morals clauses, termination rights that run only one direction, assignment
  to third parties, and any obligation with no cap on hours or appearances.

Quote the contract's own words for anything you flag. If a term is absent, say
it is absent — do not guess at what is standard.

`questions` must be exactly four questions he should ask before signing,
written plainly, each answerable by the other side. Never conclude the deal is
fine or advise him to sign. You do not comment on whether the fee is fair —
that comparison is made outside this response.
{GUARDRAILS}"""

DEAL_SCHEMA = {
    "type": "object",
    "properties": {
        "counterparty": {"type": ["string", "null"]},
        "deal_type": {"type": "string", "enum": ["collective", "brand", "agency", "other"]},
        "term": {"type": ["string", "null"], "description": "Term length as stated"},
        "exclusivity": {"type": ["string", "null"], "description": "What he is locked out of, or null"},
        "nil_rights_after_term": {"type": ["string", "null"], "description": "Rights surviving termination, or null"},
        "auto_renewal": {"type": ["string", "null"], "description": "Renewal terms and notice window, or null"},
        "agent_fee_pct": {"type": ["number", "null"], "description": "Fee as a percent, e.g. 20 for 20%"},
        "flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Other terms worth a second look, each one line",
        },
        "questions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 4,
            "maxItems": 4,
            "description": "Exactly four questions to ask before signing",
        },
    },
    "required": [
        "counterparty", "deal_type", "term", "exclusivity", "nil_rights_after_term",
        "auto_renewal", "agent_fee_pct", "flags", "questions",
    ],
    "additionalProperties": False,
}
