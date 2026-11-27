"""Story → core style, older skins, Tesla shapes, and Space DataCenter."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import styles  # noqa: E402
from services.styles import (  # noqa: E402
    build_imagine_prompt,
    choose_story_core,
    core_for_story,
    search_lane_for_core,
    shape_kind,
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
            "data-space",
        )
        self.assertEqual(
            vehicle_kind("Starlink direct to cell adds another satellite pass."),
            "starlink",
        )
        self.assertEqual(
            core_for_story("SpaceX Dragon cargo ship splashes down off the coast."),
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
            [
                "data-space",
                "space-datacenter",
                "planet-core",
                "data-tunnel",
                "signal-cathedral",
                "rootkit-city",
            ],
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

    def test_falcon_prompt_is_the_real_first_stage(self) -> None:
        story = "Falcon 9 launches Starlink Group 10-17 from Vandenberg."
        got = style_for_story(story, random.Random(1))
        self.assertEqual(got["vehicle"], "falcon")
        prompt = build_imagine_prompt("SHOT: A neon rocket climbs past Earth.\n", got, story).lower()
        self.assertTrue(prompt.startswith("the hero is a real spacex falcon 9"))
        self.assertIn("octaweb", prompt)
        self.assertIn("nine merlin", prompt)
        self.assertIn("interstage", prompt)
        self.assertIn("no rounded nose cone", prompt)
        self.assertIn("no heat-shield tiles", prompt)
        self.assertIn("white paint stays white", prompt)

    def test_starlink_satellites_lead_the_data_space_plate(self) -> None:
        story = "Starlink direct to cell adds another satellite pass."
        got = style_for_story(story, recent=[])
        self.assertEqual(got["id"], "data-space")
        self.assertEqual(got["vehicle"], "starlink")
        prompt = build_imagine_prompt("SHOT: Objects over the night side of Earth.\n", got, story).lower()
        self.assertIn("starlink satellites", prompt)
        self.assertIn("solar wing", prompt)
        self.assertIn("not a user dish", prompt)
        self.assertNotIn("falcon 9 first stage", prompt)

    def test_version_walks_the_older_skins(self) -> None:
        story = "Anthropic drops a new model checkpoint."
        first = style_for_story(story, recent=[])
        self.assertEqual(first["version"], "core")
        second = style_for_story(story, recent=[{"id": "data-tunnel", "version": "core"}])
        self.assertEqual(second["version"], "pixel-run")
        third = style_for_story(story, recent=[{"id": "data-tunnel", "version": "pixel-run"}])
        self.assertEqual(third["version"], "weight-stream")
        fourth = style_for_story(story, recent=[{"id": "data-tunnel", "version": "weight-stream"}])
        self.assertEqual(fourth["version"], "clear")
        fifth = style_for_story(story, recent=[{"id": "data-tunnel", "version": "clear"}])
        self.assertEqual(fifth["version"], "core")
        prompt = build_imagine_prompt("SHOT: A ribbed metal tunnel.\n", second)
        self.assertIn("pixel", prompt.lower())

    def test_one_core_cannot_fill_the_wire(self) -> None:
        from services.events import _take_balanced

        rows = []
        for n in range(8):
            rows.append({"title": f"Tesla FSD v15 rollout note {n}", "published_at": f"2026-11-22T1{n}:00:00+00:00"})
        rows.append({
            "title": "Tesla plans Model Y without a steering wheel or pedals",
            "published_at": "2026-11-22T09:00:00+00:00",
        })
        kept = _take_balanced(rows, limit=5, per_core=2)
        cores = [core_for_story(row["title"]) for row in kept]
        self.assertEqual(len(kept), 5)
        self.assertIn("signal-cathedral", cores)

    def test_next_story_leaves_a_core_that_just_ran(self) -> None:
        texts = [
            "Anthropic releases a Claude checkpoint to early testers.",
            "NVIDIA releases a hotfix driver for Blackwell cards.",
            "SpaceX Dragon cargo ship splashes down off the coast.",
        ]
        self.assertEqual(choose_story_core(texts, ["data-tunnel", "data-tunnel"]), "rootkit-city")
        self.assertEqual(choose_story_core(texts[:1], ["data-tunnel"]), "data-tunnel")
        self.assertEqual(choose_story_core(texts, []), "data-tunnel")


    def test_clear_skin_is_added_beside_the_neon_lock(self) -> None:
        for sid in (
            "data-space",
            "space-datacenter",
            "planet-core",
            "data-tunnel",
            "signal-cathedral",
            "rootkit-city",
        ):
            self.assertIn("clear", styles.version_ids(sid))
            got = styles.get_style(sid, version="clear")
            prompt = build_imagine_prompt(
                "SHOT: void black neon-night acid-green poster.\n",
                got,
                "A headline that must not replace the clear plate.",
            )
            self.assertIn("finished VFX still", prompt)
            self.assertIn("Photoreal materials", prompt)
            self.assertNotIn("void black neon-night", prompt)
        neon = styles.get_style("data-tunnel", version="core")
        neon_prompt = build_imagine_prompt("SHOT: A ribbed metal tunnel of cyan light.\n", neon)
        self.assertIn("neon-night", neon_prompt)
        self.assertNotIn("finished VFX still", neon_prompt)

    def test_tesla_shapes_use_the_clear_plates(self) -> None:
        truck = "A Tesla tuner showed a lifted Cybertruck on massive tires."
        self.assertEqual(shape_kind(truck), "cybertruck")
        self.assertEqual(core_for_story(truck), "tesla-shape")
        first = style_for_story(truck, recent=[])
        self.assertEqual(first["story_core"], "tesla-shape")
        self.assertEqual(first["id"], "signal-cathedral")
        self.assertEqual(first["version"], "clear")
        self.assertEqual(first["shape"], "cybertruck")
        self.assertNotIn("vehicle", first)
        prompt = build_imagine_prompt("SHOT: A neon cathedral of ribs.\n", first, truck).lower()
        self.assertIn("cybertruck", prompt)
        self.assertIn("stainless", prompt)
        self.assertIn("finished vfx still", prompt)
        self.assertNotIn("neon-night", prompt)
        self.assertNotIn("neon cathedral", prompt)
        second = style_for_story(truck, recent=[{"id": "tesla-shape", "version": "signal-cathedral"}])
        self.assertEqual(second["id"], "data-space")
        third = style_for_story(truck, recent=[{"id": "tesla-shape", "version": "data-space"}])
        self.assertEqual(third["id"], "data-tunnel")
        fourth = style_for_story(truck, recent=[{"id": "tesla-shape", "version": "data-tunnel"}])
        self.assertEqual(fourth["id"], "rootkit-city")
        fifth = style_for_story(truck, recent=[{"id": "tesla-shape", "version": "rootkit-city"}])
        self.assertEqual(fifth["id"], "signal-cathedral")

    def test_cybercab_robot_and_cabin(self) -> None:
        cab = style_for_story("Tesla is adding Cybercabs by the hundreds in Texas.", recent=[])
        self.assertEqual(cab["shape"], "cybercab")
        cab_prompt = build_imagine_prompt("SHOT: ignore.\n", cab).lower()
        self.assertIn("cybercab", cab_prompt)
        self.assertIn("no steering wheel", cab_prompt)
        robot = style_for_story("Tesla Optimus robots start factory shifts.", recent=[])
        self.assertEqual(robot["shape"], "robot")
        robot_prompt = build_imagine_prompt("SHOT: ignore.\n", robot).lower()
        self.assertIn("optimus", robot_prompt)
        self.assertIn("carries a crate", robot_prompt)
        cabin = style_for_story("Tesla FSD v15 starts rolling out to early testers.", recent=[])
        self.assertEqual(cabin["shape"], "cabin")
        cabin_prompt = build_imagine_prompt("SHOT: ignore.\n", cabin).lower()
        self.assertIn("in-car view", cabin_prompt)
        self.assertIn("no driver", cabin_prompt)
        inside = style_for_story(
            "A look inside the Cybertruck cabin from the driver's view.",
            recent=[],
        )
        self.assertEqual(inside["shape"], "cabin")

    def test_space_datacenter_is_starlink_over_earth(self) -> None:
        story = "FCC approves 1 million SpaceX data centers in space."
        self.assertEqual(core_for_story(story), "space-datacenter")
        self.assertEqual(search_lane_for_core("space-datacenter"), "space")
        self.assertEqual(
            core_for_story("NVIDIA Blackwell Ultra ships into data centers."),
            "rootkit-city",
        )
        self.assertEqual(
            core_for_story("Starlink direct to cell adds another satellite pass."),
            "data-space",
        )
        got = style_for_story(story, recent=[])
        self.assertEqual(got["id"], "space-datacenter")
        self.assertEqual(got["version"], "core")
        prompt = build_imagine_prompt(
            "SHOT: A server building floats over Earth.\n",
            got,
            story,
        ).lower()
        self.assertTrue(prompt.startswith("the hero is starlink"))
        self.assertIn("solar wing", prompt)
        self.assertIn("earth", prompt)
        self.assertIn("not a server building", prompt)
        self.assertNotIn("falcon 9 first stage", prompt)

    def test_signal_cathedral_stays_a_readable_building(self) -> None:
        brief = (
            "SHOT: Wide 16:9 low angle gazes up a colossal signal cathedral nave of "
            "soaring angular metal-glass beams and dish vaults, void-black depths "
            "between them.\n"
            "HERO: ribs\n"
        )
        got = styles.get_style("signal-cathedral", version="core")
        prompt = build_imagine_prompt(brief, got).lower()
        self.assertIn("whole signal cathedral", prompt)
        self.assertIn("camera pulled back", prompt)
        self.assertNotIn("low angle gazes up", prompt)
        self.assertIn("whole building stays in frame", prompt)
        self.assertIn("wide view shows", prompt)

    def test_iridescent_is_a_held_material(self) -> None:
        styles.reload_styles()
        for sid in ("data-space", "signal-cathedral", "rootkit-city", "space-datacenter"):
            self.assertNotIn("iridescent", styles.version_ids(sid))
            self.assertNotEqual(styles.next_version(sid, "clear"), "iridescent")
            got = styles.get_style(sid, version="iridescent")
            self.assertEqual(got["version"], "iridescent")
            self.assertIn("thin-film", got["art_director_notes"].lower())
        falcon = styles.get_style("data-space", version="iridescent")
        falcon["vehicle"] = "falcon"
        prompt = build_imagine_prompt(
            "SHOT: A white Falcon 9 climbs past Earth.\n",
            falcon,
            "Falcon 9 launches Starlink Group 10-17 from Vandenberg.",
        ).lower()
        self.assertIn("falcon 9", prompt)
        self.assertIn("white cylinder", prompt)
        self.assertIn("thin-film", prompt)
        self.assertIn("polished metal", prompt)
        self.assertIn("not a silk sheet", prompt)
        self.assertIn("not a painted nebula", prompt)
        self.assertIn("not an abstract blob", prompt)


if __name__ == "__main__":
    unittest.main()
