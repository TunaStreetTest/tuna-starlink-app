"""Story → core style, and older skins as versions of the five cores."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import styles  # noqa: E402
from services.styles import (  # noqa: E402
    build_imagine_prompt,
    core_for_story,
    search_lane_for_core,
    style_for_story,
    vehicle_kind,
)


class StoryRoutes(unittest.TestCase):
    def test_vehicle_beats_starlink_and_names_the_ship(self) -> None:
        falcon = "Falcon 9 launches Starlink Group 10-17 from Vandenberg."
        starship = "SpaceX Starship stacked at Starbase for the next flight."
        self.assertEqual(core_for_story(falcon), "data-space")
        self.assertEqual(vehicle_kind(falcon), "falcon")
        self.assertEqual(core_for_story(starship), "data-space")
        self.assertEqual(vehicle_kind(starship), "starship")
        self.assertEqual(search_lane_for_core("data-space"), "space")

    def test_other_subjects(self) -> None:
        self.assertEqual(
            core_for_story("Starlink direct to cell adds another satellite pass."),
            "planet-core",
        )
        self.assertEqual(
            core_for_story("NVIDIA Blackwell Ultra ships into data centers."),
            "rootkit-city",
        )
        self.assertEqual(
            core_for_story("Anthropic releases a new Claude model."),
            "data-tunnel",
        )
        self.assertEqual(
            core_for_story("Tesla recalls a door handle on the sedan."),
            "signal-cathedral",
        )
        self.assertIsNone(search_lane_for_core("signal-cathedral"))

    def test_openai_launch_is_ai_not_space(self) -> None:
        self.assertEqual(core_for_story("OpenAI launches GPT-5."), "data-tunnel")

    def test_five_cores_and_their_versions(self) -> None:
        styles.reload_styles()
        listed = [item["id"] for item in styles.list_styles()]
        self.assertEqual(
            listed,
            ["data-space", "planet-core", "data-tunnel", "signal-cathedral", "rootkit-city"],
        )
        for sid in listed:
            ids = styles.version_ids(sid)
            self.assertGreaterEqual(len(ids), 3)
            self.assertEqual(ids[0], "core")
            for vid in ids:
                got = styles.get_style(sid, version=vid)
                self.assertEqual(got["id"], sid)
                self.assertEqual(got["label"], styles.get_style(sid)["label"])
                self.assertEqual(got["version"], vid)
                self.assertGreater(len(got["prompt_seed"]), 40)

    def test_version_stays_inside_the_core(self) -> None:
        rng = random.Random(0)
        for _ in range(30):
            got = style_for_story("Anthropic drops a new model checkpoint.", rng)
            self.assertEqual(got["id"], "data-tunnel")
            self.assertIn(got["version"], styles.version_ids("data-tunnel"))
            self.assertNotIn("vehicle", got)

    def test_starship_prompt_leads_with_the_real_ship(self) -> None:
        story = "SpaceX Starship stacked at Starbase for flight 11."
        got = style_for_story(story, random.Random(1))
        prompt = build_imagine_prompt(
            "SHOT: A neon craft flies past Earth wrapped in cyan rings.\nHERO: craft\n",
            got,
            story,
        ).lower()
        self.assertTrue(prompt.startswith("the hero is spacex starship"))
        self.assertIn("body flaps", prompt)
        self.assertIn("stainless-steel", prompt)
        self.assertNotIn("machine-craft", prompt)
        self.assertIn("not a generic spacecraft", prompt)


if __name__ == "__main__":
    unittest.main()
