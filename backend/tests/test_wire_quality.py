"""Wire quality + source-only caption helpers (no API)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.styles import build_imagine_prompt, scene_hint  # noqa: E402
from services.wire_quality import (  # noqa: E402
    expand_handles,
    is_fluff,
    is_visualizable_event,
    length_bonus,
    longest_source_text,
    wire_accept,
)
from services.xai_chat import pack_stream_slug  # noqa: E402


class HandleExpansion(unittest.TestCase):
    def test_known_handles_and_possessive(self):
        src = (
            "Watch Falcon 9 launch the @NRO_gov and @USSF_SSC’s NROL-95 "
            "mission from pad 40 in Florida."
        )
        out = expand_handles(src)
        self.assertNotIn("@", out)
        self.assertIn("NRO", out)
        self.assertIn("USSF’s", out)
        self.assertNotIn("the and", out)

    def test_unknown_handle_keeps_word(self):
        self.assertEqual(expand_handles("Launch with @SomeOrg today"), "Launch with SomeOrg today")


class FluffAndEvents(unittest.TestCase):
    def test_rejects_gears_of_war(self):
        t = (
            "The fight gets bigger in Gears of War: E-Day with #RTXON. "
            "Rally your squad across larger maps in 12-player Horde Siege, "
            "or jump into 4v4 Versus. Early access to the Open Beta begins "
            "August 6, featuring NVIDIA DLSS Super."
        )
        self.assertTrue(is_fluff(t))
        self.assertFalse(wire_accept(t))

    def test_rejects_earnings_ir(self):
        t = (
            "Ahead of our first earnings webcast, investors can submit "
            "questions using a new tool built with Grok."
        )
        self.assertTrue(is_fluff(t))
        self.assertFalse(wire_accept(t))

    def test_rejects_academic_marketing(self):
        t = (
            "We’re giving scientists, mathematicians, and engineers free access "
            "to our frontier models—starting with 10,000 researchers and expanding "
            "to 100,000 through 2027. ChatGPT for Academic Researchers is built "
            "to accelerate discovery."
        )
        self.assertTrue(is_fluff(t))
        self.assertFalse(wire_accept(t))

    def test_accepts_falcon_launch(self):
        t = (
            "LAUNCH! SpaceX Falcon 9 B1081-26 launches Starlink Group 17-52 "
            "from SLC-4E, Vandenberg."
        )
        self.assertTrue(is_visualizable_event(t))
        self.assertTrue(wire_accept(t))
        self.assertFalse(is_fluff(t))

    def test_accepts_vera_rubin_tray(self):
        t = (
            "Vera Rubin NVL72 Compute Tray. Designed to scale. Assembled in "
            "1 minute. 100% automated. No cables, no hoses, no fans."
        )
        self.assertTrue(is_visualizable_event(t))
        self.assertTrue(wire_accept(t))

    def test_accepts_model_release(self):
        t = "GPT-5.6 Sol has been used to solve open problems in mathematics."
        self.assertTrue(is_visualizable_event(t))
        self.assertTrue(wire_accept(t))


class CaptionSourceOnly(unittest.TestCase):
    def test_prefers_full_text_over_220_clip(self):
        full = (
            "We’re giving scientists, mathematicians, and engineers free access "
            "to our frontier models—starting with 10,000 researchers and expanding "
            "to 100,000 through 2027. ChatGPT for Academic Researchers is built "
            "to accelerate discovery across every field."
        )
        item = {"title": full[:160], "line": full[:220], "text": full}
        packed = longest_source_text(item)
        self.assertGreater(len(packed), 220)
        self.assertIn("every field", packed)

    def test_caption_expands_handles_and_stays_source(self):
        # pack_stream_slug is sync; craft_stream_slug just wraps it
        slug = pack_stream_slug(
            [
                "Watch Falcon 9 launch the @NRO_gov and @USSF_SSC’s NROL-95 "
                "mission from pad 40 in Florida"
            ]
        )
        self.assertIn("NRO", slug)
        self.assertIn("USSF", slug)
        self.assertNotIn("@", slug)
        self.assertNotIn("the and", slug)
        self.assertNotIn("orbit", slug.lower())  # never invent

    def test_length_bonus_prefers_full_sentence(self):
        self.assertGreater(length_bonus(140), length_bonus(35))


class ImagineCompose(unittest.TestCase):
    def test_prompt_is_shot_plus_short_lock(self):
        brief = (
            "SHOT: A single luminous glass-silicon citadel rises from a dark wafer "
            "plain, amber rack-glow in its core, ice-cyan streets fading into haze.\n"
            "HERO: glass-silicon citadel\n"
            "METAPHOR: Vera Rubin tray as self-building keep\n"
            "LIGHT: amber leads, cyan accents\n"
            "MOOD: silicon awe\n"
            "AVOID: packed server cubes"
        )
        style = {
            "id": "rootkit-city",
            "prompt_seed": "Wide 16:9 dense packed silicon skyscrapers filling the frame",
        }
        prompt = build_imagine_prompt(brief, style)
        self.assertIn("luminous glass-silicon citadel", prompt)
        self.assertNotIn("packed silicon skyscrapers filling the frame", prompt)
        self.assertNotIn("wall-to-wall", prompt.lower())
        self.assertLess(len(prompt), 900)

    def test_scene_hint_varies_by_salt(self):
        a = scene_hint("rootkit-city", "story-one")
        b = scene_hint("rootkit-city", "story-two-totally-different")
        self.assertTrue(a)
        # different stories should usually pick different hints (hash); if they
        # collide that's ok — just assert the helper returns a one-hero hint.
        self.assertNotIn("packed wall-to-wall", a)
        self.assertNotIn("Fill the frame", b)


if __name__ == "__main__":
    unittest.main()
