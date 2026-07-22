#!/usr/bin/env python3
"""CLI one-shot generator. Run from repo root or backend/:

  DRY_RUN=1 python worker/run_once.py
  python worker/run_once.py --style data-tunnel
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Allow importing backend package modules
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Planet Hack one-shot generator")
    parser.add_argument("--style", default=None, help="style id from styles.yaml")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    from services import pipeline

    meta = await pipeline.run_generate(style_id=args.style, force=args.force)
    print(json.dumps({k: meta.get(k) for k in (
        "run_id", "status", "style_id", "caption", "egress_bytes", "latency_ms", "error", "dry_run"
    )}, indent=2))
    if meta.get("status") != "complete":
        return 1
    print(f"image: art/{meta['run_id']}/art.png  (relative to ART_STORAGE_PATH)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
