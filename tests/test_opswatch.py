import unittest

from opswatch.health import check
from opswatch.logs import analyze, normalise, parse_line
from opswatch.ticket import render_note, validate_ticket


def make_lines(n_errors_per_minute=6, minutes=1):
    out = []
    for m in range(minutes):
        for s in range(n_errors_per_minute):
            out.append(f"2026-10-05 09:{m:02d}:{s:02d} ERROR api Timeout after {100 + s}ms")
    return out


class ParseTests(unittest.TestCase):
    def test_parse_valid_line(self):
        e = parse_line("2026-10-05 09:12:01 ERROR payment-api boom")
        self.assertEqual((e.level, e.service, e.message), ("ERROR", "payment-api", "boom"))

    def test_parse_invalid_line(self):
        self.assertIsNone(parse_line("garbage"))

    def test_warning_alias(self):
        self.assertEqual(parse_line("2026-10-05 09:12:01 WARNING x y").level, "WARN")

    def test_normalise_groups_numbers_and_ips(self):
        self.assertEqual(
            normalise("connect 10.0.0.5:5432 after 300ms"), "connect <ip>:<n> after <n>ms"
        )


class AnalyzeTests(unittest.TestCase):
    def test_spike_detected_and_errors_grouped(self):
        r = analyze(make_lines(6) + ["not a log line"], spike_threshold=5)
        self.assertEqual(r.error_count, 6)
        self.assertEqual(r.malformed, 1)
        self.assertEqual(len(r.spikes), 1)
        self.assertEqual(r.top_errors[0][1], 6)  # all six collapse to one message

    def test_no_errors_is_low_priority(self):
        r = analyze(["2026-10-05 09:00:00 INFO web ok"])
        self.assertEqual(r.severity, "P4 - Low")

    def test_critical_is_p1(self):
        r = analyze(["2026-10-05 09:00:00 CRITICAL db down"])
        self.assertTrue(r.severity.startswith("P1"))


class TicketTests(unittest.TestCase):
    def test_note_contains_ticket_number(self):
        note = render_note(analyze(make_lines()), "inc12345", "Payments failing")
        self.assertIn("INC12345", note)
        self.assertIn("Payments failing", note)

    def test_invalid_ticket_rejected(self):
        with self.assertRaises(ValueError):
            validate_ticket("hello world")


class HealthTests(unittest.TestCase):
    def test_invalid_target(self):
        self.assertFalse(check("nonsense").ok)

    def test_closed_port_fails(self):
        self.assertFalse(check("127.0.0.1:9", timeout=1).ok)


if __name__ == "__main__":
    unittest.main()
