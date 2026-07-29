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
| **9** | [`STATS-SESSION-9.md`](STATS-SESSION-9.md) | 2026-07-29 | Source-only captions · primary X brands · no news invent |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 9 wrap (**2026-07-29**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **3,829** |
| Frontend (`frontend/src` — ts/tsx/css) | **905** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **170** |
| **Application code subtotal** | **~4,904** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **2,143** |
| Makefile, Dockerfile, `.env.example`, samples | **133** |
| **All product files** | **~7,180** |

### Growth across sessions

| | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 (now) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Application code | ~3,135 | ~3,934 | ~4,256 | ~4,591 | ~4,687 | ~4,781 | ~4,751 | ~4,901 | **~4,904** |
| All product files | ~3,999 | ~5,330 | ~5,794 | ~6,244 | ~6,521 | ~6,610 | ~6,802 | ~7,066 | **~7,180** |

| Δ | App | All product |
|---|---:|---:|
| S1 → S2 | +799 | +1,331 |
| S2 → S3 | +322 | ~+464 |
| S3 → S4 | ~+335 | ~+450 |
| S4 → S5 | ~+96 | ~+277 |
| S5 → S6 | ~+94 | ~+89 |
| S6 → S7 | ~−30 | ~+192 |
| S7 → S8 | ~+150 | ~+264 |
| S8 → S9 | **~+3** | **~+114** |

*(S9: delete caption invent path; rebalance X search to primary brands; session stats docs.)*

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 3,829 |
| `.md` | 2,143 |
| `.tsx` / `.ts` / `.css` | 905 |
| `.yaml` / `.yml` | 170 |
| other | ~132 |

---

## Combined Grok session activity (S1–S9)

| Metric | Value |
|---|---:|
| **Active engineering time (S1–S9)** | **~10.3–11.6 h** (~9.8–10.8 + ~0.5–0.75) |
| User messages | **~118–119** (115–116 + ~3) |
| Assistant messages | **~558** (528 + ~30) |
| Tool calls | **~1,188** (1,128 + ~60) |
| Compactions | **2** |
| Files touched (agent, sum of snapshots) | **~151** (147 + 4; overlap possible) |
| Agent lines added | **~9,258** |
| Agent lines removed | **~1,586** |
| Context window | **500,000** |
| Context in use at S9 wrap | **~87,496** (~**17%**) |

**Note:** Report **active engineering time** only — wall clock includes idle.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live gallery Imagine PNGs (`art/*/art.png`) | **70** (mix ~$0.02 standard + ~$0.05 quality) ≈ **~$1.55–1.75** |
| Experiment / develop images (earlier) | **~17** × ~$0.02 ≈ **~$0.34** |
| X posts recorded in meta | **~40** |
| X Recent Search | **Primary-only when enabled** (official brands; TTL 120m). Local env may ON; config default opt-in. |
| Unattended schedule | **OFF** (systemd keeps API up; generate manual) |
| Wire | Lean cool-tech RSS + optional primary X; newest-first; soft photo-of-day blocked; 72h max age |
| Styles | `data-space`, `planet-core`, `data-tunnel`, `signal-cathedral`, `rootkit-city` |
| Art director | **Grok 4.5** (`XAI_ART_MODEL`) → SHOT paragraph; **caption is source-only** (no expand) |
| Imagine | `grok-imagine-image-quality` @ **1K** (skip 2K); craft > resolution |
| Grok Build agent tokens | **Not exposed** — dashboard |

---

## Product shape (current)

```
Studio (single page)
  → Generate (style pick) + gallery tiles → modal → Post to X
  → wire: primary X brands (when search on) else cool-tech RSS
  → single story — caption = source text only (no invent)
  → Grok 4.5 art director (SHOT: one poetic plate; no people; dual light)
  → xAI Imagine 16:9 quality @ 1K
  → X main: source-only stream body, no hashtags, no reply
```

**Trust bar:** X caption never invents facts past the wire.  
**Craft bar:** one impossible architecture + photoreal materials + dual warm/cool light.  
**Rootkit City:** classic hacker cityscape; green = building lights only — never path/bolt lightning.  
**Data Space:** deep space; few satellites max.  
**Data Tunnel:** busy packet tunnel.  
**Runtime:** `systemctl --user` or Docker; schedule **OFF** by default.

---

*Regenerate LOC anytime:*

```bash
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```
