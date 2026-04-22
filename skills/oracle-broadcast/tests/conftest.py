"""Shared pytest fixtures.

Adds ``scripts/`` to ``sys.path`` so tests can ``import voice`` etc.
Also redirects the state DB to a temp file so tests never touch
``~/.hermes/plugins/awo/oracle.db``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _SKILL_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Every test gets its own empty DB in tmp_path."""
    import state

    monkeypatch.setattr(state, "DB_PATH", tmp_path / "oracle.db")
    yield
