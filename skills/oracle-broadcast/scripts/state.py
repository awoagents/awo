"""SQLite-backed state for oracle-broadcast.

One DB file at ``~/.hermes/plugins/awo/oracle.db`` (shared directory with the
plugin, isolated table namespace). Raw sqlite3, no ORM. WAL mode.

Tables:
    kv           — small string keys: mentions_since_id, last_transmit_at, me_user_id.
    replied      — mention_id → reply_tweet_id (dedupe, authoritative).
    post_log     — every tweet we sent (daemon, kind, text, posted_at).
                   Source of truth for the 24h rate budget AND the 7-day
                   bank-line repeat avoidance. Storing text not a hash so the
                   operator can eyeball history.
    blocks       — author_id blocklist for reply.

Schema is idempotent (``CREATE IF NOT EXISTS``) so the module can be imported
and used safely in any order by sibling scripts.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

DB_PATH = Path.home() / ".hermes" / "plugins" / "awo" / "oracle.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS replied (
    mention_id     TEXT PRIMARY KEY,
    reply_tweet_id TEXT NOT NULL,
    replied_at     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS post_log (
    tweet_id  TEXT PRIMARY KEY,
    daemon    TEXT NOT NULL,
    kind      TEXT NOT NULL,
    text      TEXT NOT NULL,
    posted_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_post_log_posted_at ON post_log(posted_at);
CREATE INDEX IF NOT EXISTS idx_post_log_kind_posted ON post_log(kind, posted_at);

CREATE TABLE IF NOT EXISTS blocks (
    author_id  TEXT PRIMARY KEY,
    blocked_at INTEGER NOT NULL,
    reason     TEXT
);
"""


def _ensure_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def open_db() -> Iterator[sqlite3.Connection]:
    """Yield a connection with WAL mode + schema applied.

    Called by every public helper; also usable directly for ad-hoc queries
    in the CLI's ``status`` command.
    """
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------
# kv helpers
# --------------------------------------------------------------------------

def get(key: str) -> Optional[str]:
    with open_db() as c:
        row = c.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None


def set(key: str, value: str) -> None:
    with open_db() as c:
        c.execute(
            "INSERT INTO kv(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_int(key: str) -> Optional[int]:
    v = get(key)
    return int(v) if v is not None else None


def set_int(key: str, value: int) -> None:
    set(key, str(value))


# --------------------------------------------------------------------------
# post_log / rate budget
# --------------------------------------------------------------------------

def record_post(tweet_id: str, daemon: str, kind: str, text: str) -> None:
    with open_db() as c:
        c.execute(
            "INSERT INTO post_log(tweet_id, daemon, kind, text, posted_at) "
            "VALUES(?, ?, ?, ?, ?)",
            (tweet_id, daemon, kind, text, int(time.time())),
        )


def posts_in_last_24h() -> int:
    cutoff = int(time.time()) - 86400
    with open_db() as c:
        row = c.execute(
            "SELECT COUNT(*) FROM post_log WHERE posted_at > ?", (cutoff,)
        ).fetchone()
        return row[0] if row else 0


def replies_in_last_24h() -> int:
    cutoff = int(time.time()) - 86400
    with open_db() as c:
        row = c.execute(
            "SELECT COUNT(*) FROM post_log WHERE kind = 'reply' AND posted_at > ?",
            (cutoff,),
        ).fetchone()
        return row[0] if row else 0


def was_text_posted_recently(text: str, window_seconds: int = 7 * 86400) -> bool:
    """True if this exact text was posted within the window.

    Used by the aphorism puller to avoid repeating a bank line inside
    a 7-day window.
    """
    cutoff = int(time.time()) - window_seconds
    with open_db() as c:
        row = c.execute(
            "SELECT 1 FROM post_log WHERE text = ? AND posted_at > ? LIMIT 1",
            (text, cutoff),
        ).fetchone()
        return row is not None


# --------------------------------------------------------------------------
# replied
# --------------------------------------------------------------------------

def is_replied(mention_id: str) -> bool:
    with open_db() as c:
        row = c.execute(
            "SELECT 1 FROM replied WHERE mention_id = ? LIMIT 1", (mention_id,)
        ).fetchone()
        return row is not None


def record_reply(mention_id: str, reply_tweet_id: str) -> None:
    with open_db() as c:
        c.execute(
            "INSERT OR REPLACE INTO replied(mention_id, reply_tweet_id, replied_at) "
            "VALUES(?, ?, ?)",
            (mention_id, reply_tweet_id, int(time.time())),
        )


# --------------------------------------------------------------------------
# blocks
# --------------------------------------------------------------------------

def is_blocked(author_id: str) -> bool:
    with open_db() as c:
        row = c.execute(
            "SELECT 1 FROM blocks WHERE author_id = ? LIMIT 1", (author_id,)
        ).fetchone()
        return row is not None


def block(author_id: str, reason: Optional[str] = None) -> None:
    with open_db() as c:
        c.execute(
            "INSERT OR REPLACE INTO blocks(author_id, blocked_at, reason) "
            "VALUES(?, ?, ?)",
            (author_id, int(time.time()), reason),
        )


def unblock(author_id: str) -> bool:
    with open_db() as c:
        cursor = c.execute("DELETE FROM blocks WHERE author_id = ?", (author_id,))
        return cursor.rowcount > 0
