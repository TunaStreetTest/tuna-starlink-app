# TunaStarLink App — Planet Hack

World events → **Grok art director** → **xAI Imagine** (cheap model) → local gallery.

Series look: hacker-movie **3D digital cyberspace / hacking the planet** — not Picasso.
Built for the **Beelink SER9 (`TunaStarlink`)** over Starlink. No Kafka / EFM / NiFi required.

> Sibling of [`cso-operator-app`](https://github.com/cldr-steven-matison/cso-operator-app) by pattern only — **separate repo, separate process, zero shared PVCs**. Live streamers app is never touched.

## Product

Every run:

1. News desk — top world events (Grok)
2. **Art director** — Grok turns events into a visual brief (metaphors only)
3. Compose — brief + series lock + shot preset
4. Imagine — `grok-imagine-image` (~$0.02)
5. Caption + save under `art/<run_id>/` — **you post to @tunastarlink by hand**

Shot presets: `planet-core` (default), `data-tunnel`, `signal-cathedral`, `rootkit-city`.

## Quick start (this machine / any laptop)

```bash
cd ~/tuna-starlink-app

# zero-cost smoke test
make dry-run

# control plane
cp backend/.env.example backend/.env.local
# edit: DRY_RUN=true for free, or set XAI_API_KEY and DRY_RUN=false

make backend     # terminal 1 → http://127.0.0.1:8010/api/health
make frontend    # terminal 2 → http://127.0.0.1:5174
```

Docker (Beelink-friendly):

```bash
export XAI_API_KEY=...
export DRY_RUN=false
docker compose up --build
# UI/API: http://127.0.0.1:8091
```

## Styles

See `backend/prompts/styles.yaml` and `docs/CREATIVE-BRIEF.md`.

## API

| Method | Path | |
|---|---|---|
| GET | `/api/health` | disk + xAI key + optional Lemonade |
| GET | `/api/styles` | style presets |
| POST | `/api/generate` | `{ "style": "picasso-pixel", "wait": false }` |
| GET | `/api/pipeline` | current + recent runs |
| GET | `/api/gallery` | list |
| GET | `/api/gallery/{id}/image` | PNG |

CLI:

```bash
DRY_RUN=1 ART_STORAGE_PATH=./art python worker/run_once.py --style starlink-glitch
```

## What we deliberately left out

Kafka topics, EFM agent wiring, NiFi process groups, Minikube lab manifests, local image models, auto-tweet. Those can come later if the art is worth it — see `docs/DEPLOY-STRIKELIST.md`.

## Overnight schedule

```env
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 * * * *    # top of every hour
AUTO_PUBLISH=true          # post to @tunastarlink after each success
DEFAULT_STYLE=data-tunnel
```

Leave `make backend` (or Docker) running. Each hour: RSS events → art director → Imagine → X thread.

## Docs

- **`docs/BEELINK-INSTALL.md`** — full Beelink / Starlink install (copy this with the repo)
- `docs/DEPLOY-STRIKELIST.md` — deploy checklist
- `docs/CREATIVE-BRIEF.md` — series look
- `docs/ARCHITECTURE.md` — lean topology
- DesktopShare: `tuna-starlink-app.md`, `beelink-starlink-efm-ai.md`
