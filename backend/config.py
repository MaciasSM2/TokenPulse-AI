import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
USER_HOME = Path.home()

# Source paths
OPENCODE_DB_PATH = USER_HOME / ".local" / "share" / "opencode" / "opencode.db"
ANTIGRAVITY_BRAIN_PATH = USER_HOME / ".gemini" / "antigravity-ide" / "brain"
ANTIGRAVITY_CONVERSATIONS_PATH = USER_HOME / ".gemini" / "antigravity-ide" / "conversations"

# Application Database
TRACKER_DB_PATH = BASE_DIR / "token_tracker.db"
PRICING_FILE_PATH = BASE_DIR / "backend" / "pricing_models.json"

# Server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4120
