# Planet Hack — Session 2 plan

**Status:** Implementation started 2026-07-22 — Session 2 building.  
**Session 1 baseline:** RSS news stream, four styles, Imagine 16:9, X post + news reply, schedule 6–10pm ET hourly (live until Session 2 ships).

---

## Locked decisions (2026-07-22)

| # | Topic | Decision |
|---|---|---|
| **2** | News tap size | **1** headline/story per run |
| **3** | Style hashtags | **camelCase** |
| **4** | Style ↔ news lane | Pairing table **approved** (below) |
| **5** | Event source | **Must include X search** (not RSS-only) |
| **6** | Schedule | **7pm–10pm Eastern**, every **21 minutes** |

### #1 Density / “styles look the same” — rephrased simply

Earlier “quiet vs busy” language was confusing. Plain version:

**Problem:** Different style names, but images still look like the same busy neon collage.

**What we’ll fix in Session 2 (no code yet):**

1. Make each style **obviously different** (camera + subject + color dominance), not the same lock with a new label.  
2. **Tone down AI “extra”** a bit so pieces don’t all scream at max intensity — still interesting, less clutter.

We’ll show you 1–2 revised seed drafts in planning before regenerating live art.

---

## Style ↔ news lane (#4 locked)

| Style id | camelCase hashtag | News lane |
|---|---|---|
| `planet-core` | `#PlanetCore` | Geopolitics / global order |
| `data-tunnel` | `#DataTunnel` | Tech / AI / infrastructure |
| `signal-cathedral` | `#SignalCathedral` | Science / space / climate / energy |
| `rootkit-city` | `#RootkitCity` | Markets / power / civic systems |

Franchise tag always: **`#PlanetHack`**.

---

## Post contract (#2 + #3)

### Main post
- Image + short atmospheric caption  
- Ends with: **`#PlanetHack #DataTunnel`** (or whichever style ran)  
- camelCase style tag only — no run-id salts, no extra hash spam  

### One reply only
```text
Generative Stream: <short human slug about that one story>. #DataTunnel
```
- Prefix exactly: **`Generative Stream: `**  
- Ends with the **same style hashtag** as the main post  
- **No `#PlanetHack` in the reply** (keeps franchise tag on the parent only — or we can put both only on main; reply is style-tagged)  
- No full RSS paste; slug derived from the **single** tapped story  

### Stream size
- Tap **1** item per run (after style + lane filter / X search).  
- Art director, caption, and Generative Stream reply all orbit **that one story**.

---

## Schedule (#6 locked for Session 2)

| Setting | Value |
|---|---|
| Window | **7:00pm – 10:00pm** America/New_York |
| Cadence | Every **21 minutes** |
| Outside window | No scheduled posts |

**Cron sketch (when implementing):** not a simple hourly cron — need either:

- `*/21` within hours 19–22 Eastern, or  
- explicit fire list / APScheduler interval with a time-window guard  

Example fire times if starting at 19:00:  
`19:00, 19:21, 19:42, 20:03, 20:24, 20:45, 21:06, 21:27, 21:48, 22:09, 22:30, 22:51`  
(exact grid TBD at implement time; last fires must still be ≤ 10pm or cut off after 22:00 start).

**Rough volume:** ~9–12 posts/evening if full window — confirm cost comfort (~$0.02–0.04 × N xAI + X writes).

---

## X search as source (#5 locked)

### Goal
Use **X as a live viral/news surface** (per XFreeze-style thinking: news breaks first on X), not only RSS wires.

### Session 2 design (proposed)

```
1. Pick style (random in schedule, or UI)
2. Resolve news lane for that style
3. X search (and/or lane query) for recent high-signal posts
4. Grok ranks → pick ONE story/event suitable for abstract art
5. Optional: merge or prefer X over RSS when score is high
6. Art director + Imagine + post/comment from that single story
```

### Technical notes (for later)

- Needs **X API read/search** permissions on the app (beyond post+media).  
- Start with: recent search query per lane, min likes/reposts filter, last N hours.  
- Store on run: `events_source: x-search`, post ids/urls of source tweets (for provenance, not necessarily public on our reply).  
- Fail soft: if X search empty/errors → RSS lane fallback **once**, still 1 story.  

### Not in Session 2 scope
- Full bookmark OS / MCP research agent from the XFreeze essay  
- Auto-reply to others’ posts  
- Unsupervised viral engagement farming  

---

## Session 2 work packages (when “go”)

1. **Creative seeds** — differentiate four styles; slightly less busy shared rules.  
2. **Single-story tap** — stream + lane filter.  
3. **X search spike** — lane queries → one story.  
4. **Post/comment rewrite** — `#PlanetHack #StyleCamel` + `Generative Stream: … #StyleCamel`.  
5. **Schedule** — 7–10pm ET every 21 minutes (window guard).  
6. **Docs** — README + STYLE-SEEDS + BEELINK env examples.  
7. **Smoke** — one manual run per style with X search; one evening dry observation.

---

## Still open (soft)

1. **#1 density:** After you see draft seed text, approve “a bit quieter” vs “keep intensity, only differentiate.”  
2. **21-minute grid:** First fire exactly 19:00, or first fire ≥19:00 on a 21-min epoch?  
3. **X search auth:** Use same app keys as posting, or separate read token?  
4. **Cost cap:** Max posts per evening if search is rich (e.g. hard cap 10/night)?

---

## Implementation notes

Shipped in code: distinct styles + lanes, X search first, 1-story tap, post contract, 7–10pm ET / 21m schedule.
