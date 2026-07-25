# Planet Hack — build stats (whole repo)

Rolling tallies for **tuna-starlink-app**. Per-session write-ups:

| Session | File | When | Focus |
|---|---|---|---|
| **1** | [`STATS-SESSION-1.md`](STATS-SESSION-1.md) | 2026-07-21/22 | Greenfield: RSS → Imagine → gallery → X |
| **2** | [`STATS-SESSION-2.md`](STATS-SESSION-2.md) | 2026-07-22 | Lanes, X search, peak schedule, wire pack, Generative Stream |
| **3** | [`STATS-SESSION-3.md`](STATS-SESSION-3.md) | 2026-07-22 | Cost control: X search off, lean RSS, scheduler off |
| **4** | [`STATS-SESSION-4.md`](STATS-SESSION-4.md) | 2026-07-23 | Stream-render experiments → classic Imagine; Stream = X body |
| **5** | [`STATS-SESSION-5.md`](STATS-SESSION-5.md) | 2026-07-24/25 | Cool-tech wire + matrix prompts + systemd service |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 5 wrap (**2026-07-25**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,384** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,165** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **138** |
| **Application code subtotal** | **~4,687** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **1,705** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~6,521** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 (now) |
|---|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | **~4,687** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | **~6,521** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | ~+335 | ~+450 |
| S4 → S5 | **~+96** | **~+277** |

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 3,384 |
| `.md` | 1,705 |
| `.tsx` / `.ts` / `.css` | 1,165 |
| `.yaml` / `.yml` | 138 |
| other | ~129 |

---

## Combined Grok session activity (S1–S5)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S5)** | **~8.0–8.3 h** (~7.3–7.5 + ~0.7) |
| User messages | **100** (89 + 11) |
| Assistant messages | **426** (385 + 41) |
| Tool calls | **865** (806 + 59) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **111** (102 + 9; overlap possible) |
| Agent lines added | **~7,839** |
| Agent lines removed | **~924** |
| Context window | **500,000** |
| Context in use at S5 wrap | **~266,596** (~**53%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **31** × ~$0.02 ≈ **~$0.62** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X Recent Search | **OFF** |
| Unattended schedule | **OFF** (manual generate; service keeps API up) |
| Wire | Cool-tech only (SpaceX / GPU / AI) |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
style → lane (space | ai | gpu)
  → cool-tech RSS (SpaceX / NVIDIA-GPU / AI models, hard filter)
  → single story (title + summary, fill ~280 post)
  → Grok art director (matrix / hacker CGI)
  → xAI Imagine 16:9
  → X main: Generative Stream body, no hashtags, no reply
```

**Runtime:** prefer `systemctl --user` service (`scripts/install-persist.sh`) or Docker `restart: unless-stopped`.  
**Ops:** `SCHEDULE_ENABLED=false`, `X_SEARCH_ENABLED=false`, optional `AUTO_PUBLISH`.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
