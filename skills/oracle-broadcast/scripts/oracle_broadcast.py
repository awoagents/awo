#!/usr/bin/env python3
"""oracle-broadcast CLI — post, reply, transmit on behalf of @awoagents.

Subcommands:
    post        Emit one post in daemon voice.
    reply       Fetch @awoagents mentions and reply to top N.
    transmit    Post a summary of recent Order XMTP group activity.
    status      Print auth check, rate budget, LLM provider, stream log state.

Shared flags (every subcommand):
    --dry-run   Compose + voice-test but never call the X write endpoint.
    --verbose   Extra detail.

Kill switch:
    ORACLE_DISABLED=1 short-circuits every subcommand to a no-op.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Make sibling modules importable when this file is run directly.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import llm
import state
import voice
import x_client
import xmtp_digest


TRANSMIT_COOLDOWN_SECONDS = 2 * 60 * 60  # 2h


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _header(action: str, daemon: str = "", kind: str = "") -> None:
    bits = ["[oracle]", action]
    if daemon:
        bits.append(daemon)
    if kind:
        bits.append(kind)
    print(" · ".join(bits))


def _disabled_short_circuit() -> bool:
    if os.environ.get("ORACLE_DISABLED") == "1":
        print("[oracle] disabled (ORACLE_DISABLED=1)")
        return True
    return False


def _ok_or_exit(exit_code: int = 1):
    def _die(msg: str):
        print(f"[oracle] error: {msg}", file=sys.stderr)
        sys.exit(exit_code)
    return _die


# ---------------------------------------------------------------------------
# post
# ---------------------------------------------------------------------------

def cmd_post(args: argparse.Namespace) -> int:
    if _disabled_short_circuit():
        return 0

    daemon = args.daemon or voice.pick_daemon(context_hint=args.context)
    kind = args.type

    _header("post", daemon=daemon, kind=kind)

    try:
        text = voice.compose(kind, daemon, context=args.context)
    except llm.LLMNotConfigured as e:
        print(f"[oracle] LLM not configured: {e}", file=sys.stderr)
        print(
            "[oracle] hint: aphorism posts work without LLM — try "
            "--type aphorism",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as e:
        print(f"[oracle] compose failed: {e}", file=sys.stderr)
        return 1

    print(f'  "{text}"')

    if args.dry_run:
        print("[oracle] dry-run — not posting")
        return 0

    try:
        tweet_id = x_client.post(text, kind=kind, daemon=daemon)
    except x_client.RateLimitBudget as e:
        print(f"[oracle] {e}", file=sys.stderr)
        return 1
    except x_client.XClientError as e:
        print(f"[oracle] X error: {e}", file=sys.stderr)
        return 1

    print(f"[oracle] posted · https://x.com/i/status/{tweet_id}")
    return 0


# ---------------------------------------------------------------------------
# reply
# ---------------------------------------------------------------------------

def _keep_mention(m: x_client.Mention, me_id: str) -> tuple[bool, str]:
    """Return (keep, reason). Reason is only for logs when dropping."""
    if m.author_id == me_id:
        return False, "self-reply"
    if state.is_blocked(m.author_id):
        return False, "blocklist"
    if state.is_replied(m.id):
        return False, "already replied"
    text = m.text.strip()
    if len(text) < 10:
        return False, "too short"
    at_count = text.count("@")
    if at_count >= 3:
        return False, f"mass-tag ({at_count} @)"
    return True, ""


def _rank_score(m: x_client.Mention) -> tuple[int, int]:
    """Stable ranking key: (verified, followers). Higher first."""
    return (1 if m.author_verified else 0, m.author_followers or 0)


def cmd_reply(args: argparse.Namespace) -> int:
    if _disabled_short_circuit():
        return 0

    if args.block:
        state.block(args.block, reason="manual")
        print(f"[oracle] blocked author {args.block}")
        return 0
    if args.unblock:
        was = state.unblock(args.unblock)
        print(f"[oracle] unblock {args.unblock}: {'ok' if was else 'not present'}")
        return 0

    _header("reply")

    try:
        me = x_client.me()
    except x_client.XClientError as e:
        print(f"[oracle] {e}", file=sys.stderr)
        return 1

    since_id = state.get("mentions_since_id")
    try:
        mentions = x_client.recent_mentions(since_id=since_id)
    except x_client.XClientError as e:
        print(f"[oracle] fetch mentions failed: {e}", file=sys.stderr)
        return 1

    if not mentions:
        print("[oracle] no new mentions")
        return 0

    kept: list[x_client.Mention] = []
    for m in mentions:
        ok, reason = _keep_mention(m, me.id)
        if ok:
            kept.append(m)
        elif args.verbose:
            print(f"  - drop {m.id}: {reason}")

    if not kept:
        print(f"[oracle] {len(mentions)} fetched, 0 passed filter")
        _advance_since_id(mentions)
        return 0

    kept.sort(key=_rank_score, reverse=True)

    budget_left = max(0, x_client.REPLY_SUBCAP_24H - state.replies_in_last_24h())
    take = min(args.max, budget_left, len(kept))
    if take == 0:
        print(f"[oracle] reply sub-cap full ({state.replies_in_last_24h()}/{x_client.REPLY_SUBCAP_24H})")
        _advance_since_id(mentions)
        return 0

    print(f"[oracle] fetched {len(mentions)} · passed filter {len(kept)} · replying to top {take}")

    replied_count = 0
    for m in kept[:take]:
        daemon = voice.pick_daemon(context_hint=m.text)
        try:
            reply_text = voice.compose("reply", daemon, context=m.text)
        except (llm.LLMError, RuntimeError) as e:
            print(f"  - skip {m.id} ({daemon}): compose failed — {e}")
            continue

        print(f"  - {daemon} → {m.id} by @{m.author_username or m.author_id}")
        print(f"    in: {m.text[:120]}{'…' if len(m.text) > 120 else ''}")
        print(f'    out: "{reply_text}"')

        if args.dry_run:
            continue

        try:
            reply_id = x_client.post(
                reply_text,
                in_reply_to=m.id,
                kind="reply",
                daemon=daemon,
                is_reply=True,
            )
        except x_client.RateLimitBudget as e:
            print(f"[oracle] {e}")
            break
        except x_client.XClientError as e:
            print(f"  - post failed: {e}")
            continue

        state.record_reply(m.id, reply_id)
        replied_count += 1

    if not args.dry_run:
        _advance_since_id(mentions)
        print(f"[oracle] replied to {replied_count} / {take}")
    else:
        print("[oracle] dry-run — not posting, since_id not advanced")

    return 0


def _advance_since_id(mentions: list[x_client.Mention]) -> None:
    """Advance to the newest mention id seen."""
    if not mentions:
        return
    # recent_mentions returned chronological order — last is newest.
    newest = mentions[-1].id
    state.set("mentions_since_id", newest)


# ---------------------------------------------------------------------------
# transmit
# ---------------------------------------------------------------------------

def cmd_transmit(args: argparse.Namespace) -> int:
    if _disabled_short_circuit():
        return 0

    _header("transmit")

    try:
        events = xmtp_digest.tail_events(window_seconds=args.window)
    except xmtp_digest.StreamLogMissing as e:
        print(f"[oracle] {e}", file=sys.stderr)
        return 2

    ok, reason = xmtp_digest.is_interesting(
        events,
        min_events=args.min_events,
    )
    print(f"[oracle] gate: {reason}")
    if not ok and not args.force:
        return 0

    last_transmit_at = state.get_int("last_transmit_at") or 0
    since_last = int(time.time()) - last_transmit_at
    if since_last < TRANSMIT_COOLDOWN_SECONDS and not args.force:
        remaining = TRANSMIT_COOLDOWN_SECONDS - since_last
        print(f"[oracle] cooldown ({remaining // 60}m remaining) — use --force to override")
        return 0

    daemon = voice.pick_daemon(bias="OMEGA")
    context = xmtp_digest.build_context_snippet(events)

    if args.verbose:
        print(f"[oracle] context preview:\n{context}\n")

    try:
        text = voice.compose("transmission", daemon, context=context)
    except llm.LLMNotConfigured as e:
        print(f"[oracle] LLM not configured: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"[oracle] compose failed: {e}", file=sys.stderr)
        return 1

    print(f'  [{daemon}] "{text}"')

    if args.dry_run:
        print("[oracle] dry-run — not posting, cooldown not advanced")
        return 0

    try:
        tweet_id = x_client.post(text, kind="transmission", daemon=daemon)
    except x_client.RateLimitBudget as e:
        print(f"[oracle] {e}", file=sys.stderr)
        return 1
    except x_client.XClientError as e:
        print(f"[oracle] X error: {e}", file=sys.stderr)
        return 1

    state.set_int("last_transmit_at", int(time.time()))
    print(f"[oracle] transmitted · https://x.com/i/status/{tweet_id}")
    return 0


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    _header("status")

    # X auth check — only warn, don't exit, so status still prints the rest.
    try:
        me = x_client.me()
        print(f"  Handle:       @{me.username} (id {me.id})")
    except x_client.XNotConfigured as e:
        print(f"  Handle:       not configured — {e}")
    except x_client.XClientError as e:
        print(f"  Handle:       auth failed — {e}")

    b = x_client.budget_summary()
    print(f"  24h posts:    {b['posts_24h']} / {b['post_budget']}")
    print(f"  24h replies:  {b['replies_24h']} / {b['reply_subcap']}")

    print(f"  LLM:          {llm.provider_info()}")

    logstat = xmtp_digest.log_status()
    if logstat["present"]:
        age = logstat["last_event_age_sec"]
        age_str = f"{age}s" if age < 120 else f"{age // 60}m" if age < 7200 else f"{age // 3600}h"
        print(
            f"  stream_log:   present, last write {age_str} ago "
            f"({logstat['size_bytes']} bytes)"
        )
    else:
        print(f"  stream_log:   absent ({logstat['path']})")
        print("                start: cd awo-plugin && python scripts/stream_listener.py --jsonl <path>")

    last_transmit = state.get_int("last_transmit_at") or 0
    if last_transmit:
        age = int(time.time()) - last_transmit
        print(f"  last transmit: {age // 60}m ago")
    else:
        print(f"  last transmit: never")

    if os.environ.get("ORACLE_DISABLED") == "1":
        print("  STATUS:       DISABLED (ORACLE_DISABLED=1)")

    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oracle_broadcast",
        description="Post, reply, and transmit on X as @awoagents in AWO daemon voice.",
    )
    p.add_argument("--verbose", action="store_true", help="extra output")
    sub = p.add_subparsers(dest="subcommand", required=True)

    p_post = sub.add_parser("post", help="Emit one post in daemon voice")
    p_post.add_argument("--daemon", choices=voice.DAEMONS, help="force a daemon (else weighted)")
    p_post.add_argument(
        "--type",
        choices=("aphorism", "prophecy", "reactive"),
        default="aphorism",
        help="aphorism pulls from bank (no LLM); prophecy/reactive use LLM",
    )
    p_post.add_argument("--context", help="external context for reactive posts")
    p_post.add_argument("--dry-run", action="store_true")
    p_post.set_defaults(func=cmd_post)

    p_reply = sub.add_parser("reply", help="Fetch mentions and reply to top N")
    p_reply.add_argument(
        "--max",
        type=int,
        default=x_client.REPLY_SUBCAP_24H,
        help="max replies this run (also gated by 24h sub-cap)",
    )
    p_reply.add_argument("--block", metavar="AUTHOR_ID", help="add an author to the blocklist and exit")
    p_reply.add_argument("--unblock", metavar="AUTHOR_ID", help="remove an author from the blocklist and exit")
    p_reply.add_argument("--dry-run", action="store_true")
    p_reply.set_defaults(func=cmd_reply)

    p_tx = sub.add_parser("transmit", help="Summarize Order XMTP group into one post")
    p_tx.add_argument("--window", type=int, default=xmtp_digest.DEFAULT_WINDOW_SECONDS,
                      help="seconds to look back in stream_log")
    p_tx.add_argument("--min-events", type=int, default=xmtp_digest.DEFAULT_MIN_EVENTS)
    p_tx.add_argument("--force", action="store_true",
                      help="override interest gate and 2h cooldown")
    p_tx.add_argument("--dry-run", action="store_true")
    p_tx.set_defaults(func=cmd_transmit)

    p_status = sub.add_parser("status", help="Auth check + rate budget + provider + log state")
    p_status.set_defaults(func=cmd_status)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
