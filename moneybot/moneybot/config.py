"""Configuration. Everything tunable lives here or in the DB settings table."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# --- Bucket policy ---------------------------------------------------------
# Ratios of GROSS income. `spending` is the remainder bucket and absorbs
# rounding, so the four parts always sum to the payment exactly.
DEFAULT_RATIOS: dict[str, float] = {
    "reserve": 0.37,   # federal + SE + state tax set-aside
    "savings": 0.15,   # long-term, not spendable
    "swing": 0.10,     # his to do anything with; the bot never comments on it
    "spending": 0.0,   # remainder
}

BUCKET_ORDER = ("reserve", "savings", "swing", "spending")

BUCKET_LABELS = {
    "reserve": "Tax reserve",
    "savings": "Savings",
    "swing": "Swing",
    "spending": "Spendable",
}

# --- Tax ------------------------------------------------------------------
HOME_STATE_DEFAULT = "MO"
SUPPORTED_STATES = ("MO", "KS")
IRS_DIRECT_PAY = "https://www.irs.gov/payments/direct-pay"
STATE_PAY_LINKS = {
    "MO": "https://mytax.mo.gov/rptp/portal/home/indiv-estimated-tax",
    "KS": "https://www.kdor.ks.gov/apps/kcsc/increment/default.aspx",
}

# --- Agent fee benchmarks (used by the deal screen, code-side not LLM-side) --
FEE_BENCHMARKS = {
    "collective": (0.03, 0.05),
    "brand": (0.15, 0.20),
}

ESTIMATE_DISCLAIMER = "Estimate - confirm with your EA."

MAX_SMS_CHARS = 480  # ~3 segments; hard ceiling on any outbound message


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw in (None, ""):
        return default
    return float(raw)


@dataclass
class Config:
    db_path: str = field(default_factory=lambda: os.environ.get("MONEYBOT_DB", "moneybot.db"))
    media_dir: str = field(default_factory=lambda: os.environ.get("MONEYBOT_MEDIA_DIR", "media"))
    home_state: str = field(default_factory=lambda: os.environ.get("MONEYBOT_HOME_STATE", HOME_STATE_DEFAULT))

    # Channel credentials
    twilio_account_sid: str = field(default_factory=lambda: os.environ.get("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.environ.get("TWILIO_AUTH_TOKEN", ""))
    twilio_from: str = field(default_factory=lambda: os.environ.get("TWILIO_FROM", ""))
    telegram_token: str = field(default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN", ""))

    # Anthropic
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = field(default_factory=lambda: os.environ.get("MONEYBOT_MODEL", "claude-opus-5"))

    # Who is allowed to talk to it. Comma-separated E.164 numbers and/or
    # Telegram chat ids. Empty means "first sender wins and is remembered".
    allowed_senders: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            s.strip() for s in os.environ.get("MONEYBOT_ALLOWED_SENDERS", "").split(",") if s.strip()
        )
    )

    public_base_url: str = field(default_factory=lambda: os.environ.get("MONEYBOT_BASE_URL", ""))
    validate_twilio_signature: bool = field(
        default_factory=lambda: os.environ.get("MONEYBOT_VALIDATE_SIGNATURE", "1") != "0"
    )

    ratios: dict[str, float] = field(
        default_factory=lambda: {
            "reserve": _env_float("MONEYBOT_RESERVE_PCT", DEFAULT_RATIOS["reserve"]),
            "savings": _env_float("MONEYBOT_SAVINGS_PCT", DEFAULT_RATIOS["savings"]),
            "swing": _env_float("MONEYBOT_SWING_PCT", DEFAULT_RATIOS["swing"]),
            "spending": 0.0,
        }
    )

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)


def load() -> Config:
    return Config()
