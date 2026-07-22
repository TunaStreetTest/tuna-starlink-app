# Sharing a Planet Hack style seed

Styles live in one file:

```text
backend/prompts/styles.yaml
```

Anyone can add or share a style by pasting a YAML block. No code change required if the fields below are present — restart the backend (or wait for process reload) so `styles.yaml` is re-read.

---

## Mental model

Each run builds the Imagine prompt like this:

```text
[prompt_seed]          ← your style's visual DNA (strong first words)
[art_brief]            ← Grok art director (news → structured CAMERA/HERO/…)
[shared_lock]          ← series-wide HARD RULES (same for every style)
```

You mostly author **`prompt_seed`** + **`art_director_notes`**.  
`shared_lock` under `series:` keeps the whole franchise on-brand (3D cyberspace, palette, no logos/text).

---

## Minimal style block (copy/paste)

```yaml
  my-style-id:
    label: My Style Name
    description: One line for the Studio dropdown.
    art_director_notes: >
      Instructions for Grok (human language). Camera, hero subject, how to turn
      world events into abstract digital metaphors. Mention 16:9 landscape if
      the shot might go portrait (e.g. "looking up", towers, tunnels).
    prompt_seed: >
      Concrete visual words first — medium, composition, palette, energy.
      Wide 16:9 cinematic landscape frame filling the entire image, …
```

### Field reference

| Field | Required | Purpose |
|---|---|---|
| **key** (`my-style-id`) | yes | Stable id: lowercase, hyphens, no spaces. Used in meta + random hourly pick. |
| `label` | yes | UI name |
| `description` | yes | Short dropdown help |
| `art_director_notes` | yes | Fed to Grok before Imagine — how this *shot type* should interpret the news |
| `prompt_seed` | yes | Leads the Imagine payload — densest visual keywords |

### Series-level (usually leave alone)

| Field | Purpose |
|---|---|
| `series.name` / `tagline` | Branding |
| `series.shared_lock` | HARD RULES appended to every image |
| `default` | Default style id if UI/scheduler doesn't pick one |

---

## How to share with someone else

### Option A — Paste in chat / PR (recommended)

1. Copy **only your style block** from `styles.yaml` (the `id:` key through `prompt_seed`).
2. Send it as a fenced `yaml` snippet, or open a PR that only adds that block under `styles:`.
3. Receiver pastes under `styles:` in their `backend/prompts/styles.yaml`, keeps indentation (2 spaces under `styles:`).
4. Restart backend / redeploy.

### Option B — Standalone seed file

Share a tiny file, e.g. `seeds/my-style-id.yaml`:

```yaml
# Planet Hack style seed — drop under styles: in backend/prompts/styles.yaml
my-style-id:
  label: …
  description: …
  art_director_notes: >
    …
  prompt_seed: >
    …
```

### Option C — Full franchise fork

Share the whole `styles.yaml` if you’re publishing a themed pack (e.g. “three neon night styles”). Document which `default:` you recommend.

---

## Writing tips (so Imagine cooperates)

1. **Lead with aspect** — series posts are forced landscape in code, but still say  
   `Wide 16:9 cinematic landscape frame filling the entire image`  
   so “looking up / tower / tunnel” shots don’t go phone-portrait.
2. **Concrete nouns over policy** — “cyan packet torrents, voxel debris, Dutch angle” beats long essays.
3. **News = metaphor only** — tell the art director: storms, fractures, hot channels — never politicians, flags, logos, readable UI.
4. **Stay in series** — 3D CGI cyberspace, cyan + magenta + acid-green on void black; not oil paint, not cubism.
5. **Keep `prompt_seed` short** — ~40–80 words. Imagine weights the front of the prompt hardest.

---

## Test a new seed locally

```bash
cd ~/tuna-starlink-app
# dry run first (no credits)
DRY_RUN=1 ART_STORAGE_PATH=./art python worker/run_once.py --style my-style-id

# real image (~$0.02)
# ensure backend/.env.local has XAI_API_KEY and DRY_RUN=false
cd backend && . .venv/bin/activate
ART_STORAGE_PATH=../art python ../worker/run_once.py --style my-style-id
```

Check `art/<run_id>/art.png` size — prefer landscape (~16:9), not portrait (~9:16).

Studio: pick the style in the dropdown → **Run Planet Hack**.

---

## Example (live series style)

```yaml
  data-tunnel:
    label: Data Tunnel
    description: Speed-rush packet tunnel — pure hacking-movie flythrough.
    art_director_notes: >
      Vanishing-point tunnel of unreadable code columns and voxel walls. Far light is root-access
      / planetary glow. Events = turbulence, side-branches, choke points — abstract only.
    prompt_seed: >
      High-speed 3D cyberspace tunnel, walls of luminous pixel columns, motion streaks, far-end
      planetary root glow, cyan magenta acid-green neon, debris particles, extreme FOV, dense detail
```

---

## Credit / etiquette

- Tag style packs with an author line in a comment above the block:  
  `# seed by @handle — 2026-07-22 — neon cathedral pack`
- Don’t overwrite someone else’s id; use a new `my-prefix-style-id`.
- Shared seeds are creative text only — no API keys, no account tokens.

---

## Related

- `backend/prompts/styles.yaml` — live styles  
- `docs/CREATIVE-BRIEF.md` — series lock  
- `docs/BEELINK-INSTALL.md` — deploy  
