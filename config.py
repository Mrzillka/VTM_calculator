from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import NamedTuple

import dotenv


def resource_path(relative: str) -> Path:
    """Return absolute path to a bundled resource (works with PyInstaller)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative


NPC_NAMES: tuple[str, ...] = (
    "Alex", "Greg", "John", "Bill", "Emma", "Richard",
    "Anna", "Thomas", "Andrew", "Maria", "Caren", "Carl",
)

FONT = "Book Antiqua"


class WoundLevel(NamedTuple):
    name: str
    penalty: int


BACKGROUNDS: tuple[str, ...] = (
    "Allies", "Alternate Identity", "Armory", "Contacts", "Domain",
    "Fame", "Generation", "Haven", "Herd", "Influence", "Library",
    "Mentor", "Resources", "Retainers", "Status",
)

DISCIPLINES: tuple[str, ...] = (
    "Animalism", "Auspex", "Celerity", "Chimerstry",
    "Dementation", "Dominate", "Fortitude",
    "Necromancy", "Obfuscate", "Obtenebration",
    "Potence", "Presence", "Protean", "Quietus",
    "Serpentis", "Thaumaturgy", "Vicissitude",
    "Abombwe", "Daimonion", "Melpominee",
    "Mortis", "Mytherceria", "Obeah",
    "Sanguinus", "Temporis", "Thanatosis", "Visceratika",
    "Assamite Sorcery", "Koldunic Sorcery", "Setite Sorcery",
)

DISCIPLINE_PATHS: dict[str, tuple[str, ...]] = {
    "Thaumaturgy": (
        "Path of Blood", "Elemental Mastery", "The Green Path",
        "Hands of Destruction", "The Lure of Flames", "Movement of the Mind",
        "Neptune's Might", "Path of Conjuring", "Path of Corruption",
        "Path of Mars", "Path of Technomancy", "Path of the Father's Vengeance",
        "Thaumaturgical Countermagic", "Weather Control",
    ),
    "Necromancy": (
        "Sepulchre Path", "Ash Path", "Bone Path",
        "Cenotaph Path", "Mortuus Path", "Vitreous Path",
    ),
    "Assamite Sorcery": (
        "Path of the Levinbolt", "Path of Awakening", "Hands of the Divine",
        "Movement of the Loyal Heart", "The Stolen Heart",
    ),
    "Koldunic Sorcery": (
        "Way of Earth", "Way of Fire", "Way of Water", "Way of Wind", "Way of Spirit",
    ),
    "Setite Sorcery": (
        "Path of the Cobra's Favor", "Path of Duat", "Path of Phobos",
    ),
}

MERITS: dict[str, int] = {
    "Acute Senses": 1, "Ambidextrous": 1, "Baby Face": 2, "Blush of Health": 2,
    "Catlike Balance": 1, "Daredevil": 3, "Eat Food": 1, "Friendly Face": 1,
    "Gunslinger": 3, "Inoffensive to Animals": 1, "Calm Heart": 3,
    "Code of Honor": 2, "Common Sense": 1, "Concentration": 1, "Danger Sense": 2,
    "Eidetic Memory": 2, "Jack of All Trades": 5, "Light Sleeper": 2,
    "Oracular Ability": 3, "Early Riser": 1, "Enchanting Voice": 2,
    "Holistic Awareness": 2, "Iron Will": 3, "Lucky": 3, "Natural Linguist": 2,
    "Pitiable": 1, "Sanctity": 2, "Scholar of Enemies": 2, "Self-Confident": 5,
    "Magic Resistance": 2, "Medium": 2, "True Faith": 7, "True Love": 1,
}

FLAWS: dict[str, int] = {
    "Addiction": 1, "Allergic": 2, "Deep Sleeper": 1, "Deformity": 3,
    "Lame": 3, "Monstrous": 3, "One Eye": 2, "Permanent Wound": 3,
    "Short": 1, "Slow Healing": 3, "Speech Impediment": 1, "Absent Minded": 3,
    "Amnesia": 2, "Bard's Tongue": 1, "Compulsion": 1, "Confused": 2,
    "Curiosity": 2, "Derangement": 2, "Flashbacks": 2, "Nightmares": 1,
    "Overconfident": 1, "Soft-Hearted": 1, "Vengeance": 2, "Weak Willed": 3,
    "Clan Enmity": 2, "Dark Secret": 1, "Enemy": 3, "Hatred": 3,
    "Hunted": 4, "Infamy": 2, "Intolerance": 1, "Lifesaver": 3,
    "Lunacy": 2, "Notoriety": 3, "Phobia": 2, "Prey Exclusion": 1,
    "Territorial": 2, "Beacon of the Unholy": 2, "Eerie Presence": 2,
    "Grip of the Damned": 3, "Haunted": 3, "Thin Blood": 4,
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
# Legacy path kept for one-time migration only.
CHARACTER_FILE_PATH: Path = APP_DATA_DIR / "character.json"
CHARACTERS_DIR: Path = APP_DATA_DIR / "characters"
NPC_DIR: Path = APP_DATA_DIR / "npcs"
PC_DIR: Path = APP_DATA_DIR / "pcs"

GENERATION_RULES: dict[int, dict] = {
    4:  {"blood_max": 50, "blood_per_turn": 6, "max_trait": 9},
    5:  {"blood_max": 40, "blood_per_turn": 5, "max_trait": 8},
    6:  {"blood_max": 30, "blood_per_turn": 4, "max_trait": 7},
    7:  {"blood_max": 20, "blood_per_turn": 3, "max_trait": 6},
    8:  {"blood_max": 15, "blood_per_turn": 3, "max_trait": 6},
    9:  {"blood_max": 14, "blood_per_turn": 2, "max_trait": 5},
    10: {"blood_max": 13, "blood_per_turn": 1, "max_trait": 5},
    11: {"blood_max": 12, "blood_per_turn": 1, "max_trait": 5},
    12: {"blood_max": 11, "blood_per_turn": 1, "max_trait": 5},
    13: {"blood_max": 10, "blood_per_turn": 1, "max_trait": 5},
    14: {"blood_max": 10, "blood_per_turn": 1, "max_trait": 5},
    15: {"blood_max": 10, "blood_per_turn": 1, "max_trait": 5},
}

DEFAULT_SERVER_PORT: int = 9999


def get_server_port() -> int:
    """Return the configured TCP server port, reading SERVER_PORT from the environment."""
    return int(os.getenv("SERVER_PORT", str(DEFAULT_SERVER_PORT)))


def ensure_app_data_dir() -> None:
    """Create application data directories and .env file if they do not exist."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    NPC_DIR.mkdir(parents=True, exist_ok=True)
    PC_DIR.mkdir(parents=True, exist_ok=True)
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