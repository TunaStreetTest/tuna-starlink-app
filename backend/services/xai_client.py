"""xAI OpenAI-compatible client helpers."""

from __future__ import annotations

from openai import OpenAI

from config import settings


def client() -> OpenAI:
    if not settings.XAI_API_KEY and not settings.DRY_RUN:
        raise RuntimeError("XAI_API_KEY is not set (and DRY_RUN is false)")
    return OpenAI(
        base_url=settings.XAI_BASE_URL.rstrip("/"),
        api_key=settings.XAI_API_KEY or "dry-run",
    )
