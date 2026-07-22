---
name: session-wrap
description: >
  Close a Planet Hack / tuna-starlink-app Grok Build session: measure whole-repo LOC,
  write or update session stats docs, refresh README totals tables, commit, and push.
  Use when the user says wrap up, close session, update stats, session wrap, end of
  session, ship stats, or runs /session-wrap.
---

# Session wrap (Planet Hack stats + ship)

Run this at the end of a focused build session so **whole-repo totals stay honest** and history is preserved per session.

## Preconditions

- Working directory is the **tuna-starlink-app** repo root (or `cwd` contains `backend/` + `docs/STATS.md`).
- Do **not** commit secrets (`.env`, `.env.local`, tokens).
- Ask before `git push` only if the user has not already said to ship / wrap / push.

## Steps

### 1. Measure product LOC (whole repo, current)

Exclude: `node_modules`, `.venv`, `dist`, `__pycache__`, `art/`, `.git`, `package-lock.json`.

```bash
# Prefer the helper when present:
python3 .grok/skills/session-wrap/scripts/measure_loc.py
```

Or manual:

```bash
find backend worker scripts -name '*.py' ! -path '*/.venv/*' ! -path '*/__pycache__/*' | xargs wc -l
find frontend/src -type f \( -name '*.tsx' -o -name '*.ts' -o -name '*.css' \) | xargs wc -l
wc -l backend/prompts/styles.yaml docker-compose.yml
find docs -name '*.md' | xargs wc -l; wc -l README.md GROK.md
wc -l Makefile Dockerfile backend/.env.example samples/example-run.json 2>/dev/null
```

Record:

| Bucket | What |
|---|---|
| Python | `backend/` + `worker/` + `scripts/` `*.py` |
| Frontend | `frontend/src` ts/tsx/css |
| YAML | `styles.yaml` + `docker-compose.yml` |
| **App subtotal** | Python + Frontend + YAML |
| Docs | `docs/*.md` + `README.md` + `GROK.md` |
| Other | Makefile, Dockerfile, `.env.example`, samples |
| **All product** | App + Docs + Other |

### 2. Session telemetry (Grok Build)

From the **current** session directory (typically under `~/.grok/sessions/…`):

- Read `signals.json` for: `userMessageCount`, `assistantMessageCount`, `toolCallCount`, `toolFailureCount`, `agentLinesAdded`, `agentLinesRemoved`, `agentFilesTouched`, `compactionCount`, `gitCommitCount`, `contextTokensUsed`, `contextWindowTokens`, `totalTokensBeforeCompaction`, `toolsUsed`, `primaryModelId`.
- Read `summary.json` for session id / timestamps if useful.
- **`sessionDurationSeconds` is wall clock** — it includes overnight / lunch / idle while the session stays open. **Never report it as effort.** Estimate **active engineering time** from real work windows (or Δ vs prior wrap’s active estimate), and label it clearly as active-only.

**Token rules (always state clearly):**

- `contextTokensUsed` = window **occupancy**, not lifetime bill.
- Lifetime billed in/out is **not exposed** unless the user has a dashboard number — say so.
- If prior session wrap exists in `docs/STATS-SESSION-N.md`, compute **Δ** vs that snapshot for the new session file.

### 3. Product API spend (optional but preferred)

From `art/*/meta.json`:

- Count non–`dry_run` Imagine runs × ~$0.02.
- Count runs with `x_url` or successful `auto_publish`.
- Note peak schedule cost: fires/night × unit price.

### 4. Write stats files

Convention:

| File | Role |
|---|---|
| `docs/STATS.md` | **Whole-repo index** — current LOC tables, combined session activity, spend, links |
| `docs/STATS-SESSION-1.md` | Session 1 snapshot (immutable once written) |
| `docs/STATS-SESSION-N.md` | This session — goals, Δ activity, LOC growth, checklist, commits |

For a new session `N`:

1. Create `docs/STATS-SESSION-N.md` from the template in `references/stats-session-template.md`.
2. Rewrite `docs/STATS.md` tables to **current whole-repo** LOC + combined activity + links to all session files.
3. Update **README.md** “Build stats (whole repo)” section tables to the same **current** totals (not session-only).
4. If a session plan doc exists (`docs/SESSION-N-PLAN.md`), mark status **Shipped** and link stats.

### 5. Product copy sanity (light)

If the session changed pipeline behavior, align short product bullets in README (flow, X post contract, schedule) — do not rewrite the whole README.

### 6. Commit + push

```bash
git status
git diff --stat
git log -5 --oneline
```

Stage stats + intentional product fixes only. Commit message style (complete sentences):

```text
Session N wrap: <one-line theme>

<1–2 sentences: stats docs + any last product fixes included.>
```

Then:

```bash
git push origin main
```

Confirm clean tree and pushed SHA.

### 7. Optional runtime teardown

Only if the user asked to stop local servers:

- Kill uvicorn on the app port (often **8010**) and Vite (often **5174**) by **PID** from `ss`/`lsof`, not broad `pkill -f` patterns that can self-match.
- Do **not** stop Beelink / Docker hosts unless explicitly requested.

### 8. Hand-off

Reply with:

- New session stats path + README totals summary (app LOC, all product LOC, Δ).
- Commit SHA + push status.
- Overnight / Beelink reminder if schedule is live (`SCHEDULE_ENABLED`, peak window, `AUTO_PUBLISH`).

## Do not

- Invent billed token totals.
- Commit `.env.local` or art binaries.
- Overwrite old `STATS-SESSION-*.md` history — add a new file instead.
- Force-push.

## Related

- Install overnight host: `docs/BEELINK-INSTALL.md`
- Style seeds: `docs/STYLE-SEEDS.md`
