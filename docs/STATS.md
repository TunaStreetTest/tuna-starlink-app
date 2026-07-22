# Planet Hack — build stats (whole repo)

Rolling tallies for **tuna-starlink-app**. Per-session write-ups:

| Session | File | When | Focus |
|---|---|---|---|
| **1** | [`STATS-SESSION-1.md`](STATS-SESSION-1.md) | 2026-07-21/22 | Greenfield: RSS → Imagine → gallery → X |
| **2** | [`STATS-SESSION-2.md`](STATS-SESSION-2.md) | 2026-07-22 | Lanes, X search, peak schedule, wire pack, Generative Stream |

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model (both sessions):** grok-4.5  

---

## Whole-repo lines of code (current)

Counted at Session 2 wrap (**2026-07-22**). Excludes `node_modules`, `.venv`, `art/` outputs, `package-lock.json`, `frontend/dist`.

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **2,675** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,147** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **112** |
| **Application code subtotal** | **~3,934** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **1,277** |
| Makefile, Dockerfile, `.env.example`, samples | **119** |
| **All product files** | **~5,330** |

### Growth across sessions

| | Session 1 wrap | Session 2 wrap (now) | Δ |
|---|---:|---:|---:|
| Application code | ~3,135 | **~3,934** | **+799** |
| All product files | ~3,999 | **~5,330** | **+1,331** |

### By language (product tree, current)

| Ext | Lines |
|---|---:|
| `.py` | 2,675 |
| `.md` | 1,277 |
| `.tsx` | 1,020 |
| `.ts` | 154 |
| `.yaml` / `.yml` | 112 |
| other (Makefile, Dockerfile, env.example, …) | ~119 |

---

## Combined Grok session activity (S1 + S2)

One continuous Grok Build session; numbers from final `signals.json`.

| Metric | Value |
|---|---:|
| **Active engineering time (S1 + S2)** | **~5.2 h** (~2.65 h + ~2.5 h) |
| User messages | **60** |
| Assistant messages | **249** |
| Tool calls | **533** |
| Compactions | **2** |
| Files touched (agent) | **77** |
| Agent lines added | **6,138** |
| Agent lines removed | **306** |
| Git commits (signal) | **6** |
| Context window | **500,000** |
| Context in use at wrap | **~89,546** (~18%) |

**Note:** Raw Grok wall-clock duration includes overnight idle with the session left open — **excluded** from effort totals. Use active engineering time only.

Session-level detail and deltas: Session 1 / Session 2 files above.

---

## Spend (product APIs, cumulative art)

| Item | Estimate |
|---|---:|
| Live Imagine images on disk | **22** × ~$0.02 ≈ **~$0.44** |
| Image payload total | **~9.6 MB** |
| X posts recorded on runs | **~16** |
| xAI chat (director / caption / slug) | Not metered in-repo |
| Grok Build agent tokens (invoice) | **Not exposed** to the agent — use xAI / Grok Build dashboard |

Practice: re-measure LOC + session signals at each session wrap; keep product API spend (Imagine count × unit price) in the same note so overnight ops stay predictable.

---

## Product shape (current)

```
style → news lane
  → X search (outlets / has:links) + RSS stream
  → multi-headline wire pack (primary first)
  → Grok art director (primary metaphor)
  → xAI Imagine 16:9
  → main: mood caption + #PlanetHack #StyleCamel
  → reply: Generative Stream (full ~280, multi-headline)
```

Peak schedule: **7–10pm America/New_York**, every **21 minutes**, `AUTO_PUBLISH` optional.

---

*Regenerate LOC anytime:*

```bash
find backend worker scripts -name '*.py' ! -path '*/.venv/*' | xargs wc -l
find frontend/src -type f \( -name '*.tsx' -o -name '*.ts' -o -name '*.css' \) | xargs wc -l
wc -l backend/prompts/styles.yaml docker-compose.yml
find docs -name '*.md' | xargs wc -l; wc -l README.md GROK.md
```
