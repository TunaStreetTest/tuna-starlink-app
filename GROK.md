# Read this first (TunaStarLink / Planet Hack)

## Scope

FastAPI + React control plane: news stream, Grok art director, xAI Imagine (16:9), gallery, X post to **@tunastarlink** (caption + news-keyword reply), hourly schedule with **random style**.

## Secrets

Only in `.env` / `backend/.env.local` — never commit. X access tokens must be **@tunastarlink**.

## Hosting

Primary: **Beelink TunaStarlink** on Starlink. See `docs/BEELINK-INSTALL.md`.

## Key paths

| Path | Role |
|---|---|
| `backend/services/pipeline.py` | Generate orchestration |
| `backend/services/events.py` | News stream ingest + tap |
| `backend/services/x_publish.py` | X media + news reply |
| `backend/prompts/styles.yaml` | Style seeds |
| `docs/STYLE-SEEDS.md` | How to share a style |
| `art/<run_id>/` | PNG + meta (`planethack_<id>.png` downloads) |

## Dev

```bash
make dry-run          # no API spend
make backend          # :8010
make frontend         # :5174
```

Real image: `XAI_API_KEY` + `DRY_RUN=false` in `backend/.env.local`.
