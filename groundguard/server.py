from __future__ import annotations

import argparse
import json
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from groundguard.core.config import GroundGuardConfig, load_config
from groundguard.runtime import FactGate
from groundguard.report import report_to_versioned_dict


def evaluate_payload(
    payload: dict[str, Any],
    config: GroundGuardConfig | None = None,
) -> dict[str, Any]:
    """Evaluate one JSON-compatible request payload."""

    gate = FactGate(
        session_id=str(payload.get("session_id", "groundguard_server")),
        config=config,
    )
    for fact_payload in payload.get("facts", []):
        if not isinstance(fact_payload, dict):
            continue
        gate.record_fact(
            key=str(fact_payload["key"]),
            value=_coerce_numeric(fact_payload.get("value", "")),
            unit=_optional_str(fact_payload.get("unit")),
            source_tool=str(fact_payload.get("source_tool", "tool")),
            source_call_id=str(fact_payload.get("source_call_id", "server")),
        )
    required_facts = [
        str(item)
        for item in payload.get("required_facts", payload.get("required_fact_keys", []))
    ]
    report = gate.check(
        str(payload.get("answer", "")),
        required_fact_keys=required_facts or None,
    )
    return report_to_versioned_dict(report)


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    config: GroundGuardConfig | None = None,
) -> None:
    """Start a tiny dependency-free HTTP server with POST /check."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/check":
                self.send_error(404)
                return
            length = int(self.headers.get("content-length", "0"))
            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
                result = evaluate_payload(payload, config=config)
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            except Exception as exc:  # pragma: no cover - defensive server path
                self.send_response(400)
                self.send_header("content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
                )
                return
            self.send_response(200)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    HTTPServer((host, port), Handler).serve_forever()


def cli() -> None:
    parser = argparse.ArgumentParser(
        prog="groundguard-server",
        description="Run a minimal GroundGuard HTTP fact gate.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config", help="Optional groundguard.yml or JSON config.")
    args = parser.parse_args()
    config = load_config(args.config) if args.config else None
    serve(host=args.host, port=args.port, config=config)


def _coerce_numeric(value: object) -> Decimal | str:
    try:
        return Decimal(str(value))
    except Exception:
        return str(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


if __name__ == "__main__":
    cli()
