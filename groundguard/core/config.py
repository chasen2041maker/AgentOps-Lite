from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from groundguard.core.policy import Policy


@dataclass(frozen=True)
class ReportConfig:
    schema: str = "groundguard"
    fail_on_policy: bool = False


@dataclass(frozen=True)
class GroundGuardConfig:
    required_facts: list[str] = field(default_factory=list)
    policy: Policy = field(default_factory=Policy)
    report: ReportConfig = field(default_factory=ReportConfig)


def load_config(path: str | Path) -> GroundGuardConfig:
    """Load a small GroundGuard JSON/YAML config without external dependencies."""

    config_path = Path(path)
    raw_text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        payload = json.loads(raw_text)
    else:
        payload = _parse_simple_yaml(raw_text)
    return _config_from_payload(payload)


def _config_from_payload(payload: dict[str, Any]) -> GroundGuardConfig:
    policy_payload = _dict_or_empty(payload.get("policy"))
    report_payload = _dict_or_empty(payload.get("report"))
    return GroundGuardConfig(
        required_facts=[
            str(item) for item in _list_or_empty(payload.get("required_facts"))
        ],
        policy=Policy(
            max_unverified_ratio=float(
                policy_payload.get("max_unverified_ratio", Policy.max_unverified_ratio)
            ),
            max_contradicted=int(policy_payload.get("max_contradicted", Policy.max_contradicted)),
            max_ambiguous=int(policy_payload.get("max_ambiguous", Policy.max_ambiguous)),
            max_omitted_required=int(
                policy_payload.get("max_omitted_required", Policy.max_omitted_required)
            ),
            allow_candidate_matches=bool(
                policy_payload.get(
                    "allow_candidate_matches",
                    Policy.allow_candidate_matches,
                )
            ),
            on_unverified=str(policy_payload.get("on_unverified", Policy.on_unverified)),  # type: ignore[arg-type]
            on_contradicted=str(
                policy_payload.get("on_contradicted", Policy.on_contradicted)
            ),  # type: ignore[arg-type]
            on_omitted_required=str(
                policy_payload.get("on_omitted_required", Policy.on_omitted_required)
            ),  # type: ignore[arg-type]
        ),
        report=ReportConfig(
            schema=str(report_payload.get("schema", "groundguard")),
            fail_on_policy=bool(report_payload.get("fail_on_policy", False)),
        ),
    )


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_section: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not raw_line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1].strip()
            result[current_section] = [] if current_section == "required_facts" else {}
            continue
        if current_section == "required_facts" and line.strip().startswith("- "):
            result.setdefault(current_section, []).append(line.strip()[2:].strip())
            continue
        if current_section is not None and ":" in line:
            key, value = line.strip().split(":", 1)
            section = result.setdefault(current_section, {})
            if isinstance(section, dict):
                section[key.strip()] = _parse_scalar(value.strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = _parse_scalar(value.strip())
    return result


def _parse_scalar(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def _dict_or_empty(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list_or_empty(value: object) -> list[object]:
    return value if isinstance(value, list) else []

