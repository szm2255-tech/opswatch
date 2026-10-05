"""Simple service health checks (HTTP and TCP) using only the standard library."""

from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class CheckResult:
    target: str
    ok: bool
    detail: str
    latency_ms: float


def check_http(url: str, timeout: float = 5.0) -> CheckResult:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "opswatch/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ms = (time.perf_counter() - start) * 1000
            return CheckResult(url, 200 <= resp.status < 400, f"HTTP {resp.status}", ms)
    except urllib.error.HTTPError as exc:
        ms = (time.perf_counter() - start) * 1000
        return CheckResult(url, False, f"HTTP {exc.code}", ms)
    except Exception as exc:  # DNS failure, timeout, TLS error, refused...
        ms = (time.perf_counter() - start) * 1000
        return CheckResult(url, False, f"{type(exc).__name__}: {exc}", ms)


def check_tcp(host: str, port: int, timeout: float = 3.0) -> CheckResult:
    start = time.perf_counter()
    target = f"{host}:{port}"
    try:
        with socket.create_connection((host, port), timeout=timeout):
            ms = (time.perf_counter() - start) * 1000
            return CheckResult(target, True, "port open", ms)
    except Exception as exc:
        ms = (time.perf_counter() - start) * 1000
        return CheckResult(target, False, f"{type(exc).__name__}: {exc}", ms)


def check(target: str, timeout: float = 5.0) -> CheckResult:
    """Dispatch on target format: http(s)://... or host:port."""
    if target.startswith(("http://", "https://")):
        return check_http(target, timeout)
    host, _, port = target.rpartition(":")
    if not host or not port.isdigit():
        return CheckResult(target, False, "invalid target (use URL or host:port)", 0.0)
    return check_tcp(host, int(port), timeout)
