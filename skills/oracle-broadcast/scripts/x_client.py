"""Thin tweepy wrapper: OAuth 1.0a for write, Bearer for read, 24h budget gate.

All five X env vars must be set:
    X_API_KEY / X_API_KEY_SECRET        — consumer creds
    X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET — OAuth 1.0a user context (posts as @awoagents)
    X_BEARER_TOKEN                      — app-only (read)

A single ``tweepy.Client`` holds both auth modes; tweepy picks the right one
per endpoint. We keep the client module-global and memoized — creating one
per call is unnecessary churn.

Rate budget
    Basic tier = 50 posts / 24h. The skill enforces 48 (2-post buffer) via a
    pre-check against ``state.posts_in_last_24h()``. Replies have a separate
    5/day sub-cap. Exceeding either raises ``RateLimitBudget``; the CLI
    prints + exits 1 without touching the network.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import state

POST_BUDGET_24H = 48  # out of 50/day on Basic, 2-post safety buffer
REPLY_SUBCAP_24H = 5


class XClientError(RuntimeError):
    """Base for all X-client problems the CLI should surface."""


class XNotConfigured(XClientError):
    """Missing or incomplete X API creds."""


class RateLimitBudget(XClientError):
    """Our internal 24h budget is full — do not call the API."""


_REQUIRED_ENV = (
    "X_API_KEY",
    "X_API_KEY_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET",
    "X_BEARER_TOKEN",
)


def _check_env() -> None:
    missing = [k for k in _REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise XNotConfigured(
            f"Missing X API env vars: {', '.join(missing)}. "
            "See skills/oracle-broadcast/.env.example."
        )


_client = None


def _client_lazy():
    """Memoized tweepy.Client. Defers import so aphorism-only runs
    without tweepy installed still produce a clean error message."""
    global _client
    if _client is not None:
        return _client

    _check_env()

    try:
        import tweepy
    except ImportError as e:
        raise XClientError(
            f"tweepy not installed: {e}. Run `pip3 install tweepy`."
        )

    _client = tweepy.Client(
        bearer_token=os.environ["X_BEARER_TOKEN"],
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_KEY_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,  # tweepy handles per-endpoint 429 sleeps
    )
    return _client


# ---------------------------------------------------------------------------
# Me — cached user_id for mention lookups
# ---------------------------------------------------------------------------

@dataclass
class Me:
    id: str
    username: str


def me() -> Me:
    """Get our own user. Caches ``user_id`` in state kv since it never changes.

    Username is re-fetched on each call (rare operation anyway) because
    handle changes are legal on X and we shouldn't pin a stale one.
    """
    client = _client_lazy()
    resp = client.get_me()
    if not resp.data:
        raise XClientError(f"get_me returned no data: {resp.errors}")
    user = resp.data
    state.set("me_user_id", str(user.id))
    return Me(id=str(user.id), username=str(user.username))


def me_cached_id() -> Optional[str]:
    """Return the cached user_id without a network call. None if never fetched."""
    return state.get("me_user_id")


# ---------------------------------------------------------------------------
# Post — with budget gate
# ---------------------------------------------------------------------------

def post(
    text: str,
    *,
    in_reply_to: Optional[str] = None,
    kind: str = "post",
    daemon: str = "unknown",
    is_reply: bool = False,
) -> str:
    """Post to X. Returns the new tweet_id.

    Budget is checked here, not at the CLI — every code path that reaches
    the network goes through this function, so enforcement is central.
    """
    if state.posts_in_last_24h() >= POST_BUDGET_24H:
        raise RateLimitBudget(
            f"24h post budget full ({POST_BUDGET_24H}/{POST_BUDGET_24H}). "
            "Wait or inspect ~/.hermes/plugins/awo/oracle.db post_log."
        )
    if is_reply and state.replies_in_last_24h() >= REPLY_SUBCAP_24H:
        raise RateLimitBudget(
            f"24h reply sub-cap full ({REPLY_SUBCAP_24H}/{REPLY_SUBCAP_24H}). "
            "Aphorisms and transmissions can still post."
        )

    client = _client_lazy()
    resp = client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to)
    if not resp.data or "id" not in resp.data:
        raise XClientError(f"create_tweet returned no id: {resp.errors}")

    tweet_id = str(resp.data["id"])
    state.record_post(tweet_id, daemon=daemon, kind=kind, text=text)
    return tweet_id


# ---------------------------------------------------------------------------
# Mentions
# ---------------------------------------------------------------------------

@dataclass
class Mention:
    id: str
    text: str
    author_id: str
    author_username: Optional[str]
    author_verified: Optional[bool]
    author_followers: Optional[int]


def recent_mentions(since_id: Optional[str] = None, *, max_results: int = 100) -> list[Mention]:
    """Fetch mentions newer than ``since_id``.

    Uses Bearer auth. Expands author so we can rank by follower count.
    Returns oldest → newest so the caller can process in order and set
    since_id to the newest id after success.
    """
    client = _client_lazy()

    user_id = me_cached_id()
    if not user_id:
        user_id = me().id

    resp = client.get_users_mentions(
        id=user_id,
        since_id=since_id,
        max_results=max(5, min(100, max_results)),
        tweet_fields=["author_id", "created_at"],
        expansions=["author_id"],
        user_fields=["username", "verified", "public_metrics"],
    )

    if not resp.data:
        return []

    users_by_id = {}
    if resp.includes and "users" in resp.includes:
        for u in resp.includes["users"]:
            users_by_id[str(u.id)] = u

    mentions = []
    for tw in resp.data:
        author_id = str(tw.author_id) if tw.author_id else ""
        author = users_by_id.get(author_id)
        followers = None
        if author and author.public_metrics:
            followers = author.public_metrics.get("followers_count")
        mentions.append(
            Mention(
                id=str(tw.id),
                text=tw.text or "",
                author_id=author_id,
                author_username=str(author.username) if author else None,
                author_verified=bool(author.verified) if author else None,
                author_followers=followers,
            )
        )

    # tweepy returns newest first — reverse so callers see chronological order.
    mentions.reverse()
    return mentions


# ---------------------------------------------------------------------------
# Budget readouts for status
# ---------------------------------------------------------------------------

def budget_summary() -> dict:
    return {
        "posts_24h": state.posts_in_last_24h(),
        "post_budget": POST_BUDGET_24H,
        "replies_24h": state.replies_in_last_24h(),
        "reply_subcap": REPLY_SUBCAP_24H,
    }
