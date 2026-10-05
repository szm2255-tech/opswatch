"""Generate a ticket note from a log analysis."""

from __future__ import annotations

import re

from .logs import Report

TICKET_RE = re.compile(r"^[A-Za-z]{2,10}-?\d{1,10}$")  # e.g. INC12345, OPS-482


def validate_ticket(ticket: str) -> str:
    ticket = ticket.strip()
    if not TICKET_RE.match(ticket):
        raise ValueError(f"'{ticket}' does not look like a ticket number (e.g. INC12345, OPS-482)")
    return ticket.upper()


def render_note(report: Report, ticket: str, summary: str = "") -> str:
    """Return a markdown ticket note. The ticket number is always included."""
    ticket = validate_ticket(ticket)
    lines = [f"## Ticket {ticket}: log analysis", ""]
    if summary:
        lines += [f"**Reported issue:** {summary}", ""]
    window = (
        f"{report.first:%Y-%m-%d %H:%M} to {report.last:%Y-%m-%d %H:%M}"
        if report.first and report.last
        else "n/a"
    )
    lines += [
        f"**Suggested priority:** {report.severity}",
        f"**Window analysed:** {window}",
        f"**Lines parsed:** {report.total} ({report.malformed} unparseable)",
        f"**Errors:** {report.error_count}",
        "",
    ]
    if report.errors_by_service:
        lines.append("### Errors by service")
        lines += [f"- {svc}: {n}" for svc, n in report.errors_by_service.most_common()]
        lines.append("")
    if report.top_errors:
        lines.append("### Most frequent errors")
        lines += [f"- ({n}x) {msg}" for msg, n in report.top_errors]
        lines.append("")
    if report.spikes:
        lines.append("### Error spikes (per minute)")
        lines += [f"- {minute}: {n} errors" for minute, n in report.spikes]
        lines.append("")
    lines += [
        "### Next steps",
        f"- [ ] Confirm impact with the service owner and update {ticket}",
        "- [ ] Check recent deployments/config changes around the first spike",
        "- [ ] Escalate per runbook if priority is P1/P2",
    ]
    return "\n".join(lines) + "\n"
