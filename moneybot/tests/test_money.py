import pytest

from moneybot.money import MoneyError, fmt, split_by_ratio, to_cents


@pytest.mark.parametrize(
    "raw,cents",
    [
        ("10000", 1_000_000),
        ("10k", 1_000_000),
        ("$1,234.56", 123_456),
        ("214.5", 21_450),
        ("0.01", 1),
        (1234, 123_400),
        (12.34, 1234),
        ("  $42 ", 4200),
    ],
)
def test_to_cents(raw, cents):
    assert to_cents(raw) == cents


def test_to_cents_rejects_junk():
    with pytest.raises(MoneyError):
        to_cents("later")


def test_to_cents_rounds_half_up():
    assert to_cents("0.005") == 1
    assert to_cents("1.994") == 199


@pytest.mark.parametrize(
    "cents,text",
    [(1_000_000, "$10,000"), (21_450, "$214.50"), (0, "$0"), (-4200, "-$42")],
)
def test_fmt(cents, text):
    assert fmt(cents) == text


def test_fmt_forces_cents_when_asked():
    assert fmt(1_000_000, cents_always=True) == "$10,000.00"


RATIOS = {"reserve": 0.37, "savings": 0.15, "swing": 0.10, "spending": 0.0}


def test_split_matches_the_spec_example():
    parts = split_by_ratio(1_000_000, {**RATIOS, "savings": 0.0}, "spending")
    assert parts["reserve"] == 370_000
    assert parts["swing"] == 100_000
    assert parts["spending"] == 530_000


@pytest.mark.parametrize("total", [1, 7, 99, 333_333, 1_000_000, 12_345_678, 1_000_001])
def test_split_is_lossless(total):
    parts = split_by_ratio(total, RATIOS, "spending")
    assert sum(parts.values()) == total


def test_split_handles_a_clawback():
    parts = split_by_ratio(-100_000, RATIOS, "spending")
    assert sum(parts.values()) == -100_000
    assert parts["reserve"] == -37_000


def test_split_requires_a_remainder_bucket():
    with pytest.raises(ValueError):
        split_by_ratio(100, RATIOS, "nope")
