# Planet Hack — Session 1 build stats

Greenfield session that created `tuna-starlink-app` from scratch (**2026-07-21/22**).

**Repo:** https://github.com/TunaStreetTest/tuna-starlink-app  
**Model:** grok-4.5  
**Phase:** scaffold → RSS news stream → Imagine 16:9 → gallery → X @tunastarlink → first schedule

Cumulative / whole-repo tallies live in [`STATS.md`](STATS.md). Session 2: [`STATS-SESSION-2.md`](STATS-SESSION-2.md).

---

## Lines of code (repo at Session 1 wrap)

Counted with `wc -l` on product sources (excludes `node_modules`, `.venv`, `art/` outputs, lockfiles, `frontend/dist`).

| Area | Lines |
|---|---:|
| Python (`backend/`, `worker/`, `scripts/`) | **1,969** |
| Frontend (`frontend/src` — ts/tsx/css) | **1,057** |
| Style seeds + compose (`styles.yaml`, `docker-compose.yml`) | **109** |
| **Application code subtotal** | **~3,135** |
| Docs (`docs/*.md`, `README.md`, `GROK.md`) | **735** |
| Makefile, Dockerfile, `.env.example`, samples | **129** |
| **All product files** | **~3,999** |

Rough shape at end of Session 1: **~3.1k app lines**, **~4.0k with docs**.

### By language (product tree)

| Ext | Lines |
|---|---:|
| `.py` | 1,969 |
| `.tsx` | 936 |
| `.md` | 735 |
| `.ts` | 148 |
| `.yaml` / `.yml` | 109 |
| other (Makefile, Dockerfile, env.example, …) | ~102 |

---

## Session activity (Grok Build signals)

From session telemetry (`signals.json`) at Session 1 wrap-up:

| Metric | Value |
|---|---:|
| Session duration (to S1 wrap) | **~9,548 s** (~2.65 hours) |
| User messages / turns | **46** |
| Assistant messages | **164** |
| Tool calls | **371** (4 failures) |
| Files touched by agent | **59** |
| Agent lines added (editor telemetry) | **4,680** |
| Agent lines removed | **1** |
| Compactions | **0** |
| Git commits (signal counter) | **1+** |

Tools used: `run_terminal_command`, `read_file`, `write`, `search_replace`, `grep`, `list_dir`, `web_fetch`, `todo_write`, `enter_plan_mode` / `exit_plan_mode`, `ask_user_question`, …

---

## Tokens

| What | Value | Notes |
|---|---:|---|
| **Context window size** | **500,000** | Session model window |
| **Context tokens in use (S1 wrap)** | **~316,480** | ~**63%** of window — *occupancy, not lifetime bill* |
| **Lifetime prompt + completion tokens billed** | **Not exposed** | Runtime does not publish a cumulative in/out meter to the agent |

**How to read this:** `contextTokensUsed` is how full the active window was. Lifetime billed tokens over ~46 turns is **higher** and only available from the xAI / Grok Build usage dashboard.

---

## Product shipped (Session 1)

- News stream (RSS inject → tap unconsumed, multi-headline packs)
- Grok art director + Imagine (16:9)
- Studio + tiled Gallery + modal
- X post to @tunastarlink (caption + news-keyword reply)
- Schedule + optional auto-publish
- Beelink install + style-seed sharing docs
- `planethack_<run_id>.png` downloads

---

*Measured at first stats wrap (`d5f6cce` era). Later repo totals supersede these LOC numbers — see [`STATS.md`](STATS.md).*
