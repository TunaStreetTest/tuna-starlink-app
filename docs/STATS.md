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
| **7** | [`STATS-SESSION-7.md`](STATS-SESSION-7.md) | 2026-07-28 | Studio merge · neon spectrum restore · lean newest-first wire |
| **8** | [`STATS-SESSION-8.md`](STATS-SESSION-8.md) | 2026-07-29 | Rootkit cityscape · kill lightning motif · Grok 4.5 art director |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 8 wrap (**2026-07-29**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,826** |
| Frontend (`frontend/src` — ts/tsx/css) | **905** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **170** |
| **Application code subtotal** | **~4,901** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **2,033** |
| Makefile, Dockerfile, `.env.example`, samples | **132** |
| **All product files** | **~7,066** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 (now) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | ~4,687 | ~4,781 | ~4,751 | **~4,901** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | ~6,521 | ~6,610 | ~6,802 | **~7,066** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | ~+335 | ~+450 |
| S4 → S5 | ~+96 | ~+277 |
| S5 → S6 | ~+94 | ~+89 |
| S6 → S7 | ~−30 | ~+192 |
| S7 → S8 | **~+150** | **~+264** |

*(S8: art director + compose rewrite + rootkit sanitizer; shorter YAML lock; new session stats docs.)*

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 3,826 |
| `.md` | 2,033 |
| `.tsx` / `.ts` / `.css` | 905 |
| `.yaml` / `.yml` | 170 |
| other | ~132 |

---

## Combined Grok session activity (S1–S8)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S8)** | **~9.8–10.8 h** (~9.1–9.8 + ~0.7–1.0) |
| User messages | **~115–116** (110–111 + 5) |
| Assistant messages | **~528** (489 + 39) |
| Tool calls | **~1,128** (1,015 + 113) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **~147** (133 + 14; overlap possible) |
| Agent lines added | **~9,049** |
| Agent lines removed | **~1,448** |
| Context window | **500,000** |
| Context in use at S8 wrap | **~103,730** (~**21%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **69** (mix ~$0.02 standard + ~$0.05 quality) ≈ **~$1.50–1.70** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X posts recorded in meta | **~43** |
| X Recent Search | **OFF** |
| Unattended schedule | **OFF** (systemd keeps API up; generate manual) |
| Wire | Lean cool-tech: SpaceX · Tesla/xAI · NVIDIA/AI (3 RSS feeds, newest-first, 72h max age) |
| Styles | `data-space`, `planet-core`, `data-tunnel`, `signal-cathedral`, `rootkit-city` |
| Art director | **Grok 4.5** (`XAI_ART_MODEL`) → SHOT paragraph; stream slug on fast model |
| Imagine | `grok-imagine-image-quality` @ **1K** (skip 2K); craft > resolution |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
Studio (single page)
  → Generate (style pick) + gallery tiles → modal → Post to X
  → cool-tech RSS (3 feeds, when:3d, 72h prune, newest publish first)
  → single story (title + summary → ~280 Generative Stream body)
  → Grok 4.5 art director (SHOT: one poetic plate; no people; dual light)
  → xAI Imagine 16:9 quality @ 1K
  → X main: Generative Stream body, no hashtags, no reply
```

**Craft bar:** one impossible architecture + photoreal materials + dual warm/cool light (showcase DNA).  
**Rootkit City:** classic hacker cityscape; green = building lights only — never path/bolt lightning.  
**Data Space:** deep space; few satellites max.  
**Data Tunnel:** busy packet tunnel.  
**Runtime:** `systemctl --user` or Docker; schedule **OFF** by default.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
