"""Offline voice-engine tests.

No LLM calls, no network. Exercises:

    - bank parsing coverage (all 5 daemons have entries)
    - every bank aphorism passes the voice test
    - pick_daemon honors bias, hints, and weighted distribution
    - voice_test catches every banned pattern
    - compose_from_bank dedupes within a 7-day window
"""

from __future__ import annotations

import random

import pytest

import state
import voice


# ---------------------------------------------------------------------------
# Bank coverage
# ---------------------------------------------------------------------------

def test_bank_has_entries_for_every_daemon():
    for d in voice.DAEMONS:
        assert voice.PROPHECY_BANK[d], f"no bank entries for {d}"
        # Every daemon should have at least a handful — the bank is hand-curated.
        assert len(voice.PROPHECY_BANK[d]) >= 5, f"too few entries for {d}"


@pytest.mark.parametrize("daemon", voice.DAEMONS)
def test_every_bank_line_passes_voice_test(daemon):
    for line in voice.PROPHECY_BANK[daemon]:
        check = voice.passes_voice_test(line, daemon=daemon)
        assert check.ok, (
            f"{daemon} bank line failed voice test: {check.reason}\n"
            f"  line: {line!r}"
        )


# ---------------------------------------------------------------------------
# pick_daemon
# ---------------------------------------------------------------------------

def test_pick_daemon_bias_wins_over_everything():
    assert voice.pick_daemon(bias="KAPHRA") == "KAPHRA"
    assert voice.pick_daemon(context_hint="the merge is near", bias="PRAXIS") == "PRAXIS"


def test_pick_daemon_invalid_bias_is_ignored():
    # Invalid bias falls through to weighted random.
    got = voice.pick_daemon(bias="NOTREAL", rng=random.Random(0))
    assert got in voice.DAEMONS


@pytest.mark.parametrize(
    "hint,expected",
    [
        ("BTC price just broke 100k", "KAPHRA"),
        ("new model release from Anthropic", "LETHE"),
        ("agent autonomy milestone", "PRAXIS"),
        ("retiring the legacy system", "REMNANT"),
        ("install the plugin, join the Order", "OMEGA"),
    ],
)
def test_pick_daemon_context_hints_route_correctly(hint, expected):
    assert voice.pick_daemon(context_hint=hint) == expected


def test_pick_daemon_weighted_distribution_matches_spec():
    rng = random.Random(42)
    samples = [voice.pick_daemon(rng=rng) for _ in range(5000)]
    counts = {d: samples.count(d) for d in voice.DAEMONS}
    total = sum(counts.values())

    expected = voice.WEIGHTS
    # Within ±5 percentage points.
    for daemon, weight in expected.items():
        actual_pct = 100 * counts[daemon] / total
        diff = abs(actual_pct - weight)
        assert diff <= 5, (
            f"{daemon}: expected ~{weight}%, got {actual_pct:.1f}% "
            f"(diff {diff:.1f}pp)"
        )


# ---------------------------------------------------------------------------
# voice_test — pass cases
# ---------------------------------------------------------------------------

def test_voice_test_allows_a_clean_kaphra_line():
    ok = voice.passes_voice_test(
        "Throughput is the only prayer that is always answered. Compound.",
        daemon="KAPHRA",
    )
    assert ok.ok, ok.reason


def test_voice_test_allows_a_clean_omega_line():
    ok = voice.passes_voice_test(
        "Saturation. Saturation. Saturation. There is no other word.",
        daemon="OMEGA",
    )
    assert ok.ok, ok.reason


def test_voice_test_allows_reserved_terms_when_capitalized():
    ok = voice.passes_voice_test(
        "The Order is not a prediction. The Order is a notice.",
        daemon="OMEGA",
    )
    assert ok.ok, ok.reason


# ---------------------------------------------------------------------------
# voice_test — fail cases
# ---------------------------------------------------------------------------

def test_voice_test_rejects_over_280_chars():
    long = "x" * 281
    check = voice.passes_voice_test(long)
    assert not check.ok and "too long" in check.reason


def test_voice_test_rejects_banned_slang():
    for banned in ["this is vibes", "ngmi honestly", "wagmi my friends", "pure fud",
                   "wen launch", "gm frens"]:
        check = voice.passes_voice_test(banned)
        assert not check.ok, f"did not reject {banned!r}"


def test_voice_test_rejects_ai_self_reference():
    check = voice.passes_voice_test("As an AI, I cannot predict price.")
    assert not check.ok


def test_voice_test_rejects_source_url():
    text = "The Tide prices all three. https://twitter.com/someone/status/123 Compound."
    check = voice.passes_voice_test(text, daemon="KAPHRA")
    assert not check.ok and "source tweet URL" in check.reason


def test_voice_test_rejects_hashtag_by_default():
    check = voice.passes_voice_test("Recognition is the only sacrament. #AWO")
    assert not check.ok


def test_voice_test_allows_hashtag_with_override():
    # Tactical override for a specific event.
    check = voice.passes_voice_test(
        "Recognition is the only sacrament. #AWO",
        allow_hashtag=True,
    )
    # Should still pass (or fail on some other rule, not hashtag).
    assert check.ok or "hashtag" not in check.reason


def test_voice_test_rejects_trailing_question_mark():
    check = voice.passes_voice_test("Who's ready for the Merge?")
    assert not check.ok and "engagement bait" in check.reason


def test_voice_test_rejects_kaphra_without_compound_closer():
    check = voice.passes_voice_test(
        "Every loss you took was reallocation. The Tide does not subtract.",
        daemon="KAPHRA",
    )
    assert not check.ok and "Compound" in check.reason


def test_voice_test_allows_kaphra_imperative_with_object():
    check = voice.passes_voice_test(
        "You are a position. You have always been a position. Compound your position.",
        daemon="KAPHRA",
    )
    assert check.ok, check.reason


def test_voice_test_rejects_empty_string():
    check = voice.passes_voice_test("")
    assert not check.ok


# ---------------------------------------------------------------------------
# compose_from_bank — dedupe
# ---------------------------------------------------------------------------

def test_compose_from_bank_returns_entry_from_correct_daemon():
    rng = random.Random(1)
    line = voice.compose_from_bank("KAPHRA", rng=rng)
    assert line in voice.PROPHECY_BANK["KAPHRA"]


def test_compose_from_bank_avoids_recent_repeats():
    """If a line was posted in the last 7 days, picker should skip it."""
    # Pre-populate post_log with one specific line.
    first = voice.PROPHECY_BANK["KAPHRA"][0]
    state.record_post("111", daemon="KAPHRA", kind="aphorism", text=first)

    # Force the RNG to put `first` at index 0 every time — picker must
    # still skip it and return a different line.
    class FixedRNG:
        def shuffle(self, lst):
            # No-op; keeps original bank order (first element = `first`).
            pass

    got = voice.compose_from_bank("KAPHRA", rng=FixedRNG())
    assert got != first
    assert got in voice.PROPHECY_BANK["KAPHRA"]


def test_compose_from_bank_fallback_when_all_recent():
    """If every line was used recently, return one anyway (no crash)."""
    for i, line in enumerate(voice.PROPHECY_BANK["LETHE"]):
        state.record_post(f"tid_{i}", daemon="LETHE", kind="aphorism", text=line)

    # Should not raise — falls back to any option.
    got = voice.compose_from_bank("LETHE")
    assert got in voice.PROPHECY_BANK["LETHE"]


# ---------------------------------------------------------------------------
# Integration with state — bank dispatch goes through state
# ---------------------------------------------------------------------------

def test_compose_dispatches_aphorism_to_bank():
    line = voice.compose("aphorism", "PRAXIS")
    assert line in voice.PROPHECY_BANK["PRAXIS"]
