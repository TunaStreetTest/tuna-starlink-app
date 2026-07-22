# Beelink install — TunaStarLink / Planet Hack

Primary home for this app: **Windows host `TunaStarlink` (Beelink SER9 MAX) on Starlink**.

---

## What runs on the Beelink

| Component | Required? | Notes |
|---|---|---|
| TunaStarLink app (Docker or Python) | **Yes** | Generate + gallery + X post |
| Internet (Starlink) | **Yes** | xAI Imagine + X API |
| `XAI_API_KEY` + X tokens for **@tunastarlink** | **Yes** | In `.env` |
| Local disk for `art/` | **Yes** | PNGs + meta.json |
| Lemonade | Optional | Text only (`EDGE_TEXT=lemonade`) |
| Docker Desktop | Recommended | One-command runtime |

---

## 1. Copy the repo onto the Beelink

Any of:

- `git clone` / pull from your remote  
- USB / network share from the gaming PC  
- `scp -r tuna-starlink-app/` over Tailscale  

Suggested path:

```text
C:\Users\tunas\tuna-starlink-app
```

or WSL:

```text
~/tuna-starlink-app
```

---

## 2. Create art storage

```powershell
mkdir D:\TunaStarLink\art
```

(or `./art` inside the repo)

---

## 3. Environment file

Create `.env` next to `docker-compose.yml` (or `backend/.env.local` for native Python):

```env
DRY_RUN=false
ART_STORAGE_PATH=/art
XAI_API_KEY=xai-...
XAI_CHAT_MODEL=grok-4-1-fast-reasoning
XAI_IMAGE_MODEL=grok-imagine-image
DEFAULT_STYLE=data-tunnel
EVENTS_SOURCE=rss

# Overnight / unattended
SCHEDULE_ENABLED=true
SCHEDULE_CRON=0 18-22 * * *
SCHEDULE_TIMEZONE=America/New_York
AUTO_PUBLISH=true

# X — @tunastarlink user tokens (same developer app as TunaStreetTest is OK)
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
X_ACCOUNT_HANDLE=@tunastarlink
```

**Do not** reuse @TunaStreetTest *access* tokens. App API key/secret can be the same developer project; access tokens must be for **@tunastarlink**.

---

## 4A. Docker (recommended)

Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).

From the repo root:

```powershell
cd C:\Users\tunas\tuna-starlink-app
docker compose up --build -d
```

- UI/API: **http://127.0.0.1:8091**  
- Art volume: `./art` → `/art` in the container  

Logs:

```powershell
docker compose logs -f
```

Stop:

```powershell
docker compose down
```

---

## 4B. Native Python (no Docker)

Needs Python 3.12 + Node 20 if you rebuild the frontend.

```powershell
cd C:\Users\tunas\tuna-starlink-app
# or in WSL:
cd ~/tuna-starlink-app
make install-backend
# production-ish: build frontend once, serve from backend/static
cd frontend && npm install && npm run build
# copy dist into backend/static
mkdir -p ../backend/static && cp -r dist/* ../backend/static/
cd ../backend
# set ART_STORAGE_PATH and env, then:
.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8010
```

---

## 5. First checks on Starlink

1. Open `http://127.0.0.1:8091` (Docker) or `:8010`  
2. Health: **xai** + **x** green  
3. Studio → Run once (or wait for hourly cron)  
4. Gallery → confirm PNG + caption  
5. If `AUTO_PUBLISH=true`, check **@tunastarlink** for the thread  

Starlink tip: each run downloads **one image** (~0.5 MB). No model weights over the link.

---

## 6. Overnight / schedule

| Env | Meaning |
|---|---|
| `SCHEDULE_ENABLED=true` | In-process cron on |
| `SCHEDULE_CRON=0 18-22 * * *
SCHEDULE_TIMEZONE=America/New_York` | Top of every hour |
| `AUTO_PUBLISH=true` | After each success → X post + comment thread |

**Cost ballpark (cheap Imagine model):**

- ~**$0.02–0.04** xAI per full run (image dominates)  
- 8 hours hourly ≈ **$0.16–0.32** xAI  
- X posts/replies use your **X API plan limits**, not xAI credits  

---

## 7. X post behavior

- Main post: image + caption (≤280 chars, includes `#PlanetHack`)  
- **One reply:** news context — packs real headline phrases/keywords from the RSS events that fueled the piece (`Wired into this Planet Hack: …`) so the thread is discoverable around current events  
- Full art-director brief stays in local `meta.json` / gallery only  

---

## 8. Firewall / Tailscale (optional)

- Local UI only: no firewall change  
- Remote from gaming PC: allow inbound on 8091/8010 for Tailscale, or SSH tunnel  

---

## Related

- `docs/CREATIVE-BRIEF.md` — Planet Hack series lock  
- `docs/DEPLOY-STRIKELIST.md` — deploy checklist  
- `docs/STYLE-SEEDS.md` — share a style seed  
