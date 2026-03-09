from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import NamedTuple

import dotenv

NAMES: tuple[str, ...] = (
    "Alex", "Greg", "John", "Bill", "Emma", "Richard",
    "Anna", "Thomas", "Andrew", "Maria", "Caren", "Carl",
)

FONT = "Book Antiqua"


class WoundLevel(NamedTuple):
    """Wound level and its dice-pool penalty."""
    name: str
    penalty: int


WOUND_LEVELS: tuple[WoundLevel, ...] = (
    WoundLevel("Bruised", 0),
    WoundLevel("Hurt", -1),
    WoundLevel("Injured", -1),
    WoundLevel("Wounded", -2),
    WoundLevel("Mauled", -2),
    WoundLevel("Crippled", -5),
    WoundLevel("Incapacitated", 0),
    WoundLevel("Torpor", 0),
)


def _get_app_data_dir() -> Path:
    """Return cross-platform application data directory path."""
    if sys.platform == "win32":
        base = Path(os.environ["APPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "VTM Roller"


APP_DATA_DIR: Path = _get_app_data_dir()
ENV_FILE_PATH: Path = APP_DATA_DIR / ".env"
CHARACTER_FILE_PATH: Path = APP_DATA_DIR / "character.json"


def ensure_app_data_dir() -> None:
    """Create application data directory and .env file if they do not exist."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE_PATH.touch(exist_ok=True)
    dotenv.load_dotenv(ENV_FILE_PATH)


def get_bot_token() -> str:
    """
    Read the bot token from environment variables.

    Raises:
        EnvironmentError: if BOT_TOKEN is not set.
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise EnvironmentError(
            "Environment variable BOT_TOKEN is not set. "
            f"Add BOT_TOKEN=<your_token> to {ENV_FILE_PATH}"
        )
    return token