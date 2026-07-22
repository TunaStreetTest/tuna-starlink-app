"""Load Planet Hack style presets from prompts/styles.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from config import settings

_STYLES_FILE = Path(__file__).resolve().parent.parent / "prompts" / "styles.yaml"


@lru_cache(maxsize=1)
def _raw() -> dict[str, Any]:
    with _STYLES_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def reload_styles() -> None:
    _raw.cache_clear()


def series_info() -> dict[str, str]:
    data = _raw()
    s = data.get("series") or {}
    return {
        "name": (s.get("name") or "Planet Hack").strip(),
        "tagline": (s.get("tagline") or "").strip(),
        "shared_lock": (s.get("shared_lock") or "").strip(),
    }


def list_styles() -> list[dict[str, str]]:
    data = _raw()
    styles = data.get("styles") or {}
    out = []
    for key, val in styles.items():
        out.append(
            {
                "id": key,
                "label": val.get("label", key),
                "description": val.get("description", ""),
            }
        )
    return out


def get_style(style_id: str | None = None) -> dict[str, Any]:
    data = _raw()
    styles = data.get("styles") or {}
    key = style_id or settings.DEFAULT_STYLE or data.get("default") or next(iter(styles), "")
    if key not in styles:
        raise ValueError(f"unknown style {key!r}; known: {list(styles)}")
    val = styles[key]
    series = series_info()
    return {
        "id": key,
        "label": val.get("label", key),
        "description": val.get("description", ""),
        "art_director_notes": (val.get("art_director_notes") or "").strip(),
        "prompt_seed": (val.get("prompt_seed") or "").strip(),
        "series_name": series["name"],
        "series_tagline": series["tagline"],
        "shared_lock": series["shared_lock"],
    }


def build_imagine_prompt(art_brief: str, style: dict[str, Any]) -> str:
    """
    Compact Imagine payload. Order matters:
      1) concrete visual seed (strong prior)
      2) structured art-director brief
      3) short hard rules / anti-stock
    """
    seed = (style.get("prompt_seed") or "").strip()
    brief = art_brief.strip()
    lock = (style.get("shared_lock") or "").strip()
    parts = [
        seed,
        "",
        brief,
        "",
        lock,
    ]
    return "\n".join(parts).strip()
