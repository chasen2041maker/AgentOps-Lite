from __future__ import annotations

from dataclasses import replace

from groundguard.core.models import OutputClaim
from groundguard.core.output_claim_extractor import registered_extractors


_FINANCE_ALIASES = {
    "free_cash_flow": ("free cash flow", "fcf", "\u81ea\u7531\u73b0\u91d1\u6d41"),
    "operating_cash_flow": ("operating cash flow", "\u7ecf\u8425\u73b0\u91d1\u6d41"),
    "gross_margin": ("gross margin", "margin", "\u6bdb\u5229\u7387"),
    "net_profit": ("net profit", "\u51c0\u5229\u6da6"),
    "revenue": ("revenue", "sales", "\u6536\u5165", "\u8425\u6536"),
    "eps": ("eps", "earnings per share"),
    "yoy_growth": ("yoy", "year over year", "\u540c\u6bd4"),
    "qoq_growth": ("qoq", "quarter over quarter", "\u73af\u6bd4"),
}

_SAAS_ALIASES = {
    "arr": ("arr", "annual recurring revenue"),
    "mrr": ("mrr", "monthly recurring revenue"),
    "churn": ("churn", "\u6d41\u5931\u7387"),
    "nrr": ("nrr", "net revenue retention"),
    "cac": ("cac", "customer acquisition cost"),
    "ltv": ("ltv", "lifetime value"),
}

_ECOMMERCE_ALIASES = {
    "conversion_rate": ("conversion rate", "conversion", "\u8f6c\u5316\u7387"),
    "orders": ("orders", "order count", "\u8ba2\u5355"),
    "gmv": ("gmv", "gross merchandise value"),
    "aov": ("aov", "average order value"),
}

_OPS_ALIASES = {
    "p95_latency": ("p95 latency", "p95", "p95\u5ef6\u8fdf"),
    "error_rate": ("error rate", "\u9519\u8bef\u7387"),
    "uptime": ("uptime", "\u53ef\u7528\u6027"),
    "throughput": ("throughput", "\u541e\u5410\u91cf"),
    "storage": ("storage", "\u5b58\u50a8"),
    "latency": ("latency", "\u5ef6\u8fdf"),
}


def finance_metric_extractor(text: str) -> list[OutputClaim]:
    return _extract_metric_claims(text, _FINANCE_ALIASES)


def saas_metric_extractor(text: str) -> list[OutputClaim]:
    return _extract_metric_claims(text, _SAAS_ALIASES)


def ecommerce_metric_extractor(text: str) -> list[OutputClaim]:
    return _extract_metric_claims(text, _ECOMMERCE_ALIASES)


def ops_metric_extractor(text: str) -> list[OutputClaim]:
    return _extract_metric_claims(text, _OPS_ALIASES)


def _extract_metric_claims(
    text: str,
    aliases_by_key: dict[str, tuple[str, ...]],
) -> list[OutputClaim]:
    numeric_extractor = registered_extractors()["numeric"]
    claims: list[OutputClaim] = []
    for claim in numeric_extractor(text):
        if claim.fact_key is not None or claim.start is None:
            continue
        fact_key = _fact_key_for_claim(text, claim, aliases_by_key)
        if fact_key is None:
            continue
        claims.append(
            replace(
                claim,
                id=f"{claim.id}_{fact_key}",
                fact_key=fact_key,
            )
        )
    return claims


def _fact_key_for_claim(
    text: str,
    claim: OutputClaim,
    aliases_by_key: dict[str, tuple[str, ...]],
) -> str | None:
    start = claim.start or 0
    window_start = _clause_start(text, start)
    window = text[window_start:start].lower()
    best_key: str | None = None
    best_end = -1
    best_length = -1
    for fact_key, aliases in aliases_by_key.items():
        for alias in aliases:
            normalized_alias = alias.lower()
            index = window.rfind(normalized_alias)
            if index == -1:
                continue
            alias_end = index + len(normalized_alias)
            if alias_end > best_end or (
                alias_end == best_end and len(alias) > best_length
            ):
                best_key = fact_key
                best_end = alias_end
                best_length = len(alias)
    return best_key


def _clause_start(text: str, index: int) -> int:
    delimiters = ".\u3002;\uff1b\n"
    starts = [text.rfind(delimiter, 0, index) for delimiter in delimiters]
    latest = max(starts)
    return latest + 1 if latest != -1 else max(0, index - 96)
