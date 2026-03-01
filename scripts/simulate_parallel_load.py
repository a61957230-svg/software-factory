#!/usr/bin/env python3
"""Run a lightweight 3-project parallel simulation and store evidence."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TASKS = [
    ("lead-project-alpha", "SIM_ALPHA_OK"),
    ("lead-project-beta", "SIM_BETA_OK"),
    ("lead-project-gamma", "SIM_GAMMA_OK"),
    ("router", "SIM_ROUTER_OK"),
]


def spawn(agent_id: str, expected_token: str) -> dict:
    prompt = f"Reply with exactly {expected_token}"
    cmd = [
        "openclaw",
        "agent",
        "--agent",
        agent_id,
        "--message",
        prompt,
        "--json",
        "--timeout",
        "120",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    raw = (p.stdout or "") + (p.stderr or "")
    parsed = None
    reply_text = ""
    if p.returncode == 0:
        try:
            parsed = json.loads(p.stdout)
            payloads = parsed.get("result", {}).get("payloads", [])
            if payloads:
                reply_text = (payloads[0].get("text") or "").strip()
        except Exception:
            pass
    return {
        "agentId": agent_id,
        "expected": expected_token,
        "exitCode": p.returncode,
        "reply": reply_text,
        "ok": p.returncode == 0 and reply_text == expected_token,
        "output": raw[-2500:],
    }


def main() -> int:
    started = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(spawn, a, t) for a, t in TASKS]
        for fut in as_completed(futs):
            results.append(fut.result())

    payload = {
        "startedAt": started,
        "finishedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "results": sorted(results, key=lambda x: x["agentId"]),
    }

    out = REPORTS_DIR / "parallel-sim.latest.json"
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))

    return 0 if all(r["ok"] for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
