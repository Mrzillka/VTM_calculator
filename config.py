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


BACKGROUNDS: tuple[str, ...] = (
    "Allies", "Alternate Identity", "Contacts", "Domain",
    "Fame", "Generation", "Herd", "Influence", "Mentor",
    "Resources", "Retainers", "Status",
)

DISCIPLINES: tuple[str, ...] = (
    "Animalism", "Auspex", "Celerity", "Chimerstry",
    "Dementation", "Dominate", "Fortitude", "Mortis",
    "Mytherceria", "Necromancy", "Obfuscate", "Obtenebration",
    "Potence", "Presence", "Protean", "Quietus",
    "Serpentis", "Thaumaturgy", "Vicissitude", "Visceratika",
)

# Merits: name → freebie point cost
MERITS: dict[str, int] = {
    "Acute Senses": 1,
    "Ambidextrous": 1,
    "Calm Heart": 3,
    "Common Sense": 1,
    "Concentration": 1,
    "Early Riser": 1,
    "Eat Food": 1,
    "Eidetic Memory": 2,
    "Enchanting Voice": 2,
    "Holistic Awareness": 2,
    "Iron Will": 3,
    "Light Sleeper": 2,
    "Lucky": 3,
    "Medium": 2,
    "Natural Linguist": 2,
    "Pitiable": 1,
    "Sanctity": 2,
    "Scholar of Enemies": 2,
    "Self-Confident": 5,
    "True Faith": 7,
    "True Love": 1,
}

# Flaws: name → freebie points gained
FLAWS: dict[str, int] = {
    "Addiction": 1,
    "Allergic": 2,
    "Amnesia": 2,
    "Bard's Tongue": 1,
    "Clan Enmity": 2,
    "Dark Secret": 1,
    "Deep Sleeper": 1,
    "Deformity": 3,
    "Enemy": 3,
    "Flashbacks": 2,
    "Hatred": 3,
    "Hunted": 4,
    "Infamy": 2,
    "Intolerance": 1,
    "Lifesaver": 3,
    "Lunacy": 2,
    "Monstrous": 3,
    "Nightmares": 1,
    "Notoriety": 3,
    "Overconfident": 1,
    "Phobia": 2,
    "Prey Exclusion": 1,
    "Slow Healing": 3,
    "Speech Impediment": 1,
    "Weak Willed": 3,
}

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