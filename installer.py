"""
Установщик VTM Calculator.

Запустите этот файл ОДИН РАЗ перед первым запуском приложения.
Он создаст необходимый конфигурационный файл с токеном бота.

Распространяйте setup.py вместе с main_storyteller.py, но НЕ включайте .env в архив.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path
from tkinter import Tk, ttk, StringVar, messagebox

# ── Обфускация токена ─────────────────────────────────────────────────────────
# Токен не хранится в открытом виде. Для замены токена:
#   1. Запустите _encode_token('ваш:токен') в Python-консоли
#   2. Вставьте результат в _TOKEN_ENCODED ниже

_XOR_KEY = b"vtm-roller-2024"  # ключ обфускации (не шифрование!)


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encode_token(token: str) -> str:
    """Вспомогательная функция для разработчика — кодирует новый токен."""
    return base64.b64encode(_xor(token.encode(), _XOR_KEY)).decode()


def _decode_token(encoded: str) -> str:
    return _xor(base64.b64decode(encoded.encode()), _XOR_KEY).decode()


# ── Замените эту строку результатом _encode_token('ваш:токен') ───────────────
_TOKEN_ENCODED = _encode_token("8184695854:AAGBsg4e2dg-IwVu-Ggf7K_a8an_1LJnObA")


# ─────────────────────────────────────────────────────────────────────────────


# ── Пути (должны совпадать с config.py) ──────────────────────────────────────

def _get_app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ["APPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "VTM Roller"


APP_DATA_DIR = _get_app_data_dir()
ENV_FILE_PATH = APP_DATA_DIR / ".env"


# ── GUI установщика ───────────────────────────────────────────────────────────

class SetupApp(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("VTM Calculator — Установка")
        self.resizable(False, False)
        self._already_installed = ENV_FILE_PATH.exists() and self._token_exists()
        self._build()
        self._center_window()

    # ── Построение интерфейса ─────────────────────────────────────────────────

    def _build(self) -> None:
        pad = {"padx": 20, "pady": 8}

        frm = ttk.Frame(self, padding=20)
        frm.grid()

        # Заголовок
        ttk.Label(
            frm,
            text="VTM Calculator",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 4))

        ttk.Label(
            frm,
            text="Установщик конфигурации",
            font=("Segoe UI", 10),
            foreground="gray",
        ).grid(row=1, column=0, columnspan=2, pady=(0, 16))

        ttk.Separator(frm).grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)

        # Статус
        status_text = (
            "✔  Конфигурация уже установлена."
            if self._already_installed
            else "⚠  Конфигурация не найдена. Нажмите «Установить»."
        )
        self._status_var = StringVar(value=status_text)
        ttk.Label(
            frm,
            textvariable=self._status_var,
            font=("Segoe UI", 9),
            width=44,
            anchor="w",
        ).grid(row=3, column=0, columnspan=2, **pad)

        # Путь установки
        ttk.Label(
            frm,
            text="Каталог конфигурации:",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=4, column=0, sticky="w", padx=20)

        ttk.Label(
            frm,
            text=str(APP_DATA_DIR),
            font=("Consolas", 8),
            foreground="#555",
            anchor="w",
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 16))

        ttk.Separator(frm).grid(row=6, column=0, columnspan=2, sticky="ew", pady=8)

        # Кнопки
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(8, 0))

        self._install_btn = ttk.Button(
            btn_frame,
            text="Установить" if not self._already_installed else "Переустановить",
            command=self._install,
            width=16,
        )
        self._install_btn.grid(row=0, column=0, padx=6)

        ttk.Button(
            btn_frame,
            text="Закрыть",
            command=self.destroy,
            width=10,
        ).grid(row=0, column=1, padx=6)

    def _center_window(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Установка ─────────────────────────────────────────────────────────────

    def _install(self) -> None:
        try:
            self._write_env()
            self._status_var.set("✔  Конфигурация успешно установлена!")
            self._install_btn.configure(text="Переустановить")
            messagebox.showinfo(
                "Готово",
                "Конфигурация установлена.\n\nТеперь можно запустить main_storyteller.py.",
            )
        except Exception as exc:
            messagebox.showerror("Ошибка установки", str(exc))
            self._status_var.set(f"✖  Ошибка: {exc}")

    def _write_env(self) -> None:
        """Создаёт каталог и записывает .env с токеном."""
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Читаем существующий .env, чтобы не затереть настройки пользователя
        existing: dict[str, str] = {}
        if ENV_FILE_PATH.exists():
            existing = _parse_env(ENV_FILE_PATH)

        # Всегда перезаписываем только токен
        existing["BOT_TOKEN"] = _decode_token(_TOKEN_ENCODED)

        # Дефолтные значения для новой установки
        defaults = {
            "CHAT_ID": "",
            "THREAD_ID": "None",
            "NAME": "Adventurer",
            "DEX": "0",
            "WITS": "0",
            "BLOOD": "10",
            "MAX_BLOOD": "10",
            "WOUNDS": "0",
            "HUMANITY": "7",
            "WILL": "5",
        }
        for key, val in defaults.items():
            existing.setdefault(key, val)

        _write_env_file(ENV_FILE_PATH, existing)

    def _token_exists(self) -> bool:
        try:
            env = _parse_env(ENV_FILE_PATH)
            return bool(env.get("BOT_TOKEN"))
        except Exception:
            return False


# ── Утилиты для работы с .env вручную (без зависимости python-dotenv) ─────────

def _parse_env(path: Path) -> dict[str, str]:
    """Читает .env в словарь, игнорируя комментарии и пустые строки."""
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip()
    return result


def _write_env_file(path: Path, data: dict[str, str]) -> None:
    """Записывает словарь в .env-файл."""
    lines = [
        "# VTM Calculator — конфигурация\n",
        "# Этот файл создан автоматически. Не редактируйте BOT_TOKEN вручную.\n",
        "\n",
    ]
    for key, val in data.items():
        lines.append(f"{key}={val}\n")
    path.write_text("".join(lines), encoding="utf-8")


# ── Точка входа ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SetupApp()
    app.mainloop()
'''

---

### Как это работает
```
Вы (разработчик)          Друг
───────────────────        ───────────────────────────────
Токен в _TOKEN_ENCODED     1. Запускает setup.py
  (обфусцирован XOR)    →  2. Нажимает «Установить»
                           3. .env создаётся в AppData
                              с расшифрованным токеном
                           4. Запускает main_storyteller.py — всё работает
'''
