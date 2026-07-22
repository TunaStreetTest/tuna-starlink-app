# TunaStarLink App — Planet Hack

World headlines → **news stream tap** → **Grok art director** → **xAI Imagine** → gallery → **@tunastarlink** on X.

Series look: hacker-movie **3D digital cyberspace / hacking the planet**.  
Home host: **Beelink SER9 (`TunaStarlink`)** on Starlink (also runs fine on a laptop).

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app

---

## Product

Each run:

1. **Ingest** public RSS into a local news stream (`art/.news_stream.json`)
2. **Tap** only *unconsumed* headlines (next run always gets a fresh set)
3. **Art director** (Grok) turns them into a visual brief
4. **Imagine** (`grok-imagine-image`, ~$0.02, landscape 16:9)
5. **Caption** + save `art/<run_id>/art.png` + `meta.json`
6. **X post** (manual button or `AUTO_PUBLISH`) — image + caption; one reply with news keywords

Downloads: `planethack_<run_id>.png`.

### Styles

| id | Shot |
|---|---|
| `planet-core` | Planetary mainframe core |
| `data-tunnel` | Packet tunnel flythrough |
| `signal-cathedral` | Signal megastructure (wide landscape) |
| `rootkit-city` | Circuit metropolis mid-infiltration |

Hourly schedule **picks a style at random**. Studio dropdown for manual runs.  
Share new styles: [`docs/STYLE-SEEDS.md`](docs/STYLE-SEEDS.md).

---

## Quick start

```bash
cd ~/tuna-starlink-app
cp backend/.env.example backend/.env.local
# fill keys — see .env section below

make backend     # http://127.0.0.1:8010
make frontend    # http://127.0.0.1:5174  (proxies /api → :8010)
```

Zero-cost plumbing test:

```bash
make dry-run
```

Docker:

```bash
# put the same vars in .env next to docker-compose.yml
docker compose up --build
# http://127.0.0.1:8091
```

Beelink install: [`docs/BEELINK-INSTALL.md`](docs/BEELINK-INSTALL.md).

---

## Full `.env` / `backend/.env.local`

```env
# --- generation ---
DRY_RUN=false
ART_STORAGE_PATH=../art

XAI_API_KEY=xai-...
XAI_CHAT_MODEL=grok-4-1-fast-reasoning
XAI_IMAGE_MODEL=grok-imagine-image
XAI_IMAGE_SIZE=1792x1024
XAI_IMAGE_ASPECT_RATIO=16:9

DEFAULT_STYLE=data-tunnel
EVENTS_SOURCE=stream

# optional local text model on Beelink
EDGE_TEXT=xai
LEMONADE_URL=http://127.0.0.1:13305
LEMONADE_MODEL=Qwen3-4B-GGUF

# --- unattended ---
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 * * * *
AUTO_PUBLISH=true

# --- X / @tunastarlink (OAuth 1.0a) ---
# API key/secret = developer app (can be the same project as other bots).
# Access token/secret MUST be for @tunastarlink (not another account).
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
X_ACCOUNT_HANDLE=@tunastarlink
```

OAuth pin helper (authorize @tunastarlink under your developer app):

```bash
# start flow prints a URL — log into X as @tunastarlink, authorize, get PIN
# then:
python scripts/x-oauth-finish.py <PIN>
```

That writes access tokens into `backend/.env.local`. Restart the backend after any env change.

---

## X (@tunastarlink)

| Step | Content |
|---|---|
| Main | Image + wordy caption + `#PlanetHack` |
| One reply | News headlines/keywords that fueled the piece |

Stored on each run: `x_url`, `x_post_id`, `x_replies` in `meta.json`.

**Gallery** tab → tile → modal → **Post to X**, or enable `AUTO_PUBLISH=true` for hourly auto-post.

---

## Overnight

```env
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 * * * *
AUTO_PUBLISH=true
EVENTS_SOURCE=stream
```

Leave backend or Docker running. ~$0.02–0.04 xAI per hourly run.

---

## API

| Method | Path | |
|---|---|---|
| GET | `/api/health` | disk, xAI, X |
| GET | `/api/styles` | style list |
| POST | `/api/generate` | `{ "style": "data-tunnel", "wait": false }` |
| GET | `/api/pipeline` | current run + news stream stats |
| GET | `/api/gallery` | runs |
| GET | `/api/gallery/{id}/image` | PNG (`planethack_<id>.png`) |
| GET | `/api/publish/status` | X credentials ready? |
| POST | `/api/publish/x` | `{ "run_id": "…", "with_comments": true }` |
| POST | `/api/publish/x/reply` | repair news comment |

```bash
DRY_RUN=1 ART_STORAGE_PATH=./art python worker/run_once.py --style data-tunnel
```

---

## Docs

| Doc | |
|---|---|
| [`docs/BEELINK-INSTALL.md`](docs/BEELINK-INSTALL.md) | Beelink / Starlink install |
| [`docs/STYLE-SEEDS.md`](docs/STYLE-SEEDS.md) | Add / share style seeds |
| [`docs/CREATIVE-BRIEF.md`](docs/CREATIVE-BRIEF.md) | Series look |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Topology |
| [`docs/DEPLOY-STRIKELIST.md`](docs/DEPLOY-STRIKELIST.md) | Deploy checklist |
| [`docs/STATS.md`](docs/STATS.md) | LOC + session token/activity tallies |
| [`GROK.md`](GROK.md) | Agent rules |

---

## Layout

```text
backend/     FastAPI + pipeline + news stream + X publish
frontend/    Studio + Gallery control plane
worker/      one-shot CLI
docs/        install, styles, creative
art/         generated assets (gitignored content)
scripts/     X OAuth pin finish helper
```
