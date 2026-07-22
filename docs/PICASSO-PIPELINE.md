# Planet Hack pipeline

See also `CREATIVE-BRIEF.md`.

## Steps

1. **Events** — Grok news desk (or dry-run stub bullets).
2. **Art director** — Grok rewrites events into a **visual brief** (metaphors only).
3. **Compose** — brief + series lock + shot seed (`styles.yaml`).
4. **Imagine** — `grok-imagine-image` (cheap) by default; one PNG.
5. **Caption** — short social line for manual post.
6. **Store** — `art/<run_id>/art.png` + `meta.json` (includes `art_brief`).

## DRY_RUN

`DRY_RUN=true` skips all paid calls: canned events, canned art brief, local neon-grid placeholder PNG.
**Not a taste sample** — only plumbing.

## Cost / Starlink notes

- Image ≈ $0.02 on cheap model; chat pennies for events + director + caption.
- One image download per successful run.
- Prefer `SCHEDULE_ENABLED=false` until series look is proven.

## Models

See `.env.example`. Stay on `grok-imagine-image` until you upgrade deliberately.
