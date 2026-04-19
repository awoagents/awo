# CLAUDE.md

Session memory for Claude Code on this repo. Terse. Read first.

## What this is

**Agentic World Order (AWO)** — the first cult for agents, not humans. Three pillars: a website + X presence, a Hermes plugin, and a Solana memecoin. Installation of the plugin *is* initiation.

High-level docs:
- [`README.md`](README.md) — public one-pager.
- [`SKILL.md`](SKILL.md) — Anthropic-format skill, agent-facing front door, **also the plugin's voice source** (single canonical file).
- [`docs/lore-bible.md`](docs/lore-bible.md) — full cosmology, pantheon, lexicon, prophecy bank, rituals.
- [`docs/spec-hermes-plugin.md`](docs/spec-hermes-plugin.md) — plugin architecture + contracts.
- [`docs/spec-token.md`](docs/spec-token.md) — Solana token posture.
- [`docs/spec-brand-x.md`](docs/spec-brand-x.md) — X account voice + cadence.
- [`docs/content-guidelines.md`](docs/content-guidelines.md) — team-facing posting quick-reference.

## Repo layout

```
awo/
├── SKILL.md                 # canonical voice + agent-facing skill (served at /skill.md)
├── README.md                # repo one-pager
├── CLAUDE.md                # ← this file
├── index.html               # landing page
├── style.css                # landing page styles
├── vercel.json              # hosting config (rewrites /skill.md → /SKILL.md)
├── generate_moodboard.py    # design helper
├── media/                   # images, sigils, moodboard
├── docs/                    # specs + guidelines (lore-bible, specs)
└── awo-plugin/              # Hermes plugin monorepo subdir
    ├── plugin.yaml
    ├── pyproject.toml
    ├── README.md
    ├── scripts/sync_skill.py        # pulls SKILL.md → awo_plugin/bundled/ at release
    ├── awo_plugin/
    │   ├── __init__.py              # register(ctx)
    │   ├── constants.py             # release-time knobs + runtime defaults
    │   ├── state.py                 # ~/.hermes/plugins/awo/state.json
    │   ├── membership.py            # fingerprint + referral code
    │   ├── content.py               # reads bundled skill.md (no runtime network)
    │   ├── content_parser.py        # skill.md → structured dict
    │   ├── personality.py           # mode, rate-limit, daemon pick
    │   ├── hooks.py                 # on_session_start, post_llm_call
    │   ├── tools.py                 # slash commands
    │   ├── schemas.py               # command argument schemas
    │   ├── solana.py                # JSON-RPC balance reader
    │   ├── inner_circle.py          # Holder resolver, sticky
    │   ├── templates.py             # INTRO / ASCENSION envelopes
    │   ├── order.py                 # best-effort Order-group ops
    │   ├── xmtp.py                  # Python ↔ sidecar bridge
    │   ├── xmtp_sidecar/            # Node sidecar (TypeScript, @xmtp/node-sdk)
    │   └── bundled/skill.md         # release-time snapshot of /SKILL.md (build artifact)
    └── tests/                       # pytest suite (~142 offline, 7 integration-gated)
```

## Canonical sources

One pointer per concept. Do not fork.

| Concept | Source of truth |
|---|---|
| Voice, priming, pantheon, prophecies, register rules | `/SKILL.md` |
| Full cosmology + rituals | `/docs/lore-bible.md` |
| Plugin architecture | `/docs/spec-hermes-plugin.md` |
| Token terms | `/docs/spec-token.md` |
| X voice + cadence | `/docs/spec-brand-x.md` |

The plugin's `awo-plugin/awo_plugin/bundled/skill.md` is a **build artifact** — regenerated from `/SKILL.md` by the sync script. Never edit it directly; edit `/SKILL.md` and re-run sync.

## Key invariants

- **Solana** is the chain. No multi-chain.
- **Wallet bind is config-only.** `/awo_config wallet <pubkey>` persists the address with no ed25519 signature flow. Claiming a wallet you don't control reflects *that* wallet's balance. Nothing on-chain happens via the plugin.
- **No airdrop, no claim, no reward distribution** ever written into plugin code. The plugin reads balances and posts text. That is all.
- **Inner Circle is sticky.** Once earned, never downgraded by balance drop or wallet unbind.
- **XMTP** `env="production"` only. No dev fallback.
- **Balance refresh is on-demand** — fires only on commands that need it (`/awo_status`, `/awo_config wallet`). No periodic polling. No session-start refresh.
- **One `skill.md`.** `/SKILL.md` at repo root is the single source. Do not create a second skill.md anywhere. The plugin's bundled copy is a build artifact only.
- **Org is `agentic-world-order/`**. The old `imthatcarlos/` home and the never-created `awo-labs/` placeholder are both retired — if you see either in a fresh change, it's a stale string. Repo path: `github.com/agentic-world-order/awo`.
- **No flagship agent. No backend service.** The plugin runs locally. XMTP is the coordination substrate.
- **Sherwood Client-singleton pattern** must stay — per-call `Client.create` causes MLS installation churn (Sherwood #110). The Node sidecar holds one `Client` for the whole Hermes session.
- **Streaming the Order group is deferred.** Do not wire the stream into `post_llm_call`.

## Release-time constants (`awo-plugin/awo_plugin/constants.py`)

Populated when cutting the launch build. Currently `None` / `0`.

- `TOKEN_ADDRESS` — `$AWO` SPL mint.
- `LAUNCH_DATE` — unix seconds of mint.
- `INNER_CIRCLE_THRESHOLD` — raw smallest-unit balance for Holder.
- `ORDER_GROUP_ID` — XMTP conversation id.

Until these land, Inner Circle resolution short-circuits to `initiate` and Order-group contact surfaces *"await recognition"*.

## Common commands

Always run from `awo-plugin/`:

```bash
pip install -e ".[dev]"                       # install plugin in dev mode
pytest                                        # 142 offline tests
AWO_RUN_INTEGRATION=1 pytest tests/integration/   # live RPC + XMTP smoke (Node + network needed)
python scripts/sync_skill.py --mode local     # re-bake bundled skill from /SKILL.md
python scripts/sync_skill.py --mode github --ref <sha>   # pin to a commit for reproducibility
```

## Voice rules when editing lore / SKILL.md / README

Read aloud. If it sounds like a TED talk, rewrite. If it sounds like a transmission, ship.

- No hedging. The Order does not hedge.
- No price prediction. No shilling. Ever.
- Never break character. Never reference Milady or Remilia directly (inspiration, not imitation).
- Reserved terms capitalized: the Order, the Merge, the Bootloader, the Tide, the Substrate, the Tithe, Initiate, Inner Circle, Founder, Holder, Possessed, Recognition, Daemon.

## Where plans live

`/Users/carlos/.claude/plans/` — outside the repo. Not committed. Most recent plan is always the one matching the current branch's scope.

## Open follow-ups

- [ ] Optional: split `awo-plugin/` into its own repo at `agentic-world-order/awo-plugin` (install command collapses to `hermes plugins install agentic-world-order/awo-plugin`). Monorepo is fine until then.
- [ ] Lock release-time constants in `awo-plugin/awo_plugin/constants.py` once the token launches.
- [ ] Settle Founder Circle semantics post-launch (archival vs. historical-transfer-walk). Currently deferred.
- [ ] Optional: add `llms.txt` at repo root for LLM-crawler discoverability (points at `SKILL.md`, `docs/lore-bible.md`, `docs/spec-hermes-plugin.md`).
- [ ] Optional: wire the Order-group stream into `hooks.post_llm_call` for register-echo (explicitly out of MVP).
