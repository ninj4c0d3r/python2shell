#!/usr/bin/env python3
"""Minimal two-stage Brotli target for the local lab."""

from __future__ import annotations
import json
import platform
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.metadata import version
from urllib.parse import urlsplit

import brotli

HOST = "0.0.0.0"
PORT = 8080
MAX_STAGE = 24 * 1024 * 1024
LAB_TOKEN = "python2shell-local-lab"


class Session:
    def __init__(self) -> None:
        # The trigger remains active while the OOB write targets the separate
        # victim. The victim is released only after trigger.process returns.
        self.victim = brotli.Decompressor()
        self.trigger = brotli.Decompressor()
        self.stage1_complete = False

    def stage1(self, body: bytes) -> None:
        if self.stage1_complete:
            raise ValueError("stage 1 was already processed")
        self.staged_output = self.trigger.process(body)
        self.stage1_complete = True

    def stage2(self, body: bytes) -> None:
        if not self.stage1_complete or self.trigger is None:
            raise ValueError("stage 1 is required")
        self.trigger.process(body)
        victim = self.victim
        self.victim = None
        del victim


SESSION = Session()


class Handler(BaseHTTPRequestHandler):
    server_version = "Python2ShellLab/3.1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} {fmt % args}", flush=True)

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return self.headers.get("X-Lab-Token", "") == LAB_TOKEN

    def _body(self) -> bytes:
        raw = self.headers.get("Content-Length")
        if raw is None:
            raise ValueError("Content-Length is required")
        length = int(raw)
        if length < 0 or length > MAX_STAGE:
            raise ValueError("body exceeds the lab limit")
        body = self.rfile.read(length)
        if len(body) != length:
            raise ValueError("incomplete request body")
        return body

    def do_GET(self) -> None:
        if urlsplit(self.path).path == "\x00":
            self._json(
                200,
                {"trigger": id(SESSION.trigger), "victim": id(SESSION.victim)},
            )
            return
        if urlsplit(self.path).path != "/prepare":
            self._json(404, {"error": "not found"})
            return
        self._json(
            200,
            {
                "token": LAB_TOKEN,
                "brotli": version("Brotli"),
                "python": platform.python_version(),
                "architecture": platform.machine(),
            },
        )

    def do_POST(self) -> None:
        if not self._authorized():
            self._json(403, {"error": "invalid lab token"})
            return
        path = urlsplit(self.path).path
        try:
            body = self._body()
            if path == "/upload":
                SESSION.stage1(body)
                self._json(200, {"accepted": True})
                return
            if path == "/commit":
                SESSION.stage2(body)
                self._json(200, {"released": True})
                return
            self._json(404, {"error": "not found"})
        except Exception as error:
            self._json(500, {"error": f"{type(error).__name__}: {error}"})


if __name__ == "__main__":
    if platform.machine() != "x86_64":
        raise SystemExit("this pinned lab requires Linux x86-64")
    if version("Brotli") != "1.2.0":
        raise SystemExit("this target requires the vulnerable Brotli 1.2.0 wheel")
    print(f"listening on {HOST}:{PORT}; vulnerable Brotli {version('Brotli')}", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
