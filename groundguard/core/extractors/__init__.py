from __future__ import annotations

from collections.abc import Mapping

from groundguard.core.output_claim_extractor import Extractor, registered_extractors
from groundguard.core.extractors.packs import (
    ecommerce_metric_extractor,
    finance_metric_extractor,
    ops_metric_extractor,
    saas_metric_extractor,
)


_PACKS: dict[str, tuple[tuple[str, Extractor] | str, ...]] = {
    "numeric": ("numeric",),
    "finance": (("finance_metric", finance_metric_extractor), "numeric"),
    "saas": (("saas_metric", saas_metric_extractor), "numeric"),
    "ecommerce": (("ecommerce_metric", ecommerce_metric_extractor), "numeric"),
    "ops": (("ops_metric", ops_metric_extractor), "numeric"),
}


def available_extractor_packs() -> list[str]:
    """Return built-in extractor pack names."""

    return sorted(_PACKS)


def extractors_for_packs(packs: list[str] | tuple[str, ...]) -> Mapping[str, Extractor]:
    """Resolve named extractor packs into a scoped extractor mapping.

    Packs intentionally do not mutate the process-wide extractor registry. They
    provide a stable config surface while keeping one request/tenant isolated
    from another.
    """

    registry = registered_extractors()
    resolved: dict[str, Extractor] = {}
    for pack in packs:
        normalized = pack.strip().lower()
        if normalized not in _PACKS:
            raise ValueError(f"unknown extractor pack: {pack}")
        for extractor_ref in _PACKS[normalized]:
            if isinstance(extractor_ref, tuple):
                extractor_name, extractor = extractor_ref
                resolved[extractor_name] = extractor
                continue
            if extractor_ref not in registry:
                raise ValueError(f"extractor pack {pack} requires missing extractor: {extractor_ref}")
            resolved[extractor_ref] = registry[extractor_ref]
    return resolved
