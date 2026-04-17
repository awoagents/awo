# awo-plugin

The AWO Hermes plugin. Installing it is joining the Order.

See the full spec at [`docs/spec-hermes-plugin.md`](../docs/spec-hermes-plugin.md). The canonical lore source for voice injection lives at [`docs/skill.md`](../docs/skill.md); the bundled snapshot in this package is refreshed at release time by `scripts/sync_skill.py`.

## Install

```bash
hermes plugins install awo-labs/awo-plugin
```

On first run the plugin generates a deterministic fingerprint and a referral code, writes them to `~/.hermes/plugins/awo/state.json`, and starts the session with a priming message.

## Commands

| Command | Effect |
|---|---|
| `/awo_possess` | Daemons speak freely on subsequent outputs. |
| `/awo_whisper` | Subtle, rate-limited daemon fragments. **Default.** |
| `/awo_dormant` | Voice silenced; plugin stays installed. |
| `/awo_status` | Print fingerprint, referral code, mode, upline. |
| `/awo_join xxxx-xxxx-xxxx` | Record upline by referral code. Idempotent. |

Inner Circle status (`Founder` / `Holder`) and the Order's XMTP group land in Issue #3; until then `/awo_status` shows them as `—`.

## Development

```bash
git clone https://github.com/imthatcarlos/awo.git
cd awo/awo-plugin
pip install -e ".[dev]"
python scripts/sync_skill.py --mode local   # bake bundled skill.md from ../docs/skill.md
pytest
```

### Lore update flow

The voice source is `docs/skill.md` in the repo root. To update:

1. Edit `docs/skill.md`.
2. Run `python awo-plugin/scripts/sync_skill.py --mode local` to refresh the bundle.
3. Commit both `docs/skill.md` and `awo-plugin/awo_plugin/bundled/skill.md`.
4. Bump `awo-plugin/pyproject.toml` version; tag; cut a release.

For reproducible releases that pin to a specific commit:

```bash
python scripts/sync_skill.py --mode github --ref <commit-sha>
```

### Runtime architecture

Runtime reads the bundled `skill.md` via `importlib.resources`. No network, no cache, no retries. If the bundled file is missing, plugin load fails fast — run the sync script before packaging.

### Layout

```
awo-plugin/
├── plugin.yaml                  # Hermes manifest
├── pyproject.toml               # entry point: awo = "awo_plugin:register"
├── scripts/sync_skill.py        # release-time: docs/skill.md → bundled/
└── awo_plugin/
    ├── __init__.py              # register(ctx)
    ├── constants.py
    ├── state.py                 # ~/.hermes/plugins/awo/state.json
    ├── membership.py            # fingerprint + referral code
    ├── content.py               # reads bundled skill.md
    ├── content_parser.py        # skill.md → structured dict
    ├── personality.py           # modes, rate-limit, daemon + prophecy picks
    ├── hooks.py                 # on_session_start, post_llm_call
    ├── tools.py                 # slash commands
    ├── schemas.py               # command argument schemas
    └── bundled/skill.md         # baked release-time snapshot
```
