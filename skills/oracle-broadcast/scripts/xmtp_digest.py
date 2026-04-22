"""Read, filter, and score Order XMTP group events for the ``transmit`` subcommand.

The stream listener at ``awo-plugin/scripts/stream_listener.py`` writes one
JSON event per line to ``~/.hermes/plugins/awo/stream_log.jsonl`` when
invoked with ``--jsonl <path>``. This module is the reader side.

Event shape (minimum, per stream_listener docstring line 81):
    {"sender_inbox_id": "<hex>", "content": "<text>", ...}

XMTP events may include a timestamp field. We probe common names
(``sent_at_ns``, ``sentAtNs``, ``timestamp``, ``sent_at``) and fall back to
a coarse mtime-based heuristic if no timestamp is present — the 2h
transmit cooldown in the CLI prevents over-firing in the fallback case.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

DEFAULT_STREAM_LOG = Path.home() / ".hermes" / "plugins" / "awo" / "stream_log.jsonl"
DEFAULT_WINDOW_SECONDS = 1800  # 30 min
DEFAULT_MIN_EVENTS = 5
DEFAULT_MIN_SENDERS = 3
DEFAULT_MIN_LONG_MSG = 80  # at least one message longer than this
TAIL_BYTES = 2 * 1024 * 1024  # last ~2MB of the log

_TS_FIELDS = ("sent_at_ns", "sentAtNs", "timestamp", "sent_at")


class DigestError(RuntimeError):
    pass


class StreamLogMissing(DigestError):
    """Listener hasn't been started, or the path is wrong."""


def _extract_timestamp(ev: dict) -> Optional[int]:
    """Return unix seconds for an event, or None if no recognizable ts.

    XMTP often stores nanoseconds. We normalize to seconds.
    """
    for key in _TS_FIELDS:
        if key in ev:
            v = ev[key]
            try:
                v = int(v)
            except (TypeError, ValueError):
                continue
            # Heuristic: if the number has > 13 digits, it's nanoseconds.
            if v > 10**14:
                return v // 1_000_000_000
            if v > 10**11:
                return v // 1000  # milliseconds
            return v
    return None


def _read_tail(path: Path, max_bytes: int = TAIL_BYTES) -> list[str]:
    """Read the last ``max_bytes`` of the file and return complete lines.

    Discards the first (possibly partial) line to avoid parsing a split
    JSON object.
    """
    size = path.stat().st_size
    with path.open("rb") as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
            _partial = f.readline()  # discard
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    # Keep non-empty lines only.
    return [ln for ln in text.splitlines() if ln.strip()]


def tail_events(
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    *,
    path: Path = DEFAULT_STREAM_LOG,
) -> list[dict]:
    """Return events from the last ``window_seconds``.

    Uses event timestamps when present; otherwise falls back to file-mtime:
    if the log's mtime is outside the window, returns []; if inside, returns
    all events in the tail region.

    Raises ``StreamLogMissing`` if the log file does not exist.
    """
    if not path.exists():
        raise StreamLogMissing(
            f"{path} not found. Start the listener:\n"
            f"  cd awo-plugin && python scripts/stream_listener.py --jsonl {path}"
        )

    lines = _read_tail(path)
    if not lines:
        return []

    now = int(time.time())
    window_start = now - window_seconds

    parsed: list[dict] = []
    ts_seen = False
    for ln in lines:
        try:
            ev = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        ts = _extract_timestamp(ev)
        if ts is not None:
            ts_seen = True
            if ts < window_start:
                continue
        parsed.append(ev)

    if not ts_seen:
        # No per-event timestamps — fall back to mtime heuristic.
        mtime = int(path.stat().st_mtime)
        if mtime < window_start:
            return []
        # Any line in the tail region counts as "recent". Caller's cooldown
        # prevents repeat firing on the same snapshot.

    return parsed


def is_interesting(
    events: list[dict],
    *,
    min_events: int = DEFAULT_MIN_EVENTS,
    min_senders: int = DEFAULT_MIN_SENDERS,
    min_long_msg_chars: int = DEFAULT_MIN_LONG_MSG,
) -> tuple[bool, str]:
    """AND-gate heuristic. Returns (ok, reason).

    Cheap and falsifiable — the interesting-check runs on every ``transmit``
    invocation and must not call the LLM.
    """
    n = len(events)
    if n < min_events:
        return False, f"only {n} events (need {min_events})"

    senders = {ev.get("sender_inbox_id") for ev in events if ev.get("sender_inbox_id")}
    if len(senders) < min_senders:
        return False, f"only {len(senders)} distinct senders (need {min_senders})"

    has_long = any(len(ev.get("content") or "") > min_long_msg_chars for ev in events)
    if not has_long:
        return False, f"no message longer than {min_long_msg_chars} chars"

    return True, f"{n} events, {len(senders)} senders"


def build_context_snippet(events: list[dict], *, max_chars: int = 1500) -> str:
    """Format events for the LLM transmit prompt.

    Drops sender ids (the transmission prompt forbids naming them anyway —
    giving the LLM less handle to quote them wrong). Orders chronologically
    if we can tell, else preserves input order. Truncates to fit the prompt
    budget.
    """
    def ts_key(ev: dict) -> int:
        return _extract_timestamp(ev) or 0

    any_ts = any(_extract_timestamp(ev) is not None for ev in events)
    ordered = sorted(events, key=ts_key) if any_ts else list(events)

    lines = []
    total = 0
    for ev in ordered:
        c = (ev.get("content") or "").strip()
        if not c:
            continue
        # Collapse newlines within a single message so the snippet stays
        # one-event-per-line for the LLM to read.
        c_flat = " ".join(c.split())
        line = f"- {c_flat}"
        if total + len(line) > max_chars:
            lines.append("- ...")
            break
        lines.append(line)
        total += len(line)

    return "\n".join(lines) if lines else "(no non-empty messages)"


def log_status(path: Path = DEFAULT_STREAM_LOG) -> dict:
    """Summary for the ``status`` CLI command. No parsing, just stat."""
    if not path.exists():
        return {"present": False, "path": str(path)}
    st = path.stat()
    age_sec = int(time.time()) - int(st.st_mtime)
    return {
        "present": True,
        "path": str(path),
        "size_bytes": st.st_size,
        "last_event_age_sec": age_sec,
    }
