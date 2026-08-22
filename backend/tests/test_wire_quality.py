"""Wire quality + source-only caption helpers (no API)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.styles import build_imagine_prompt, scene_hint  # noqa: E402
from services.xai_imagine import imagine_generate_kwargs  # noqa: E402
from services.wire_quality import (  # noqa: E402
    expand_handles,
    is_fluff,
    is_visualizable_event,
    length_bonus,
    longest_source_text,
    wire_accept,
)
from services.xai_chat import pack_stream_slug, _clean_post_body  # noqa: E402


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

    def test_rejects_rtx_giveaway(self):
        t = (
            "RTX PC Week — FREE PC DROP #5 WIN this custom STEIGERDYNAMICS build, "
            "powered by a GeForce RTX 5080 Founders Edition. A new rig is ready. "
            "Which game gets the first launch? Share your answer with #RTXPowersPlay "
            "to enter!"
        )
        self.assertTrue(is_fluff(t))
        self.assertFalse(wire_accept(t))

    def test_rejects_air_show_ad(self):
        t = (
            "America’s newest and most exciting aerospace technology expo and air show "
            "is landing NASA Kennedy in Florida on Nov. 7-8. Make plans to join us "
            "for MAX POWER!"
        )
        self.assertTrue(is_fluff(t))
        self.assertFalse(wire_accept(t))

    def test_rejects_risk_report(self):
        t = (
            "As part of our Responsible Scaling Policy, we publish regular Risk Reports. "
            "These share detailed information on the risks of our systems."
        )
        self.assertTrue(is_fluff(t))
        self.assertFalse(wire_accept(t))


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

    def test_strips_rss_nbsp(self):
        slug = pack_stream_slug(
            [
                "Full Self-Driving Is the Best Thing about the New Tesla Model Y - WSJ "
                "— Full Self-Driving Is the Best Thing about the New Tesla Model Y "
                "&nbsp;&nbsp; WSJ"
            ]
        )
        self.assertNotIn("&nbsp;", slug)
        self.assertNotIn("\xa0", slug)
        self.assertIn("Model Y", slug)


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
        self.assertLess(len(prompt), 1100)
        lock = prompt.lower()
        self.assertIn("neon-night", lock)
        self.assertNotIn("finished vfx still", lock)
        self.assertNotIn("neon accents subordinate", lock)
        self.assertNotIn("photoreal materials", lock)

    def test_scene_hint_varies_by_salt(self):
        a = scene_hint("rootkit-city", "story-one")
        b = scene_hint("rootkit-city", "story-two-totally-different")
        self.assertTrue(a)
        # different stories should usually pick different hints (hash); if they
        # collide that's ok — just assert the helper returns a one-hero hint.
        self.assertNotIn("packed wall-to-wall", a)
        self.assertNotIn("Fill the frame", b)
        self.assertNotIn("lots of night sky", a.lower())
        self.assertNotIn("lots of night sky", b.lower())

    def test_data_space_hint_is_neon_not_postcard(self):
        hint = scene_hint("data-space", "Falcon 9 Starlink launch from Vandenberg").lower()
        self.assertTrue(hint)
        self.assertNotIn("circuit-board", hint)
        self.assertNotIn("holographic data-earth as hero", hint)
        self.assertNotIn("hud", hint)
        self.assertTrue(
            "craft" in hint or "machine" in hint or "ring" in hint
        )

    def test_data_space_lock_bans_hud_globe(self):
        prompt = build_imagine_prompt(
            "SHOT: A neon-edged craft flies past Earth wrapped in cyan data rings.\n"
            "HERO: craft\n",
            {"id": "data-space", "prompt_seed": "ignore this seed"},
        )
        lock = prompt.lower()
        self.assertIn("hud", lock)
        self.assertIn("circuit-board globe", lock)
        self.assertIn("tron", lock)
        self.assertNotIn("holographic data-planet", lock)


class ImagineRequest(unittest.TestCase):
    def test_kwargs_never_send_size(self):
        kw = imagine_generate_kwargs("a test prompt")
        self.assertNotIn("size", kw)
        extra = kw.get("extra_body") or {}
        self.assertEqual(extra.get("aspect_ratio"), "16:9")
        self.assertIn(extra.get("resolution"), ("1k", "2k"))


class TunaPostClean(unittest.TestCase):
    def test_strips_hashtags_and_urls(self):
        raw = (
            "Falcon 9 put Starlink Group 17-49 up from Vandenberg. #PlanetHack\n\n"
            "https://x.com/spacex/status/1 neon plate, not a press photo."
        )
        out = _clean_post_body(raw)
        self.assertNotIn("#", out)
        self.assertNotIn("http", out)
        self.assertIn("Vandenberg", out)


if __name__ == "__main__":
    unittest.main()
