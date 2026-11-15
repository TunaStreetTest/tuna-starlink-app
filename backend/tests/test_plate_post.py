"""Plate URL on the X post, and an hourly trigger that is not the old peak window."""

from __future__ import annotations

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

PLATE = "https://planethack.space/p/20261112_125109"
TZ = ZoneInfo("America/New_York")


class PlatePostText(unittest.TestCase):
    def test_known_meta_keeps_the_url_on_its_own_line(self) -> None:
        text = build_main_post(
            {
                "run_id": "20261112_125109",
                "caption": "Starship stacked on the pad. #notag The dish heard it first.",
            }
        )
        self.assertIn(PLATE, text)
        self.assertTrue(text.endswith(PLATE))
        self.assertNotIn("#notag", text)
        caption, _, link = text.rpartition("\n")
        self.assertEqual(link, PLATE)
        self.assertNotIn("http", caption)
        bodies = tweet_bodies(text)
        self.assertGreaterEqual(len(bodies), 1)
        for body in bodies:
            self.assertIn(PLATE, body)

    def test_280_fallback_keeps_the_full_url(self) -> None:
        caption = "Starship stacked on the pad and the booster walked out. " * 40
        text = build_main_post({"run_id": "abc_DEF-1", "caption": caption})
        url = "https://planethack.space/p/abc_DEF-1"
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

    def test_next_fire_is_the_next_clock_hour_outside_the_old_peak(self) -> None:
        # 15:30 Eastern is outside the old 19:00–22:00 window.
        now = datetime(2026, 11, 15, 15, 30, tzinfo=TZ)
        nxt = scheduler.hourly_trigger(TZ).get_next_fire_time(None, now)
        self.assertIsNotNone(nxt)
        assert nxt is not None
        self.assertEqual(nxt.hour, 16)
        self.assertEqual(nxt.minute, 0)
        self.assertEqual(nxt.tzinfo, TZ)

    def test_overnight_hour_still_fires(self) -> None:
        now = datetime(2026, 11, 15, 3, 10, tzinfo=TZ)
        nxt = scheduler.hourly_trigger(TZ).get_next_fire_time(None, now)
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
