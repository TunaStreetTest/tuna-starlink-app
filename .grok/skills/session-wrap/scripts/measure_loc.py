#!/usr/bin/env python3
"""Measure product LOC for tuna-starlink-app (session-wrap helper)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXCLUDE = {"node_modules", ".venv", "dist", "__pycache__", "art", ".git"}


def ok(p: Path) -> bool:
    return not any(part in EXCLUDE for part in p.parts)


def line_count(paths: list[Path]) -> int:
    total = 0
    for p in paths:
        try:
            total += sum(1 for _ in p.open("rb"))
        except OSError:
            pass
    return total


def main() -> int:
    # repo root: walk up from script or cwd
    here = Path(__file__).resolve()
    root = here.parents[4] if (here.parents[4] / "backend").is_dir() else Path.cwd()
    if not (root / "backend").is_dir():
        # script at .grok/skills/session-wrap/scripts → parents[3] is repo
        for cand in [here.parents[i] for i in range(2, 6)] + [Path.cwd()]:
            if (cand / "backend").is_dir() and (cand / "docs").is_dir():
                root = cand
                break
    root = root.resolve()

    py = [
        p
        for base in ("backend", "worker", "scripts")
        for p in (root / base).rglob("*.py")
        if p.is_file() and ok(p)
    ]
    fe = [
        p
        for p in (root / "frontend" / "src").rglob("*")
        if p.is_file() and p.suffix in {".ts", ".tsx", ".css"} and ok(p)
    ]
    yaml = [
        root / "backend" / "prompts" / "styles.yaml",
        root / "docker-compose.yml",
    ]
    yaml = [p for p in yaml if p.is_file()]
    docs = list((root / "docs").glob("*.md")) + [
        root / "README.md",
        root / "GROK.md",
    ]
    docs = [p for p in docs if p.is_file()]
    other = [
        root / "Makefile",
        root / "Dockerfile",
        root / "backend" / ".env.example",
        root / "samples" / "example-run.json",
    ]
    other = [p for p in other if p.is_file()]

    python_n = line_count(py)
    frontend_n = line_count(fe)
    yaml_n = line_count(yaml)
    docs_n = line_count(docs)
    other_n = line_count(other)
    app = python_n + frontend_n + yaml_n
    all_product = app + docs_n + other_n

    out = {
        "root": str(root),
        "python": python_n,
        "frontend": frontend_n,
        "yaml": yaml_n,
        "application_code": app,
        "docs": docs_n,
        "other": other_n,
        "all_product": all_product,
    }
    print(json.dumps(out, indent=2))
    print(
        f"\nApp ~{app:,}  |  Docs {docs_n:,}  |  All product ~{all_product:,}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
