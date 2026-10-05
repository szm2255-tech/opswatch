"""Log parsing and incident-style analysis."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL)\s+"
    r"(?P<service>[\w.\-]+)\s+(?P<message>.*)$"
)

ERROR_LEVELS = {"ERROR", "CRITICAL"}


@dataclass
class Entry:
    ts: datetime
    level: str
    service: str
    message: str


def parse_line(line: str) -> Optional[Entry]:
    """Parse one log line, returning None if it is not in the expected format."""
    m = LINE_RE.match(line.strip())
    if not m:
        return None
    level = m["level"].replace("WARNING", "WARN")
    ts = datetime.fromisoformat(m["ts"].replace(" ", "T"))
    return Entry(ts, level, m["service"], m["message"])


def normalise(message: str) -> str:
    """Collapse variable parts (IPs, hex ids, numbers) so similar errors group together."""
    message = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<ip>", message)
    message = re.sub(r"\b[0-9a-f]{8,}\b", "<id>", message, flags=re.I)
    message = re.sub(r"\d+", "<n>", message)
    return message


@dataclass
class Report:
    total: int = 0
    malformed: int = 0
    first: Optional[datetime] = None
    last: Optional[datetime] = None
    by_level: Counter = field(default_factory=Counter)
    errors_by_service: Counter = field(default_factory=Counter)
    top_errors: list = field(default_factory=list)  # (message, count)
    spikes: list = field(default_factory=list)  # (minute string, count)

    @property
    def error_count(self) -> int:
        return sum(self.by_level[lvl] for lvl in ERROR_LEVELS)

    @property
    def severity(self) -> str:
        """Rough triage suggestion, a starting point for the analyst, not a verdict."""
        if self.by_level["CRITICAL"] or len(self.spikes) >= 2:
            return "P1 - Critical"
        if self.spikes or self.error_count >= 10:
            return "P2 - High"
        if self.error_count:
            return "P3 - Medium"
        return "P4 - Low"

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "malformed": self.malformed,
            "first": self.first.isoformat() if self.first else None,
            "last": self.last.isoformat() if self.last else None,
            "by_level": dict(self.by_level),
            "errors_by_service": dict(self.errors_by_service),
            "top_errors": self.top_errors,
            "spikes": self.spikes,
            "severity": self.severity,
        }


def analyze(lines: Iterable[str], spike_threshold: int = 5, top_n: int = 5) -> Report:
    """Summarise log lines: level counts, noisiest services, top errors, error spikes."""
    report = Report()
    error_msgs: Counter = Counter()
    per_minute: Counter = Counter()

    for raw in lines:
        if not raw.strip():
            continue
        entry = parse_line(raw)
        if entry is None:
            report.malformed += 1
            continue
        report.total += 1
        report.by_level[entry.level] += 1
        report.first = min(report.first, entry.ts) if report.first else entry.ts
        report.last = max(report.last, entry.ts) if report.last else entry.ts
        if entry.level in ERROR_LEVELS:
            report.errors_by_service[entry.service] += 1
            error_msgs[f"{entry.service}: {normalise(entry.message)}"] += 1
            per_minute[entry.ts.strftime("%Y-%m-%d %H:%M")] += 1

    report.top_errors = error_msgs.most_common(top_n)
    report.spikes = sorted(
        (minute, n) for minute, n in per_minute.items() if n >= spike_threshold
    )
    return report
