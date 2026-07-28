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

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 7 wrap (**2026-07-28**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,662** |
| Frontend (`frontend/src` — ts/tsx/css) | **905** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **184** |
| **Application code subtotal** | **~4,751** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **1,922** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~6,802** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 | S6 | S7 (now) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | ~4,687 | ~4,781 | **~4,751** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | ~6,521 | ~6,610 | **~6,802** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | ~+335 | ~+450 |
| S4 → S5 | ~+96 | ~+277 |
| S5 → S6 | ~+94 | ~+89 |
| S6 → S7 | **~−30** | **~+190** |

*(S7 app LOC down slightly: deleted list-only `StudioGallery` after merge; news + color logic grew Python.)*

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 3,662 |
| `.md` | ~1,920 |
| `.tsx` / `.ts` / `.css` | 905 |
| `.yaml` / `.yml` | 184 |
| other | ~129 |

---

## Combined Grok session activity (S1–S7)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S7)** | **~9.1–9.8 h** (~8.6–9.0 + ~0.5–0.8) |
| User messages | **~110–111** (107 + ~3–4) |
| Assistant messages | **~489** (453 + ~36) |
| Tool calls | **~1,015** (920 + ~95) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **~133** (122 + 11; overlap possible) |
| Agent lines added | **~8,742** |
| Agent lines removed | **~1,300** |
| Context window | **500,000** |
| Context in use at S7 wrap | **~101,749** (~**20%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **62** × ~$0.02 ≈ **~$1.24** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X posts recorded in meta | **~33** |
| X Recent Search | **OFF** |
| Unattended schedule | **OFF** (systemd keeps API up; generate manual) |
| Wire | Lean cool-tech: SpaceX · Tesla/xAI · NVIDIA/AI (3 RSS feeds, newest-first, 72h max age) |
| Styles | `data-space`, `planet-core`, `data-tunnel`, `signal-cathedral`, `rootkit-city` |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
Studio (single page)
  → Generate (style pick) + gallery tiles → modal → Post to X
  → cool-tech RSS (3 feeds, when:3d, 72h prune, newest publish first)
  → single story (title + summary → ~280 Generative Stream body)
  → Grok art director (no people; FULL neon spectrum, color-lead varies)
  → xAI Imagine 16:9
  → X main: Generative Stream body, no hashtags, no reply
```

**Neon DNA:** cyan + magenta + acid-green luminous color required; gold/amber optional warm; never graphite-monochrome.  
**Rootkit City:** unique cityscape recipes + classic neon night.  
**Data Space:** deep space; few satellites max.  
**Data Tunnel:** busy packet tunnel.  
**Runtime:** `systemctl --user` or Docker; schedule **OFF** by default.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
