from decimal import Decimal

import pytest

from training.integral_v2.numbers import measurement, number


@pytest.mark.parametrize(
    "raw,value",
    [
        ("tres mil quinientos", "3500"),
        ("sesenta y uno", "61"),
        ("ciento veinticinco", "125"),
        ("0,75", ".75"),
        ("12.345,67", "12345.67"),
    ],
)
def test_conservative_normalization(raw, value):
    assert number(raw) == Decimal(value)


@pytest.mark.parametrize("raw", ["dos tres", "uno veinte", "mil mil", "y dos", "1.2,50"])
def test_ambiguous_numbers_fail(raw):
    with pytest.raises(ValueError):
        number(raw)


def test_spoken_decimal_requires_metres():
    assert measurement("uno veinte metros") == {"valor": "1.2", "unidad": "m"}
    with pytest.raises(ValueError):
        measurement("uno veinte")
    with pytest.raises(ValueError):
        measurement("1,7 mm a 2,1 mm")
