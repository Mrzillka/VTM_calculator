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

FONT = "Javanese text"

class WoundLevel(NamedTuple):
    """Уровень ранения и его штраф к броскам."""
    name: str
    penalty: int


WOUND_LEVELS: tuple[WoundLevel, ...] = (
    WoundLevel("", 0),
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
    """Возвращает кроссплатформенный путь к каталогу приложения."""
    if sys.platform == "win32":
        base = Path(os.environ["APPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "VTM Roller"


APP_DATA_DIR: Path = _get_app_data_dir()
ENV_FILE_PATH: Path = APP_DATA_DIR / ".env"


def ensure_app_data_dir() -> None:
    """Создаёт каталог и .env-файл приложения, если они не существуют."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE_PATH.touch(exist_ok=True)
    dotenv.load_dotenv(ENV_FILE_PATH)


def get_bot_token() -> str:
    """
    Читает токен бота из переменных окружения.

    Raises:
        EnvironmentError: если токен не задан.
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise EnvironmentError(
            "Переменная окружения BOT_TOKEN не задана. "
            f"Добавьте BOT_TOKEN=<ваш_токен> в файл {ENV_FILE_PATH}"
        )
    return token
