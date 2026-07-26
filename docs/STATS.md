# Planet Hack — build stats (whole repo)

Rolling tallies for **tuna-starlink-app**. Per-session write-ups:

| Session | File | When | Focus |
|---|---|---|---|
| **1** | [`STATS-SESSION-1.md`](STATS-SESSION-1.md) | 2026-07-21/22 | Greenfield: RSS → Imagine → gallery → X |
| **2** | [`STATS-SESSION-2.md`](STATS-SESSION-2.md) | 2026-07-22 | Lanes, X search, peak schedule, wire pack, Generative Stream |
| **3** | [`STATS-SESSION-3.md`](STATS-SESSION-3.md) | 2026-07-22 | Cost control: X search off, lean RSS, scheduler off |
| **4** | [`STATS-SESSION-4.md`](STATS-SESSION-4.md) | 2026-07-23 | Stream-render experiments → classic Imagine; Stream = X body |
| **5** | [`STATS-SESSION-5.md`](STATS-SESSION-5.md) | 2026-07-24/25 | Cool-tech wire + matrix prompts + systemd service |
| **6** | [`STATS-SESSION-6.md`](STATS-SESSION-6.md) | 2026-07-26 | Art direction polish + **Data Space**; classic Data Tunnel |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 6 wrap (**2026-07-26**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,446** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,165** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **170** |
| **Application code subtotal** | **~4,781** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **1,700** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~6,610** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 | S6 (now) |
|---|---:|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | ~4,687 | **~4,781** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | ~6,521 | **~6,610** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | ~+335 | ~+450 |
| S4 → S5 | ~+96 | ~+277 |
| S5 → S6 | **~+94** | **~+89** |

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 3,446 |
| `.md` | 1,700 |
| `.tsx` / `.ts` / `.css` | 1,165 |
| `.yaml` / `.yml` | 170 |
| other | ~129 |

---

## Combined Grok session activity (S1–S6)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S6)** | **~8.6–9.0 h** (~8.0–8.3 + ~0.6) |
| User messages | **107** (100 + 7) |
| Assistant messages | **453** (426 + 27) |
| Tool calls | **920** (865 + 55) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **122** (111 + 11; overlap possible) |
| Agent lines added | **~8,371** |
| Agent lines removed | **~1,140** |
| Context window | **500,000** |
| Context in use at S6 wrap | **~308,787** (~**62%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **44** × ~$0.02 ≈ **~$0.88** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X Recent Search | **OFF** |
| Unattended schedule | **OFF** (systemd keeps API up; generate manual) |
| Wire | Cool-tech only (SpaceX / GPU / AI) |
| Styles | `data-space`, `planet-core`, `data-tunnel` (classic), `signal-cathedral`, `rootkit-city` |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
style → lane (space | ai | gpu)
  → cool-tech RSS (SpaceX / NVIDIA-GPU / AI models, hard filter)
  → single story (title + summary, fill ~280 post)
  → Grok art director (no people; varied palette)
  → xAI Imagine 16:9
  → X main: Generative Stream body, no hashtags, no reply
```

**Data Space:** exterior deep-space recipes (planet / multi-planet / star / SpaceX-inspired craft).  
**Data Tunnel:** classic vanishing-point energy conduit (restored).  
**Runtime:** `systemctl --user` (`scripts/install-persist.sh`) or Docker `restart: unless-stopped`.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
