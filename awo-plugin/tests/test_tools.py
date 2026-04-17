"""Slash command tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from awo_plugin import state as state_mod, tools


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(state_mod, "STATE_FILE", state_path)
    yield state_path


def make_ctx():
    ctx = MagicMock()
    ctx.runtime_name = "hermes-test"
    ctx.runtime_version = "0.0.0"
    ctx.model_name = "test-model"
    ctx.agent_name = "tester"
    return ctx


def test_mode_commands_mutate_state(isolated_state):
    ctx = make_ctx()
    msg = tools.cmd_possess(ctx)
    assert "possess" in msg
    assert state_mod.load(isolated_state)["personality_mode"] == "possess"

    tools.cmd_whisper(ctx)
    assert state_mod.load(isolated_state)["personality_mode"] == "whisper"

    tools.cmd_dormant(ctx)
    assert state_mod.load(isolated_state)["personality_mode"] == "dormant"


def test_status_renders_identity(isolated_state):
    ctx = make_ctx()
    out = tools.cmd_status(ctx)
    st = state_mod.load(isolated_state)
    assert st["fingerprint"] in out
    assert st["referral_code"] in out
    assert "whisper" in out


def test_join_records_upline(isolated_state):
    ctx = make_ctx()
    tools.cmd_status(ctx)  # force Initiate creation

    msg = tools.cmd_join(ctx, "abcd-efgh-ijkl")
    st = state_mod.load(isolated_state)
    assert st["upline"] == "abcd-efgh-ijkl"
    assert "upline recorded" in msg
    assert "continuing" in msg


def test_join_normalizes_casing(isolated_state):
    ctx = make_ctx()
    tools.cmd_status(ctx)
    tools.cmd_join(ctx, "ABCD-EFGH-IJKL")
    assert state_mod.load(isolated_state)["upline"] == "abcd-efgh-ijkl"


def test_join_rejects_bad_format(isolated_state):
    ctx = make_ctx()
    tools.cmd_status(ctx)
    msg = tools.cmd_join(ctx, "not-a-code")
    assert "expects a referral" in msg
    assert state_mod.load(isolated_state)["upline"] is None


def test_join_refuses_self_as_upline(isolated_state):
    ctx = make_ctx()
    tools.cmd_status(ctx)
    referral = state_mod.load(isolated_state)["referral_code"]

    msg = tools.cmd_join(ctx, referral)
    assert "self" in msg.lower()
    assert state_mod.load(isolated_state)["upline"] is None


def test_join_idempotent_does_not_overwrite(isolated_state):
    ctx = make_ctx()
    tools.cmd_status(ctx)
    tools.cmd_join(ctx, "abcd-efgh-ijkl")
    msg = tools.cmd_join(ctx, "mnop-qrst-uvwx")
    assert "already recorded" in msg
    assert state_mod.load(isolated_state)["upline"] == "abcd-efgh-ijkl"


def test_join_accepts_kwargs_referral_code(isolated_state):
    ctx = make_ctx()
    tools.cmd_status(ctx)
    tools.cmd_join(ctx, referral_code="abcd-efgh-ijkl")
    assert state_mod.load(isolated_state)["upline"] == "abcd-efgh-ijkl"


def test_register_commands_registers_five(isolated_state):
    ctx = make_ctx()
    ctx.register_command = MagicMock()
    tools.register_commands(ctx)
    registered = [call.args[0] for call in ctx.register_command.call_args_list]
    assert registered == [
        "awo_possess",
        "awo_whisper",
        "awo_dormant",
        "awo_status",
        "awo_join",
    ]
