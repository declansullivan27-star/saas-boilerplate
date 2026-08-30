"""Outbound copy.

Two rules run this module:

1. Everything is ASCII. A single curly quote or em dash flips an SMS from
   GSM-7 (160 chars a segment) to UCS-2 (70 chars a segment) and quietly
   triples the bill. :func:`ascii_safe` is applied to every outbound message.
2. Short. He reads this on a lock screen between classes.
"""

from __future__ import annotations

from datetime import date

from .advice import SpendPicture
from .config import BUCKET_LABELS, ESTIMATE_DISCLAIMER, MAX_SMS_CHARS
from .ledger import ExpenseResult, PaymentResult
from .money import fmt

_TRANSLIT = {
    ord("—"): "-", ord("–"): "-", ord("‒"): "-", ord("−"): "-",
    ord("‘"): "'", ord("’"): "'", ord("“"): '"', ord("”"): '"',
    ord("…"): "...", ord("·"): "-", ord("•"): "-", ord(" "): " ",
    ord("→"): "->", ord("×"): "x",
}


def ascii_safe(text: str) -> str:
    return (text or "").translate(_TRANSLIT).encode("ascii", "ignore").decode("ascii")


def clip(text: str, limit: int = MAX_SMS_CHARS) -> str:
    text = ascii_safe(text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def ordinal(day: int) -> str:
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }"


def _day_line(picture: SpendPicture) -> str:
    if picture.free_cents <= 0:
        return "Nothing free after bills until the next payment lands."
    return f"{fmt(picture.per_day_cents)}/day for the next {picture.horizon_days} days."


def payment_reply(payment: PaymentResult, picture: SpendPicture) -> str:
    parts = payment.allocations
    lines = [
        f"{fmt(payment.amount_cents)} in from {payment.source} ({payment.state_sourced}).",
        f"{fmt(parts['reserve'])} to tax. {fmt(parts['savings'])} to savings. "
        f"{fmt(parts['swing'])} to swing. {fmt(parts['spending'])} yours.",
        f"Spendable now {fmt(picture.spendable_cents)}. {_day_line(picture)}",
    ]
    return clip("\n".join(lines))


def expense_reply(expense: ExpenseResult, picture: SpendPicture) -> str:
    deduct = "likely deductible" if expense.deductible else "not deductible"
    head = f"Logged {expense.vendor} {fmt(expense.amount_cents, cents_always=True)} - {expense.category}, {deduct}."
    lines = [head]
    if expense.reason:
        lines.append(expense.reason)
    if expense.bucket == "swing":
        lines.append(f"Out of swing. {fmt(picture.swing_cents)} left there.")
    else:
        lines.append(f"Spendable now {fmt(picture.spendable_cents)}. {_day_line(picture)}")
    lines.append("Wrong? Reply UNDO.")
    return clip("\n".join(lines))


def spend_reply(picture: SpendPicture) -> str:
    lines = [f"Spendable: {fmt(picture.spendable_cents)}"]
    if picture.committed_cents:
        lines.append(f"minus {fmt(picture.committed_cents)} of bills in the next {picture.horizon_days} days")
        lines.append(f"= {fmt(picture.free_cents)} free. {_day_line(picture)}")
    else:
        lines.append(_day_line(picture))
    lines.append(f"Swing: {fmt(picture.swing_cents)} - yours, no questions.")
    lines.append(
        f"Savings {fmt(picture.savings_cents)}. Tax reserve {fmt(picture.reserve_cents)} - not yours."
    )
    lines.append(
        f"{picture.next_quarter_key} due {picture.next_quarter_due.strftime('%b')} {picture.next_quarter_due.day}: "
        f"{fmt(picture.next_quarter_set_aside_cents)} set aside. {ESTIMATE_DISCLAIMER}"
    )
    return clip("\n".join(lines))


def month_reply(picture: SpendPicture, deductions_cents: int, on: date) -> str:
    lines = [
        f"{on.strftime('%B')}: {fmt(picture.month_income_cents)} in, {fmt(picture.month_spent_cents)} out.",
        f"Spendable left {fmt(picture.spendable_cents)}. {_day_line(picture)}",
        f"Swing {fmt(picture.swing_cents)}. Savings {fmt(picture.savings_cents)}.",
        f"Deductions logged this month: {fmt(deductions_cents)}. Every one of those is money back in April.",
    ]
    return clip("\n".join(lines))


def quarter_reply(picture: SpendPicture, state_split: dict[str, int], links: str, days: int) -> str:
    when = "today" if days == 0 else f"in {days} days"
    lines = [
        f"{picture.next_quarter_key} estimated payment due "
        f"{picture.next_quarter_due.strftime('%a %b')} {picture.next_quarter_due.day} - {when}.",
        f"Set aside for it: {fmt(picture.next_quarter_set_aside_cents)}.",
    ]
    if state_split:
        lines.append("Sourced: " + ", ".join(f"{st} {fmt(c)}" for st, c in sorted(state_split.items())))
    lines.append(links)
    lines.append(ESTIMATE_DISCLAIMER)
    return clip("\n".join(lines), limit=700)


def bills_reply(rows, monthly_total: int, remaining: int) -> str:
    if not rows:
        return clip(
            "No recurring bills tracked yet.\n"
            "Text one like: rent 1200 monthly on the 1st\n"
            "Then I can tell you what's actually free to spend."
        )

    lines = ["Bills each month:"]
    for row in rows:
        lines.append(f"  {row['name']} {fmt(row['amount_cents'])} on the {ordinal(row['day_of_month'])}")
    lines.append(f"Total {fmt(monthly_total)}/mo. {fmt(remaining)} of it lands in the next 30 days.")
    lines.append("Remove one: BILL REMOVE rent")
    return clip("\n".join(lines), limit=700)


def deductions_reply(totals: list[tuple[str, int]], total_cents: int, year: int) -> str:
    if not total_cents:
        return clip(
            "No deductions logged yet this year.\n"
            "Photograph a receipt and text it to me - that is the part that pays for itself."
        )
    lines = [f"{year} deductions logged: {fmt(total_cents)}"]
    for category, cents in totals[:6]:
        lines.append(f"  {category} {fmt(cents)}")
    lines.append(f"Text EXPORT in April and your EA gets all of it as a CSV. {ESTIMATE_DISCLAIMER}")
    return clip("\n".join(lines), limit=700)


def have_reply(payment: PaymentResult | None, picture: SpendPicture, taxed: bool, amount_cents: int) -> str:
    if taxed:
        return clip(
            f"Got it - {fmt(amount_cents)} on hand, already taxed. All of it went to spendable.\n"
            f"Spendable now {fmt(picture.spendable_cents)}. {_day_line(picture)}"
        )
    assert payment is not None
    parts = payment.allocations
    return clip(
        f"Starting with {fmt(amount_cents)}. I treated it as untaxed 1099 money:\n"
        f"{fmt(parts['reserve'])} tax, {fmt(parts['savings'])} savings, {fmt(parts['swing'])} swing, "
        f"{fmt(parts['spending'])} yours.\n"
        f"Already taxed? Reply: HAVE {amount_cents // 100} TAXED"
    )


HELP = """Text me like a person. Examples:
"got 10000 from the collective" - logs it and splits it
"spent 42 on gas" - or just send a photo of the receipt
"rent 1200 monthly on the 1st" - tracks a bill
"i have 4200 in checking" - starting balance

? or SPEND - what you can spend right now
TAX - quarterly deadline and what's set aside
MONTH - this month at a glance
BILLS - what's committed
DEDUCTIONS - what you've written off
EXPORT - CSV for your EA
UNDO - take back the last thing
DEAL - forward a contract and I'll pull out the terms

I never move money and I never give tax advice."""


WELCOME = """I keep your money straight. Two things I do:

1. Every payment gets split the second it lands - tax, savings, swing, yours.
2. Every receipt gets logged so April costs you thousands less.

Start by telling me what you've got: "i have 4200 in checking"
Then text me every time money moves.
Text ? any time to see what's actually spendable.
HELP for everything else."""


UNKNOWN = """Didn't catch that. Try:
"got 5000 from the collective" | "spent 42 on gas" | "?" for what's spendable | HELP"""


def bucket_label(bucket: str) -> str:
    return BUCKET_LABELS.get(bucket, bucket)
