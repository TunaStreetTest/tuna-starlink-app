"""Plate URL on the X post, and a two-hour trigger that is not the old peak window."""

from __future__ import annotations

import re
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import scheduler  # noqa: E402
from services.x_publish import (  # noqa: E402
    build_main_post,
    clip_keeping_plate,
    plate_url_for,
    tweet_bodies,
)

TZ = ZoneInfo("America/New_York")
SHORT = re.compile(r"^https://planethack\.space/p/[0-9A-Za-z]{7}$")


class PlatePostText(unittest.TestCase):
    def test_known_meta_keeps_the_url_on_its_own_line(self) -> None:
        text = build_main_post(
            {
                "run_id": "20261112_125109",
                "caption": "Starship stacked on the pad. #notag The dish heard it first.",
            }
        )
        url = plate_url_for("20261112_125109")
        self.assertIsNotNone(url)
        assert url is not None
        self.assertRegex(url, SHORT)
        self.assertNotIn("20261112", url)
        self.assertEqual(url, plate_url_for("20261112_125109"))
        self.assertIn(url, text)
        self.assertTrue(text.endswith(url))
        self.assertNotIn("#notag", text)
        caption, _, link = text.rpartition("\n")
        self.assertEqual(link, url)
        self.assertNotIn("http", caption)
        bodies = tweet_bodies(text)
        self.assertGreaterEqual(len(bodies), 1)
        for body in bodies:
            self.assertIn(url, body)

    def test_280_fallback_keeps_the_full_url(self) -> None:
        caption = "Starship stacked on the pad and the booster walked out. " * 40
        text = build_main_post({"run_id": "abc_DEF-1", "caption": caption})
        url = plate_url_for("abc_DEF-1")
        self.assertIsNotNone(url)
        assert url is not None
        self.assertRegex(url, SHORT)
        self.assertIn(url, text)
        self.assertGreater(len(text), 280)
        bodies = tweet_bodies(text)
        self.assertGreaterEqual(len(bodies), 2)
        short = bodies[-1]
        self.assertLessEqual(len(short), 280)
        self.assertTrue(short.endswith(url))
        self.assertIn(url, clip_keeping_plate(text, 280))

    def test_bad_run_id_adds_no_link(self) -> None:
        self.assertIsNone(plate_url_for("bad id"))
        text = build_main_post({"run_id": "bad id", "caption": "Just the caption."})
        self.assertNotIn("planethack.space", text)
        self.assertIn("Just the caption.", text)


class HourlySchedule(unittest.TestCase):
    def setUp(self) -> None:
        scheduler._fired_hour = None

    def test_next_fire_is_the_next_even_hour_outside_the_old_peak(self) -> None:
        # 15:30 Eastern is outside the old 19:00–22:00 window. Next plate is 16:00.
        now = datetime(2026, 11, 15, 15, 30, tzinfo=TZ)
        nxt = scheduler.plate_trigger(TZ).get_next_fire_time(None, now)
        self.assertIsNotNone(nxt)
        assert nxt is not None
        self.assertEqual(nxt.hour, 16)
        self.assertEqual(nxt.minute, 0)
        self.assertEqual(nxt.tzinfo, TZ)

    def test_an_even_hour_does_not_fire_again_on_the_odd_hour(self) -> None:
        now = datetime(2026, 11, 15, 16, 10, tzinfo=TZ)
        nxt = scheduler.plate_trigger(TZ).get_next_fire_time(None, now)
        assert nxt is not None
        self.assertEqual((nxt.hour, nxt.minute), (18, 0))

    def test_overnight_hour_still_fires(self) -> None:
        now = datetime(2026, 11, 15, 3, 10, tzinfo=TZ)
        nxt = scheduler.plate_trigger(TZ).get_next_fire_time(None, now)
        assert nxt is not None
        self.assertEqual((nxt.hour, nxt.minute), (4, 0))

    def test_one_claim_per_clock_hour(self) -> None:
        self.assertTrue(scheduler.claim_hour("2026-11-15T14"))
        self.assertFalse(scheduler.claim_hour("2026-11-15T14"))
        self.assertTrue(scheduler.claim_hour("2026-11-15T15"))

    def test_empty_wire_is_a_wait(self) -> None:
        self.assertTrue(scheduler.wire_has_nothing(RuntimeError("no event worth a plate — wire empty")))
        self.assertFalse(scheduler.wire_has_nothing(RuntimeError("imagine timeout")))


if __name__ == "__main__":
    unittest.main()
