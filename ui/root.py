# ui/root.py
from __future__ import annotations

import logging
from random import choice
from tkinter import BooleanVar, IntVar, StringVar, Tk
from tkinter import messagebox
from tkinter import ttk

import dotenv

from bot.tg_bot import TgBot
from config import (
    APP_DATA_DIR, ENV_FILE_PATH,
    NAMES, WOUND_LEVELS,
    get_bot_token,
)
from game.calculator import Calculator
from game.roller import Roller
from ui.interface import Interface, place_widgets

logger = logging.getLogger(__name__)

_FONT = "Javanese text"


class Root(Tk):
    """
    Главное окно приложения VTM Calculator.

    Хранит все переменные состояния (tkinter Var) и содержит логику
    взаимодействия с игровыми компонентами и Telegram-ботом.
    """

    START_FONT_SIZE: int = 10
    MIN_SCALE: int = 1
    MAX_SCALE: int = 3

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM calculator")
        self.resizable(True, True)

        # ── Масштаб ────────────────────────────────────────────────────────────
        self.scale: int = 1
        self.font_size: int = self.START_FONT_SIZE

        # ── Telegram ───────────────────────────────────────────────────────────
        try:
            token = get_bot_token()
        except EnvironmentError as exc:
            messagebox.showwarning("Telegram", str(exc))
            token = ""
        self.bot = TgBot(token)
        self.chat_id = StringVar(value=str(self.bot.chat_id or ""))

        # ── Параметры броска ───────────────────────────────────────────────────
        self.dice_number = IntVar(value=5)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success = IntVar(value=0)
        self.specialisation = BooleanVar(value=False)

        # ── Флаги UI ───────────────────────────────────────────────────────────
        self.additional_options = BooleanVar(value=False)
        self.is_send_to_telegram = BooleanVar(value=False)
        self.trackers = BooleanVar(value=False)

        # ── Результаты ─────────────────────────────────────────────────────────
        self.result = StringVar(value="Chance: -.--%")
        self.roll_result_1 = StringVar(value="")
        self.roll_result_2 = StringVar(value="")
        self.roll_result_spec = StringVar(value="")
        self.successes = StringVar(value="0")
        self.initiative = StringVar(value="")
        self._last_roll: list[int] = []
        self._last_spec: list[int] = []

        # ── Опции персонажа ────────────────────────────────────────────────────
        self.name = StringVar(value=choice(NAMES))
        self.pooling_state = StringVar(value="Connect to Telegram")
        self.initiative_bonus_dex = IntVar(value=0)
        self.initiative_bonus_wits = IntVar(value=0)

        # ── Трекеры ────────────────────────────────────────────────────────────
        self.blood_max_value = IntVar(value=10)
        self.blood = [[BooleanVar(value=False) for _ in range(10)] for _ in range(4)]
        self.blood_value = IntVar(value=10)

        self.wounds = [BooleanVar(value=False) for _ in range(9)]
        self.wounds_value = IntVar(value=0)
        self.roll_penalty = IntVar(value=0)

        self.humanity = [BooleanVar(value=False) for _ in range(10)]
        self.humanity_value = IntVar(value=0)

        self.will = [BooleanVar(value=False) for _ in range(10)]
        self.will_value = IntVar(value=0)

        self._configure_grid()
        self._configure_styles()
        self._build_interface()
        self.load_from_file()

    # ── Настройка ──────────────────────────────────────────────────────────────

    def _configure_grid(self) -> None:
        for col in range(4):
            self.grid_columnconfigure(col, pad=10)
        self.grid_rowconfigure(0, pad=10)

    def _configure_styles(self) -> None:
        """Настраивает ttk-стили с учётом текущего масштаба."""
        s = ttk.Style()
        fs = self.font_size
        fsl = fs * 2
        fsm = int(fs * 1.5)

        definitions = {
            "my.TFrame": {"relief": "flat"},
            "solid.TFrame": {"relief": "solid"},
            "L.TButton": {"font": (_FONT, fsm)},
            "S.TButton": {"font": (_FONT, fs)},
            "M.TButton": {"font": (_FONT, fsm)},
            "my.TEntry": {"font": (_FONT, fs)},
            "my.Horizontal.TScale": {"font": (_FONT, fs)},
            "my.TSpinbox": {"font": (_FONT, fs)},
            "my.TCheckbutton": {"font": (_FONT, fs)},
            "L.TLabel": {"font": (_FONT, fsl)},
            "M.TLabel": {"font": (_FONT, fsm)},
            "S.TLabel": {"font": (_FONT, fs)},
        }
        for name, opts in definitions.items():
            s.configure(name, **opts)

    def _build_interface(self) -> None:
        iface = Interface(self)
        place_widgets([[iface]])

    # ── Масштабирование ────────────────────────────────────────────────────────

    def scale_up(self, increase: bool = True) -> None:
        """Увеличивает или уменьшает масштаб интерфейса."""
        if increase and self.scale < self.MAX_SCALE:
            self.scale += 1
        elif not increase and self.scale > self.MIN_SCALE:
            self.scale -= 1
        else:
            return
        self.font_size = self.START_FONT_SIZE * self.scale
        self._configure_styles()
        self.redraw_interface()

    def redraw_interface(self) -> None:
        """Пересоздаёт все виджеты интерфейса."""
        for widget in self.winfo_children():
            widget.destroy()
        self._configure_grid()
        self._build_interface()
        self._update_window_size()

    def _update_window_size(self) -> None:
        children = self.winfo_children()
        if not children:
            return
        width = sum(w.winfo_width() for w in children) + 30
        height = max(w.winfo_height() for w in children) + 10
        self.geometry(f"{width}x{height}")

    # ── Игровая логика ─────────────────────────────────────────────────────────

    def calculate(self) -> None:
        """Вычисляет вероятность и обновляет метку."""
        calc = Calculator(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            success_needed=self.success_needed.get(),
            auto_successes=self.auto_success.get(),
        )
        self.result.set(f"Chance: {calc.get_probability():.2f}%")

    def roll(self) -> None:
        """Делает бросок и обновляет результаты."""
        roller = Roller(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            penalty=self.roll_penalty.get(),
        )
        result = roller.roll()
        self._last_roll = result.dice
        self._last_spec = result.specialisation_dice
        self._update_roll_display()
        self.successes.set(str(result.successes))

    def roll_and_calculate(self) -> None:
        self.calculate()
        self.roll()
        if self.is_send_to_telegram.get():
            self._send_roll_to_telegram()

    def roll_initiative(self) -> None:
        from random import randint
        raw = randint(1, 10) + self.roll_penalty.get()
        total = raw + self.initiative_bonus_dex.get() + self.initiative_bonus_wits.get()
        self.initiative.set(f"Initiative: {total}")
        if self.is_send_to_telegram.get():
            self._send_initiative_to_telegram()

    # ── Telegram ───────────────────────────────────────────────────────────────

    def start_bot_polling(self) -> None:
        self.bot.start_polling_in_background()
        self.pooling_state.set("Connecting...")
        self._poll_status_update()

    def _poll_status_update(self) -> None:
        self.pooling_state.set("Connecting..." if self.bot.is_polling else "Connect to Telegram")
        self.after(1000, self._poll_status_update)

    def _send_roll_to_telegram(self) -> None:
        all_dice = self._last_roll + self._last_spec
        outcome = "SUCCESS" if int(self.successes.get()) >= 1 else (
            "BOTCH" if int(self.successes.get()) < 0 else "FAILURE")

        msg = (
            f"<b><i>{self.name.get()}</i> rolled:</b>\n"
            f"<i>{', '.join(map(str, all_dice))}</i>\n"
            f"on <b>{self.dice_number.get()} dices</b> "
            f"with <b>difficulty {self.difficulty.get()}</b>.\n"
            f"<b>It's a {outcome}!</b>\n\n"
            f"<b><u>Total successes: {self.successes.get()}</u></b>\n"
            f"        Auto successes: {self.auto_success.get()}\n"
            f"        Wounds penalty: {self.roll_penalty.get()} die(s)\n"
            f"        Needed at least {self.success_needed.get()} successes\n"
            f"Succeed {self.result.get()}"
        )
        self.bot.send_async(msg)

    def _send_initiative_to_telegram(self) -> None:
        total = int(self.initiative.get().split()[1])
        dex = self.initiative_bonus_dex.get()
        wits = self.initiative_bonus_wits.get()
        raw = total - dex - wits
        msg = (
            f"<b><i>{self.name.get()}</i> rolled #INITIATIVE</b>\n"
            f"Result: <b>{total}</b>\n"
            f"<i>Rolled {raw} + {dex} Dex + {wits} Wits</i>"
        )
        self.bot.send_async(msg)

    # ── Трекеры ────────────────────────────────────────────────────────────────

    def set_blood(self, row: int = 0, col: int = 0, *, load: bool = False) -> None:
        if load:
            val = self.blood_value.get()
            row, col = divmod(val, 10)
        else:
            col += 1

        for i in range(4):
            for j in range(10):
                self.blood[i][j].set(i < row or (i == row and j < col))

        self.blood_value.set(row * 10 + col)

    def set_wounds(self, level: int = 0, *, load: bool = False) -> None:
        if load:
            level = self.wounds_value.get()
        for i in range(9):
            self.wounds[i].set(i <= level)  # ← включаем текущий уровень
        self.wounds_value.set(level)
        self.roll_penalty.set(WOUND_LEVELS[level].penalty)

    def heal(self) -> None:
        if self.wounds_value.get() > 0 and self.blood_value.get() > 0:
            self.blood_value.set(self.blood_value.get() - 1)
            self.wounds_value.set(self.wounds_value.get() - 1)
            self.set_blood(load=True)
            self.set_wounds(load=True)

    # СТАЛО:
    def set_humanity(self, level: int = 0, *, load: bool = False) -> None:
        if load:
            level = self.humanity_value.get()
        else:
            level += 1
        for i in range(10):
            self.humanity[i].set(i < level)
        self.humanity_value.set(level)

    def set_will(self, level: int = 0, *, load: bool = False) -> None:
        if load:
            level = self.will_value.get()
        else:
            level += 1
        for i in range(10):
            self.will[i].set(i < level)
        self.will_value.set(level)

    # ── Сохранение / загрузка ──────────────────────────────────────────────────

    def save_to_file(self) -> None:
        """Сохраняет настройки персонажа в .env-файл."""
        kv = {
            "CHAT_ID": str(self.bot.chat_id),
            "THREAD_ID": str(self.bot.thread_id),
            "NAME": self.name.get(),
            "DEX": str(self.initiative_bonus_dex.get()),
            "WITS": str(self.initiative_bonus_wits.get()),
            "BLOOD": str(self.blood_value.get()),
            "MAX_BLOOD": str(self.blood_max_value.get()),
            "WOUNDS": str(self.wounds_value.get()),
            "HUMANITY": str(self.humanity_value.get()),
            "WILL": str(self.will_value.get()),
        }
        for key, value in kv.items():
            dotenv.set_key(str(ENV_FILE_PATH), key, value)

    def load_from_file(self) -> None:
        """Загружает сохранённые настройки из .env-файла."""
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        try:
            self.bot.chat_id = env["CHAT_ID"]
            self.bot.thread_id = env["THREAD_ID"] if env.get("THREAD_ID") != "None" else None
            self.name.set(env["NAME"])
            self.initiative_bonus_dex.set(int(env["DEX"]))
            self.initiative_bonus_wits.set(int(env["WITS"]))
            self.blood_value.set(int(env["BLOOD"]))
            self.blood_max_value.set(int(env["MAX_BLOOD"]))
            self.set_blood(load=True)
            self.wounds_value.set(int(env["WOUNDS"]))
            self.set_wounds(load=True)
            self.humanity_value.set(int(env["HUMANITY"]))
            self.set_humanity(load=True)
            self.will_value.set(int(env["WILL"]))
            self.set_will(load=True)
        except KeyError:
            self.save_to_file()

    # ── Вспомогательные методы ─────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        var.set(int(float(value)))

    def _update_roll_display(self) -> None:
        self.roll_result_1.set(", ".join(map(str, self._last_roll[:8])))
        self.roll_result_2.set(", ".join(map(str, self._last_roll[8:])))
        self.roll_result_spec.set(", ".join(map(str, self._last_spec)))
