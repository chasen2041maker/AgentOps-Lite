from __future__ import annotations

from decimal import Decimal


def normalize_numeric_fact(value: Decimal, unit: str | None) -> tuple[Decimal, str | None]:
    """Normalize a numeric fact value into base units used by the matcher."""

    multiplier, normalized_unit = unit_multiplier_and_name(unit)
    return value * multiplier, normalized_unit


def unit_multiplier_and_name(unit: str | None) -> tuple[Decimal, str | None]:
    if unit is None:
        return Decimal("1"), None
    normalized = unit.strip().lower().replace(" ", "_").replace("-", "_")

    exact_units = {
        "cny": (Decimal("1"), "CNY"),
        "rmb": (Decimal("1"), "CNY"),
        "人民币": (Decimal("1"), "CNY"),
        "元": (Decimal("1"), "CNY"),
        "usd": (Decimal("1"), "USD"),
        "us$": (Decimal("1"), "USD"),
        "$": (Decimal("1"), "USD"),
        "美元": (Decimal("1"), "USD"),
        "dollar": (Decimal("1"), "USD"),
        "dollars": (Decimal("1"), "USD"),
        "us_dollar": (Decimal("1"), "USD"),
        "us_dollars": (Decimal("1"), "USD"),
        "%": (Decimal("1"), "%"),
        "percent": (Decimal("1"), "%"),
        "percentage_point": (Decimal("1"), "%"),
        "percentage_points": (Decimal("1"), "%"),
        "股": (Decimal("1"), "股"),
        "shares": (Decimal("1"), "股"),
        "倍": (Decimal("1"), "倍"),
        "x": (Decimal("1"), "倍"),
        "times": (Decimal("1"), "倍"),
    }
    if normalized in exact_units:
        return exact_units[normalized]

    scaled_units = {
        "亿元": (Decimal("100000000"), "CNY"),
        "万亿元": (Decimal("1000000000000"), "CNY"),
        "万元": (Decimal("10000"), "CNY"),
        "千元": (Decimal("1000"), "CNY"),
        "cny_b": (Decimal("1000000000"), "CNY"),
        "cny_bn": (Decimal("1000000000"), "CNY"),
        "cny_m": (Decimal("1000000"), "CNY"),
        "cny_mn": (Decimal("1000000"), "CNY"),
        "cny_k": (Decimal("1000"), "CNY"),
        "cny_100m": (Decimal("100000000"), "CNY"),
        "cny_10k": (Decimal("10000"), "CNY"),
        "亿美元": (Decimal("100000000"), "USD"),
        "万美元": (Decimal("10000"), "USD"),
        "千美元": (Decimal("1000"), "USD"),
        "usd_b": (Decimal("1000000000"), "USD"),
        "usd_bn": (Decimal("1000000000"), "USD"),
        "usd_m": (Decimal("1000000"), "USD"),
        "usd_mn": (Decimal("1000000"), "USD"),
        "usd_k": (Decimal("1000"), "USD"),
        "usd_100m": (Decimal("100000000"), "USD"),
        "usd_10k": (Decimal("10000"), "USD"),
    }
    if normalized in scaled_units:
        return scaled_units[normalized]

    return Decimal("1"), unit


def magnitude_multiplier(magnitude: str | None) -> Decimal:
    if magnitude is None:
        return Decimal("1")
    normalized = magnitude.lower()
    if magnitude == "亿":
        return Decimal("100000000")
    if magnitude == "万":
        return Decimal("10000")
    if magnitude == "千":
        return Decimal("1000")
    if normalized in {"billion", "bn", "b"}:
        return Decimal("1000000000")
    if normalized in {"million", "mn", "m"}:
        return Decimal("1000000")
    if normalized in {"thousand", "k"}:
        return Decimal("1000")
    return Decimal("1")


def normalized_unit(unit: str | None) -> str | None:
    return unit_multiplier_and_name(unit)[1]


def normalized_currency_prefix(currency_prefix: str | None) -> str | None:
    return normalized_unit(currency_prefix)
