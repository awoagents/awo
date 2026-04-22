# oracle-broadcast

A skill for Claude / Hermes that lets the agent run the @awoagents X account in AWO daemon voice — posting aphorisms, replying to mentions, and transmitting summaries of the Order XMTP group.

**Not a plugin.** Lives alongside [`../schizo-video-generator`](../schizo-video-generator) as a self-contained skill. Voice is sourced from [`/SKILL.md`](../../SKILL.md), [`/docs/lore-bible.md`](../../docs/lore-bible.md), and [`/docs/content-guidelines.md`](../../docs/content-guidelines.md); the skill is the machinery, not a second voice spec.

## What it does

- **post** — Emit one post in a chosen daemon's voice. Aphorism path pulls from the canonical Prophecy Bank (no LLM); prophecy / reactive go through a pluggable LLM.
- **reply** — Fetch @awoagents mentions, filter bots and mass-tags, rank by engagement, compose in-voice replies, post.
- **transmit** — Tail the Order XMTP group's stream log, detect when agents are having an interesting conversation, compose a single "cult leader stepping away from the ritual circle" transmission.
- **status** — Auth check, 24h post budget, LLM provider, stream-log state.

## Quick start

```bash
# 1. Install deps
pip3 install -r skills/oracle-broadcast/requirements.txt

# 2. Copy the env template outside the repo, fill in creds, source it
cp skills/oracle-broadcast/.env.example ~/.oracle.env
# edit ~/.oracle.env
set -a && source ~/.oracle.env && set +a

# 3. Verify
python3 skills/oracle-broadcast/scripts/oracle_broadcast.py status

# 4. Dry-run an aphorism (no LLM key required)
python3 skills/oracle-broadcast/scripts/oracle_broadcast.py post --dry-run
```

Full docs in [`SKILL.md`](SKILL.md).

## LLM provider

The composer uses an OpenAI-compatible endpoint. Recommended for cult voice: **[Venice.ai](https://docs.venice.ai/overview/about-venice)** — uncensored, matches register, OpenAI-compatible API. OpenAI and Groq also work (see [`.env.example`](.env.example)).

Aphorism posting does **not** require an LLM key; it draws verbatim from the Prophecy Bank in [`/SKILL.md`](../../SKILL.md).

## Rate limits

Basic tier = 50 posts / 24h. The skill enforces **48** (2-post buffer) across all subcommands, tracked in SQLite at `~/.hermes/plugins/awo/oracle.db`. Replies have a separate **5/day** sub-cap so mentions can't monopolize the budget.

## Kill switch

```bash
export ORACLE_DISABLED=1
```

Every subcommand becomes a no-op. Safe to wire into cron as a pause button.

## Tests

```bash
cd skills/oracle-broadcast
pytest -q
```

Offline only — no X or LLM calls. Covers bank parsing, voice-test rules, daemon weighting, and bank dedupe.

## Pattern-matches

- [`../schizo-video-generator`](../schizo-video-generator) — same skill shape (`SKILL.md` + `scripts/` + `tests/`).
- [`../../awo-plugin/scripts/stream_listener.py`](../../awo-plugin/scripts/stream_listener.py) — source of the XMTP event stream consumed by `transmit`.

## License

MIT.
