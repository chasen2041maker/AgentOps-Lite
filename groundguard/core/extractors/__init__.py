from __future__ import annotations

from collections.abc import Mapping

from groundguard.core.output_claim_extractor import Extractor, registered_extractors


_PACKS: dict[str, tuple[str, ...]] = {
    "numeric": ("numeric",),
    "finance": ("numeric",),
    "saas": ("numeric",),
    "ecommerce": ("numeric",),
    "ops": ("numeric",),
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
        for extractor_name in _PACKS[normalized]:
            if extractor_name not in registry:
                raise ValueError(f"extractor pack {pack} requires missing extractor: {extractor_name}")
            resolved[extractor_name] = registry[extractor_name]
    return resolved
