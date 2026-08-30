import pytest

from moneybot.allocator import allocate, ratios_from_db, validate_ratios


def test_ratios_come_from_the_database(conn):
    ratios = ratios_from_db(conn)
    assert ratios["reserve"] == 0.37
    assert ratios["spending"] == 0.0


def test_allocate_sums_to_the_payment(conn):
    parts = allocate(1_000_000, ratios_from_db(conn))
    assert sum(parts.values()) == 1_000_000
    assert parts["reserve"] == 370_000
    assert parts["savings"] == 150_000
    assert parts["swing"] == 100_000
    assert parts["spending"] == 380_000


def test_percentages_over_one_hundred_are_refused():
    with pytest.raises(ValueError, match="nothing spendable"):
        validate_ratios({"reserve": 0.6, "savings": 0.3, "swing": 0.2, "spending": 0.0})


def test_negative_percentages_are_refused():
    with pytest.raises(ValueError):
        validate_ratios({"reserve": -0.1, "savings": 0.1, "swing": 0.1, "spending": 0.0})
