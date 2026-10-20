"""Fixture checks for the public feed whitelist. Does not read the live gallery."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from PIL import Image


def load_export():
    path = Path(__file__).resolve().parent / "export_public_feed.py"
    spec = importlib.util.spec_from_file_location("export_public_feed", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load export_public_feed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


export = load_export()


def write_run(folder: Path, meta: dict, image: bool = True) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    if image:
        Image.new("RGB", (32, 16), (20, 200, 180)).save(folder / "art.png")


class ExportPublicFeedTest(unittest.TestCase):
    def test_whitelist_and_order(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            art = root / "art"
            out = root / "out"
            write_run(
                art / "older_run",
                {
                    "run_id": "older_run",
                    "status": "complete",
                    "dry_run": False,
                    "created_at": "2026-07-01T00:00:00+00:00",
                    "caption": "Older caption line",
                    "art_prompt": "PROMPT_SENTINEL_XYZZY",
                    "events_tap": {"primary_title": "Older headline", "path": "/secret/art"},
                },
            )
            write_run(
                art / "newer_run",
                {
                    "status": "complete",
                    "created_at": "2026-10-19T23:35:48+00:00",
                    "caption": "Newest caption",
                    "events": "- fallback headline",
                    "x_url": "https://x.com/tunastarlink/status/1",
                    "art_brief": "PROMPT_SENTINEL_XYZZY",
                },
            )
            write_run(
                art / "dry_run",
                {"status": "complete", "dry_run": True, "created_at": "2026-10-20T00:00:00+00:00"},
            )
            write_run(
                art / "failed_run",
                {"status": "failed", "created_at": "2026-10-20T00:00:00+00:00"},
                image=False,
            )
            write_run(
                art / "experiments" / "hidden_run",
                {"status": "complete", "created_at": "2026-10-20T00:00:00+00:00", "caption": "nope"},
            )
            write_run(
                art / "bad run",
                {"status": "complete", "created_at": "2026-10-20T00:00:00+00:00"},
            )

            result = export.export_feed(art, out, width=16)
            self.assertEqual(result["count"], 2)
            feed = json.loads((out / "feed.json").read_text(encoding="utf-8"))
            blob = (out / "feed.json").read_text(encoding="utf-8")
            self.assertNotIn("PROMPT_SENTINEL_XYZZY", blob)
            self.assertNotIn("/secret/art", blob)
            self.assertNotIn("art_prompt", blob)
            self.assertEqual([post["id"] for post in feed["posts"]], ["newer_run", "older_run"])
            self.assertEqual(feed["posts"][0]["x_url"], "https://x.com/tunastarlink/status/1")
            self.assertNotIn("x_url", feed["posts"][1])
            self.assertEqual(feed["posts"][0]["headline"], "fallback headline")
            self.assertEqual(feed["posts"][1]["headline"], "Older headline")
            self.assertEqual(feed["posts"][0]["image"], "/media/newer_run.jpg")
            self.assertTrue((out / "media" / "newer_run.jpg").is_file())
            self.assertTrue((out / "media" / "older_run.jpg").is_file())
            self.assertFalse((out / "media" / "dry_run.jpg").exists())

    def test_rejects_non_https_link(self) -> None:
        self.assertIsNone(export.x_url_of({"x_url": "http://example.com/a"}))
        self.assertIsNone(export.x_url_of({"x_url": "javascript:alert(1)"}))
        self.assertEqual(
            export.x_url_of({"x_url": "https://x.com/tunastarlink/status/9"}),
            "https://x.com/tunastarlink/status/9",
        )


if __name__ == "__main__":
    unittest.main()
