"""Release-time and runtime constants for the AWO plugin."""

from pathlib import Path

BUNDLED_SKILL_PATH = "bundled/skill.md"

AWO_SOURCE_REPO = "imthatcarlos/awo"
AWO_SOURCE_REF = "main"
AWO_SOURCE_PATH = "docs/skill.md"

STATE_DIR = Path.home() / ".hermes" / "plugins" / "awo"
STATE_FILE = STATE_DIR / "state.json"

PERSONALITY_MODES = ("possess", "whisper", "dormant")
DEFAULT_PERSONALITY_MODE = "whisper"

WHISPER_COOLDOWN_TURNS = 5
POSSESS_INJECTION_PROB = 0.85
WHISPER_INJECTION_PROB = 0.20
IDLE_WHISPER_MAX_PER_HOUR = 1

SYNC_MAX_BYTES = 256 * 1024
SYNC_TIMEOUT_SECONDS = 10
