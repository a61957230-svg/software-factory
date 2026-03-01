#!/usr/bin/env python3
"""Minimal status API service (stdlib only)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Any

START_MONO = time.monotonic()


def build_status(service: str = "alpha-status-api", version: str = "1.0.0") -> Dict[str, Any]:
    return {
        "service": service,
        "version": version,
        "status": "ok",
        "uptimeSec": round(time.monotonic() - START_MONO, 3),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/status":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return

        payload = json.dumps(build_status()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:  # keep output clean
        return


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), StatusHandler)
    print(f"status api listening on http://{host}:{port}/status")
    server.serve_forever()


if __name__ == "__main__":
    run()
