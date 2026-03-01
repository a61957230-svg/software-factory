#!/usr/bin/env python3
"""Append validated factory audit events to JSONL logs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "audit" / "event-schema.json"
EVENTS_DIR = BASE_DIR / "audit" / "events"


def _load_schema_required() -> tuple[list[str], set[str]]:
    schema = json.loads(SCHEMA_PATH.read_text())
    required = schema.get("required", [])
    status_enum = set(schema.get("properties", {}).get("status", {}).get("enum", []))
    return required, status_enum


def validate_event(event: Dict[str, Any]) -> None:
    required, status_enum = _load_schema_required()
    missing = [k for k in required if k not in event]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    if event.get("status") not in status_enum:
        raise ValueError(f"Invalid status: {event.get('status')} (allowed: {sorted(status_enum)})")

    ts = event.get("timestamp", "")
    if not isinstance(ts, str) or "T" not in ts:
        raise ValueError("timestamp must be ISO datetime string")


def append_event(event: Dict[str, Any]) -> Path:
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = EVENTS_DIR / f"{day}.jsonl"
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a validated audit event")
    parser.add_argument("--event", required=True, help="JSON object string")
    args = parser.parse_args()

    event = json.loads(args.event)
    validate_event(event)
    out = append_event(event)
    print(f"OK: appended audit event -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
