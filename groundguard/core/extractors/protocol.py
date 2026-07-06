from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

from groundguard.core.models import OutputClaim


Extractor = Callable[[str], list[OutputClaim]]
ExtractorCollection = Mapping[str, Extractor] | Iterable[Extractor]
