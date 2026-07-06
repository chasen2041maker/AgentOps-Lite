from __future__ import annotations

from decimal import Decimal


def normalize_numeric_fact(value: Decimal, unit: str | None) -> tuple[Decimal, str | None]:
    """Normalize a numeric fact value into base units used by the matcher."""

    multiplier, normalized_unit = unit_multiplier_and_name(unit)
    return value * multiplier, normalized_unit


# Normalized unit table with ASCII source plus Unicode escapes, so source
# encoding quirks cannot change matcher behavior.
def unit_multiplier_and_name(unit: str | None) -> tuple[Decimal, str | None]:
    if unit is None:
        return Decimal("1"), None
    normalized = unit.strip().lower().replace(" ", "_").replace("-", "_")

    exact_units = {
        "cny": (Decimal("1"), "CNY"),
        "rmb": (Decimal("1"), "CNY"),
        "\u4eba\u6c11\u5e01": (Decimal("1"), "CNY"),
        "\u00a5": (Decimal("1"), "CNY"),
        "\uffe5": (Decimal("1"), "CNY"),
        "\u5143": (Decimal("1"), "CNY"),
        "yuan": (Decimal("1"), "CNY"),
        "usd": (Decimal("1"), "USD"),
        "us$": (Decimal("1"), "USD"),
        "$": (Decimal("1"), "USD"),
        "\u7f8e\u5143": (Decimal("1"), "USD"),
        "dollar": (Decimal("1"), "USD"),
        "dollars": (Decimal("1"), "USD"),
        "us_dollar": (Decimal("1"), "USD"),
        "us_dollars": (Decimal("1"), "USD"),
        "eur": (Decimal("1"), "EUR"),
        "\u20ac": (Decimal("1"), "EUR"),
        "euro": (Decimal("1"), "EUR"),
        "euros": (Decimal("1"), "EUR"),
        "gbp": (Decimal("1"), "GBP"),
        "\u00a3": (Decimal("1"), "GBP"),
        "pound": (Decimal("1"), "GBP"),
        "pounds": (Decimal("1"), "GBP"),
        "%": (Decimal("1"), "%"),
        "percent": (Decimal("1"), "%"),
        "percentage_point": (Decimal("1"), "%"),
        "percentage_points": (Decimal("1"), "%"),
        "\u767e\u5206\u70b9": (Decimal("1"), "%"),
        "\u4e2a\u767e\u5206\u70b9": (Decimal("1"), "%"),
        "bps": (Decimal("1"), "bps"),
        "basis_point": (Decimal("1"), "bps"),
        "basis_points": (Decimal("1"), "bps"),
        "\u57fa\u70b9": (Decimal("1"), "bps"),
        "user": (Decimal("1"), "users"),
        "users": (Decimal("1"), "users"),
        "\u7528\u6237": (Decimal("1"), "users"),
        "customer": (Decimal("1"), "customers"),
        "customers": (Decimal("1"), "customers"),
        "\u5ba2\u6237": (Decimal("1"), "customers"),
        "request": (Decimal("1"), "requests"),
        "requests": (Decimal("1"), "requests"),
        "\u8bf7\u6c42": (Decimal("1"), "requests"),
        "order": (Decimal("1"), "orders"),
        "orders": (Decimal("1"), "orders"),
        "\u8ba2\u5355": (Decimal("1"), "orders"),
        "\u5355": (Decimal("1"), "orders"),
        "ticket": (Decimal("1"), "tickets"),
        "tickets": (Decimal("1"), "tickets"),
        "\u5de5\u5355": (Decimal("1"), "tickets"),
        "incident": (Decimal("1"), "incidents"),
        "incidents": (Decimal("1"), "incidents"),
        "\u6b21": (Decimal("1"), "incidents"),
        "shipment": (Decimal("1"), "shipments"),
        "shipments": (Decimal("1"), "shipments"),
        "\u7968": (Decimal("1"), "shipments"),
        "unit": (Decimal("1"), "units"),
        "units": (Decimal("1"), "units"),
        "item": (Decimal("1"), "units"),
        "items": (Decimal("1"), "units"),
        "\u4ef6": (Decimal("1"), "units"),
        "ms": (Decimal("1"), "ms"),
        "millisecond": (Decimal("1"), "ms"),
        "milliseconds": (Decimal("1"), "ms"),
        "\u6beb\u79d2": (Decimal("1"), "ms"),
        "second": (Decimal("1"), "seconds"),
        "seconds": (Decimal("1"), "seconds"),
        "\u79d2": (Decimal("1"), "seconds"),
        "minute": (Decimal("1"), "minutes"),
        "minutes": (Decimal("1"), "minutes"),
        "\u5206\u949f": (Decimal("1"), "minutes"),
        "hour": (Decimal("1"), "hours"),
        "hours": (Decimal("1"), "hours"),
        "\u5c0f\u65f6": (Decimal("1"), "hours"),
        "mb": (Decimal("1"), "MB"),
        "gb": (Decimal("1"), "GB"),
        "tb": (Decimal("1"), "TB"),
        "\u80a1": (Decimal("1"), "\u80a1"),
        "share": (Decimal("1"), "\u80a1"),
        "shares": (Decimal("1"), "\u80a1"),
        "\u500d": (Decimal("1"), "\u500d"),
        "x": (Decimal("1"), "\u500d"),
        "times": (Decimal("1"), "\u500d"),
    }
    if normalized in exact_units:
        return exact_units[normalized]

    scaled_units = {
        "\u4ebf\u5143": (Decimal("100000000"), "CNY"),
        "\u4e07\u4ebf\u5143": (Decimal("1000000000000"), "CNY"),
        "\u4e07\u5143": (Decimal("10000"), "CNY"),
        "\u5343\u5143": (Decimal("1000"), "CNY"),
        "cny_b": (Decimal("1000000000"), "CNY"),
        "cny_bn": (Decimal("1000000000"), "CNY"),
        "cny_m": (Decimal("1000000"), "CNY"),
        "cny_mn": (Decimal("1000000"), "CNY"),
        "cny_k": (Decimal("1000"), "CNY"),
        "cny_100m": (Decimal("100000000"), "CNY"),
        "cny_10k": (Decimal("10000"), "CNY"),
        "\u4ebf\u7f8e\u5143": (Decimal("100000000"), "USD"),
        "\u4e07\u7f8e\u5143": (Decimal("10000"), "USD"),
        "\u5343\u7f8e\u5143": (Decimal("1000"), "USD"),
        "usd_b": (Decimal("1000000000"), "USD"),
        "usd_bn": (Decimal("1000000000"), "USD"),
        "usd_m": (Decimal("1000000"), "USD"),
        "usd_mn": (Decimal("1000000"), "USD"),
        "usd_k": (Decimal("1000"), "USD"),
        "usd_100m": (Decimal("100000000"), "USD"),
        "usd_10k": (Decimal("10000"), "USD"),
        "eur_b": (Decimal("1000000000"), "EUR"),
        "eur_bn": (Decimal("1000000000"), "EUR"),
        "eur_m": (Decimal("1000000"), "EUR"),
        "eur_mn": (Decimal("1000000"), "EUR"),
        "eur_k": (Decimal("1000"), "EUR"),
        "gbp_b": (Decimal("1000000000"), "GBP"),
        "gbp_bn": (Decimal("1000000000"), "GBP"),
        "gbp_m": (Decimal("1000000"), "GBP"),
        "gbp_mn": (Decimal("1000000"), "GBP"),
        "gbp_k": (Decimal("1000"), "GBP"),
    }
    if normalized in scaled_units:
        return scaled_units[normalized]

    return Decimal("1"), unit


def magnitude_multiplier(magnitude: str | None) -> Decimal:
    if magnitude is None:
        return Decimal("1")
    normalized = magnitude.lower()
    if normalized == "\u4ebf":
        return Decimal("100000000")
    if normalized == "\u4e07":
        return Decimal("10000")
    if normalized == "\u5343":
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
