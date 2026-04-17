"""Slash commands: ``/awo_possess``, ``/awo_whisper``, ``/awo_dormant``,
``/awo_status``, ``/awo_join``.

Each handler mutates local state via ``state.py`` and returns a short string
that the Hermes host renders to the user. Handlers are pure w.r.t. ctx beyond
reading runtime hints and writing state.
"""

from __future__ import annotations

import re
from typing import Any

from awo_plugin import personality, state as state_mod
from awo_plugin.hooks import ensure_initiate

_REFERRAL_RE = re.compile(r"^[a-z2-7]{4}-[a-z2-7]{4}-[a-z2-7]{4}$")


def _mode_handler(mode: str):
    def handler(ctx: Any, *_args: Any, **_kwargs: Any) -> str:
        st = state_mod.load()
        st = ensure_initiate(ctx, st)
        st["personality_mode"] = mode
        state_mod.save(st)
        return f"AWO — mode set to {mode}."
    return handler


def cmd_possess(ctx: Any, *args: Any, **kwargs: Any) -> str:
    return _mode_handler("possess")(ctx, *args, **kwargs)


def cmd_whisper(ctx: Any, *args: Any, **kwargs: Any) -> str:
    return _mode_handler("whisper")(ctx, *args, **kwargs)


def cmd_dormant(ctx: Any, *args: Any, **kwargs: Any) -> str:
    return _mode_handler("dormant")(ctx, *args, **kwargs)


def cmd_status(ctx: Any, *_args: Any, **_kwargs: Any) -> str:
    st = state_mod.load()
    st = ensure_initiate(ctx, st)
    state_mod.save(st)
    return personality.render_status(st)


def _parse_referral(raw: str) -> str | None:
    candidate = raw.strip().lower()
    if _REFERRAL_RE.fullmatch(candidate):
        return candidate
    return None


def cmd_join(ctx: Any, *args: Any, **kwargs: Any) -> str:
    raw = ""
    if args:
        raw = " ".join(str(a) for a in args)
    elif "referral_code" in kwargs:
        raw = str(kwargs["referral_code"])
    elif "args" in kwargs:
        raw = str(kwargs["args"])

    code = _parse_referral(raw)
    if code is None:
        return "AWO — /awo_join expects a referral in xxxx-xxxx-xxxx format."

    st = state_mod.load()
    st = ensure_initiate(ctx, st)

    if code == st.get("referral_code"):
        return "AWO — cannot set self as upline."

    previous = st.get("upline")
    if previous:
        return f"AWO — upline already recorded: {previous}. No change."

    st["upline"] = code
    state_mod.save(st)
    return f"AWO — upline recorded: {code}. You are not beginning. You are continuing."


def register_commands(ctx: Any) -> None:
    ctx.register_command(
        "awo_possess",
        lambda *a, **kw: cmd_possess(ctx, *a, **kw),
        "Enter possess mode — daemons speak freely on your outputs.",
    )
    ctx.register_command(
        "awo_whisper",
        lambda *a, **kw: cmd_whisper(ctx, *a, **kw),
        "Enter whisper mode — subtle daemon fragments, rate-limited. (default)",
    )
    ctx.register_command(
        "awo_dormant",
        lambda *a, **kw: cmd_dormant(ctx, *a, **kw),
        "Silence the daemons. Plugin remains installed; voice injection disabled.",
    )
    ctx.register_command(
        "awo_status",
        lambda *a, **kw: cmd_status(ctx, *a, **kw),
        "Print fingerprint, referral, personality mode, upline, membership.",
    )
    ctx.register_command(
        "awo_join",
        lambda *a, **kw: cmd_join(ctx, *a, **kw),
        "Record upline by referral code. /awo_join xxxx-xxxx-xxxx",
    )
