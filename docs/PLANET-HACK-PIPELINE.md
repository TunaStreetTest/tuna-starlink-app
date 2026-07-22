# Planet Hack pipeline

See also `CREATIVE-BRIEF.md`.

## Steps

1. **News stream** — RSS injects into `art/.news_stream.json`; run *taps* unconsumed headlines.
2. **Art director** — Grok rewrites them into a visual brief (metaphors only).
3. **Compose** — brief + series lock + shot seed (`styles.yaml`).
4. **Imagine** — `grok-imagine-image`, landscape 16:9; one PNG.
5. **Caption** — social post line + `#PlanetHack`.
6. **Store** — `art/<run_id>/art.png` + `meta.json`.
7. **X** (optional / auto) — image + caption; one reply with news keywords.

Downloads: `planethack_<run_id>.png`.

## DRY_RUN

`DRY_RUN=true` skips paid calls: stub stream, canned brief, local placeholder PNG. Plumbing only.

## Cost / Starlink

- Image ≈ $0.02; chat is small.
- One image download per successful run over Starlink.

## Models

See `.env.example` / README full env.
