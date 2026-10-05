"""Command line interface: opswatch analyze | check | ticket"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .health import check
from .logs import analyze
from .ticket import render_note


def _read(path: str):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.readlines()


def cmd_analyze(args) -> int:
    report = analyze(_read(args.logfile), spike_threshold=args.threshold)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0
    print(f"Severity suggestion: {report.severity}")
    print(f"Lines: {report.total} parsed, {report.malformed} unparseable")
    print("Levels:", ", ".join(f"{k}={v}" for k, v in sorted(report.by_level.items())))
    if report.errors_by_service:
        print("Errors by service:")
        for svc, n in report.errors_by_service.most_common():
            print(f"  {svc:<20} {n}")
    if report.top_errors:
        print("Top errors:")
        for msg, n in report.top_errors:
            print(f"  {n:>3}x {msg}")
    if report.spikes:
        print(f"Spikes (>= {args.threshold} errors/min):")
        for minute, n in report.spikes:
            print(f"  {minute}  {n} errors")
    return 0


def cmd_check(args) -> int:
    failed = 0
    for target in args.targets:
        r = check(target, args.timeout)
        status = "OK  " if r.ok else "FAIL"
        print(f"[{status}] {r.target:<40} {r.detail} ({r.latency_ms:.0f} ms)")
        failed += not r.ok
    return 1 if failed else 0


def cmd_ticket(args) -> int:
    report = analyze(_read(args.logfile), spike_threshold=args.threshold)
    try:
        note = render_note(report, args.ticket, args.summary)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(note)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="opswatch", description="Toolkit for DevOps support analysts")
    p.add_argument("--version", action="version", version=f"opswatch {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="summarise a log file")
    a.add_argument("logfile")
    a.add_argument("--threshold", type=int, default=5, help="errors/min that count as a spike")
    a.add_argument("--json", action="store_true", help="machine-readable output")
    a.set_defaults(func=cmd_analyze)

    c = sub.add_parser("check", help="health-check URLs or host:port targets")
    c.add_argument("targets", nargs="+")
    c.add_argument("--timeout", type=float, default=5.0)
    c.set_defaults(func=cmd_check)

    t = sub.add_parser("ticket", help="generate a ticket note from a log file")
    t.add_argument("logfile")
    t.add_argument("--ticket", required=True, help="ticket number, e.g. INC12345")
    t.add_argument("--summary", default="", help="one-line description of the reported issue")
    t.add_argument("--threshold", type=int, default=5)
    t.set_defaults(func=cmd_ticket)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
