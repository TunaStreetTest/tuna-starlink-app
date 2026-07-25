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
XAI_CHAT_MODEL=grok-4-1-fast-non-reasoning
XAI_IMAGE_MODEL=grok-imagine-image
DEFAULT_STYLE=data-tunnel
EVENTS_SOURCE=stream

# Cost control — manual generate; optional auto-post after success
SCHEDULE_ENABLED=false
AUTO_PUBLISH=true
X_SEARCH_ENABLED=false

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

## 4C. Run as a service (survives Grok sessions)

**Do not** rely on `nohup uvicorn` started inside a Grok/agent shell — that dies when the session ends.

### WSL / Linux: systemd user unit (recommended on Beelink WSL)

Unit file in repo: [`deploy/tuna-starlink.service`](../deploy/tuna-starlink.service)  
Installer: [`scripts/install-persist.sh`](../scripts/install-persist.sh)

```bash
cd ~/tuna-starlink-app
# backend/.env.local filled; venv installed (make install-backend)
# frontend built into backend/static if you want UI without Vite
bash scripts/install-persist.sh
```

What it does:

- Installs `~/.config/systemd/user/tuna-starlink.service`
- `systemctl --user enable --now tuna-starlink`
- Enables **linger** so the service keeps running after logout
- Restarts on crash (`Restart=always`)
- Logs to `~/tuna-starlink-app/uvicorn.log` (+ journal)

| Action | Command |
|---|---|
| Status | `systemctl --user status tuna-starlink` |
| Logs | `journalctl --user -u tuna-starlink -f` or `tail -f ~/tuna-starlink-app/uvicorn.log` |
| Restart | `systemctl --user restart tuna-starlink` |
| Stop | `systemctl --user stop tuna-starlink` |
| Disable | `systemctl --user disable --now tuna-starlink` |

**UI:** http://127.0.0.1:8010  

**After `git pull`:** rebuild frontend if UI changed, then `systemctl --user restart tuna-starlink`.

### Docker: restart policy

`docker-compose.yml` already has `restart: unless-stopped`.

```bash
docker compose up --build -d
# http://127.0.0.1:8091
```

Survives container exits; Docker Desktop must be running.

### Windows reboot

| Goal | How |
|---|---|
| WSL service after reboot | Docker Desktop “Start when you log in”, **or** Task Scheduler → `wsl -e systemctl --user start tuna-starlink` at logon |
| Always-on container | Docker Desktop autostart + `docker compose up -d` |

**Data persistence (already on disk):** `art/`, `backend/.env.local`, `art/.news_stream.json` — independent of Grok.

---

## 5. First checks on Starlink

1. Open `http://127.0.0.1:8091` (Docker) or `:8010` (native/service)  
2. Health: **xai** + **x** green  
3. Studio → Run once  
4. Gallery → confirm PNG + Generative Stream body  
5. If `AUTO_PUBLISH=true`, check **@tunastarlink**  

Starlink tip: each run downloads **one image** (~0.5 MB). No model weights over the link.

---

## 6. Overnight / schedule

| Env | Meaning |
|---|---|
| `SCHEDULE_ENABLED=false` | Default — manual Generate only (cost control) |
| `SCHEDULE_ENABLED=true` | Optional in-process peak schedule |
| `AUTO_PUBLISH=true` | After successful generate → X main post |

**Cost ballpark (cheap Imagine model):**

- ~**$0.02–0.04** xAI per full run (Imagine dominates)  
- X posts use your **X API plan limits**, not xAI credits  

---

## 7. X post behavior

- **Main:** image + **Generative Stream** body (one cool-tech story, fill ~280, **no hashtags**)  
- **Reply:** none  
- Art-director brief stays in local `meta.json` / gallery only  

Wire is **SpaceX / GPU / AI model** only (not world politics).

---

## 8. Firewall / Tailscale (optional)

- Local UI only: no firewall change  
- Remote from gaming PC: allow inbound on 8091/8010 for Tailscale, or SSH tunnel  

---

## Related

- `docs/CREATIVE-BRIEF.md` — Planet Hack series look  
- `docs/DEPLOY-STRIKELIST.md` — deploy checklist  
- `docs/STYLE-SEEDS.md` — share a style seed  
- `docs/STATS.md` — whole-repo LOC + session index  
