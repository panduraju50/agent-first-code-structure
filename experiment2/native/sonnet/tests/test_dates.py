import unittest
from datetime import datetime, timedelta, timezone

from taskly.dates import from_iso8601, relative_from_now, to_human, to_iso8601, utc_now


class TestUtcNow(unittest.TestCase):
    def test_returns_timezone_aware_utc(self):
        now = utc_now()
        self.assertIsNotNone(now.tzinfo)
        self.assertEqual(now.utcoffset(), timedelta(0))


class TestIso8601RoundTrip(unittest.TestCase):
    def test_roundtrip_preserves_millisecond_precision(self):
        dt = datetime(2026, 8, 26, 10, 15, 30, 123000, tzinfo=timezone.utc)
        s = to_iso8601(dt)
        self.assertEqual(s, "2026-08-26T10:15:30.123Z")
        self.assertEqual(from_iso8601(s), dt)

    def test_naive_datetime_treated_as_utc(self):
        dt = datetime(2026, 1, 1, 0, 0, 0)
        s = to_iso8601(dt)
        self.assertTrue(s.startswith("2026-01-01T00:00:00"))

    def test_non_utc_timezone_converted(self):
        tz = timezone(timedelta(hours=5))
        dt = datetime(2026, 1, 1, 5, 0, 0, tzinfo=tz)  # == 2026-01-01T00:00:00Z
        s = to_iso8601(dt)
        self.assertTrue(s.startswith("2026-01-01T00:00:00"))

    def test_from_iso8601_rejects_missing_z(self):
        with self.assertRaises(ValueError):
            from_iso8601("2026-01-01T00:00:00.000")

    def test_from_iso8601_rejects_non_string(self):
        with self.assertRaises(ValueError):
            from_iso8601(12345)


class TestToHuman(unittest.TestCase):
    def test_format(self):
        dt = datetime(2026, 8, 26, 10, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(to_human(dt), "Aug 26, 2026 10:15 UTC")


class TestRelativeFromNow(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)

    def test_just_now(self):
        dt = self.now - timedelta(seconds=5)
        self.assertEqual(relative_from_now(dt, now=self.now), "just now")

    def test_minutes_ago(self):
        dt = self.now - timedelta(minutes=5)
        self.assertEqual(relative_from_now(dt, now=self.now), "5m ago")

    def test_hours_ago(self):
        dt = self.now - timedelta(hours=3)
        self.assertEqual(relative_from_now(dt, now=self.now), "3h ago")

    def test_days_ago(self):
        dt = self.now - timedelta(days=2)
        self.assertEqual(relative_from_now(dt, now=self.now), "2d ago")

    def test_future_reports_in_the_future(self):
        dt = self.now + timedelta(minutes=5)
        self.assertEqual(relative_from_now(dt, now=self.now), "in the future")

    def test_boundary_exactly_now(self):
        self.assertEqual(relative_from_now(self.now, now=self.now), "just now")


if __name__ == "__main__":
    unittest.main()
