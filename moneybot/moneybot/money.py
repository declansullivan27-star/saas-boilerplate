"""Integer-cent money helpers.

Every dollar figure in this system is an ``int`` number of cents. Floats are
only allowed at the edges (parsing user text, rendering a reply) and are
converted immediately. This is the reason the ledger can never drift.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTS = Decimal("0.01")


class MoneyError(ValueError):
    """Raised when text cannot be read as an amount of money."""


def to_cents(value) -> int:
    """Convert a user-supplied amount to integer cents.

    Accepts ``"1,234.56"``, ``"$1234.56"``, ``"10k"``, ``1234.56`` and ``1234``.
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value * 100
    if isinstance(value, float):
        dec = Decimal(str(value))
    else:
        text = str(value).strip().lower()
        text = text.replace("$", "").replace(",", "").replace("_", "")
        multiplier = 1
        if text.endswith("k"):
            multiplier, text = 1000, text[:-1]
        try:
            dec = Decimal(text) * multiplier
        except (InvalidOperation, ValueError) as exc:
            raise MoneyError(f"not an amount: {value!r}") from exc
    return int(dec.quantize(CENTS, rounding=ROUND_HALF_UP) * 100)


def fmt(cents: int, *, cents_always: bool = False) -> str:
    """Render cents as ``$1,234.56`` (or ``$1,234`` when it is a round dollar)."""
    sign = "-" if cents < 0 else ""
    whole, rem = divmod(abs(int(cents)), 100)
    if rem == 0 and not cents_always:
        return f"{sign}${whole:,}"
    return f"{sign}${whole:,}.{rem:02d}"


def split_by_ratio(total_cents: int, ratios: dict[str, float], remainder_key: str) -> dict[str, int]:
    """Split ``total_cents`` across buckets with zero rounding loss.

    Each non-remainder bucket gets ``floor``-safe rounded cents; the remainder
    bucket absorbs whatever is left so the parts always sum to the whole.
    Negative totals (a clawback) split proportionally the same way.
    """
    if remainder_key not in ratios:
        raise ValueError(f"remainder bucket {remainder_key!r} missing from ratios")
    out: dict[str, int] = {}
    allocated = 0
    for name, ratio in ratios.items():
        if name == remainder_key:
            continue
        share = int(
            (Decimal(total_cents) * Decimal(str(ratio))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        out[name] = share
        allocated += share
    out[remainder_key] = total_cents - allocated
    return out
