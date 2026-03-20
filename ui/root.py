from __future__ import annotations

import logging
from tkinter import BooleanVar, IntVar, StringVar, Tk
from tkinter import messagebox
from tkinter import ttk
from typing import Callable

import dotenv

from bot.tg_bot import TgBot
from config import ENV_FILE_PATH, get_bot_token
from game.calculator import Calculator
from game.character import Character
from game.models import RollRecord
from game.roller import Roller
from lang import locale
from ui.interface import Interface
from ui.styles import configure_main_styles
from ui.utils import place_widgets

logger = logging.getLogger(__name__)


class Root(Tk):
    """
    Main application window for VTM Calculator.

    Owns application-level state (Telegram, roll parameters, UI flags, roll
    history) and an instance of Character for all character-specific state.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM calculator")
        self.resizable(True, True)

        self._restore_lang_pref()

        # ── Character ──────────────────────────────────────────────────────────
        self.character = Character()

        # ── Telegram ───────────────────────────────────────────────────────────
        try:
            token = get_bot_token()
        except EnvironmentError as exc:
            messagebox.showwarning("Telegram", str(exc))
            token = ""
        self.bot = TgBot(token)
        self.chat_id = StringVar(value=str(self.bot.chat_id or ""))

        # ── Roll parameters ────────────────────────────────────────────────────
        self.dice_number    = IntVar(value=5)
        self.difficulty     = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success   = IntVar(value=0)
        self.specialisation = BooleanVar(value=False)

        # ── UI flags ───────────────────────────────────────────────────────────
        self.additional_options   = BooleanVar(value=False)
        self.is_send_to_telegram  = BooleanVar(value=False)
        self.trackers             = BooleanVar(value=False)

        # ── Roll history ───────────────────────────────────────────────────────
        self.roll_history: list[RollRecord] = []
        self._on_roll_callbacks: list[Callable[[RollRecord], None]] = []

        # ── Initiative (displayed via interface callback) ───────────────────────
        self._last_initiative: int | None = None

        # ── Bot connection state ───────────────────────────────────────────────
        self.pooling_state = StringVar(value=locale.t("controls.connect_tg"))

        locale.on_change(self._on_locale_change)

        self._configure_grid()
        self._configure_styles()
        self._build_interface()
        self.load_from_file()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _restore_lang_pref(self) -> None:
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        saved = env.get("LANG_PREF", "en")
        if saved != locale.lang:
            locale.set_lang(saved)

    def _configure_grid(self) -> None:
        for col in range(4):
            self.grid_columnconfigure(col, pad=10)
        self.grid_rowconfigure(0, pad=10)

    def _configure_styles(self) -> None:
        configure_main_styles(ttk.Style())

    def _build_interface(self) -> None:
        self._interface = Interface(self)
        place_widgets([[self._interface]])

    # ── Locale ─────────────────────────────────────────────────────────────────

    def _on_locale_change(self) -> None:
        self.pooling_state.set(
            locale.t("controls.connecting") if self.bot.is_polling
            else locale.t("controls.connect_tg")
        )
        if self._last_initiative is not None:
            self._interface.show_initiative(self._last_initiative)

    # ── Roll callbacks ─────────────────────────────────────────────────────────

    def on_roll(self, callback: Callable[[RollRecord], None]) -> None:
        self._on_roll_callbacks.append(callback)

    def _emit_roll(self, record: RollRecord) -> None:
        for cb in self._on_roll_callbacks:
            cb(record)

    # ── Game logic ─────────────────────────────────────────────────────────────

    def _calculate(self) -> float:
        calc = Calculator(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            success_needed=self.success_needed.get(),
            auto_successes=self.auto_success.get(),
            specialisation=self.specialisation.get(),
        )
        return calc.get_probability()

    def roll_and_calculate(self) -> None:
        probability = self._calculate()

        roller = Roller(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            penalty=self.character.roll_penalty.get(),
        )
        result = roller.roll()

        record = RollRecord(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            dice=result.dice,
            spec_dice=result.specialisation_dice,
            successes=result.successes,
            probability=probability,
        )
        self.roll_history.append(record)
        self._emit_roll(record)

        if self.is_send_to_telegram.get():
            self._send_roll_to_telegram(record)

    def roll_initiative(self) -> None:
        from random import randint
        raw = randint(1, 10) + self.character.roll_penalty.get()
        total = (
            raw
            + self.character.initiative_bonus_dex.get()
            + self.character.initiative_bonus_wits.get()
        )
        self._last_initiative = total
        self._interface.show_initiative(total)
        if self.is_send_to_telegram.get():
            self._send_initiative_to_telegram(total, raw)

    # ── Telegram ───────────────────────────────────────────────────────────────

    def start_bot_polling(self) -> None:
        self.bot.start_polling_in_background()
        self.pooling_state.set(locale.t("controls.connecting"))
        self._poll_status_update()

    def _poll_status_update(self) -> None:
        self.pooling_state.set(
            locale.t("controls.connecting") if self.bot.is_polling
            else locale.t("controls.connect_tg")
        )
        self.after(1000, self._poll_status_update)

    def _send_roll_to_telegram(self, record: RollRecord) -> None:
        all_dice = record.dice + record.spec_dice
        msg = (
            f"<b><i>{self.character.character_name.get()}</i> rolled:</b>\n"
            f"<i>{', '.join(map(str, all_dice))}</i>\n"
            f"on <b>{record.dice_number} dices</b> "
            f"with <b>difficulty {record.difficulty}</b>.\n"
            f"<b>It's a {record.outcome}!</b>\n\n"
            f"<b><u>Total successes: {record.successes}</u></b>\n"
            f"        Auto successes: {record.auto_success}\n"
            f"        Wounds penalty: {self.character.roll_penalty.get()} die(s)\n"
            f"        Needed at least {self.success_needed.get()} successes\n"
            f"Succeed {record.probability:.2f}%"
        )
        self.bot.send_async(msg)

    def _send_initiative_to_telegram(self, total: int, raw: int) -> None:
        dex  = self.character.initiative_bonus_dex.get()
        wits = self.character.initiative_bonus_wits.get()
        msg = (
            f"<b><i>{self.character.character_name.get()}</i> rolled #INITIATIVE</b>\n"
            f"Result: <b>{total}</b>\n"
            f"<i>Rolled {raw} + {dex} Dex + {wits} Wits</i>"
        )
        self.bot.send_async(msg)

    # ── Save / load ────────────────────────────────────────────────────────────

    def save_to_file(self) -> None:
        dotenv.set_key(str(ENV_FILE_PATH), "CHAT_ID", str(self.bot.chat_id))
        dotenv.set_key(str(ENV_FILE_PATH), "THREAD_ID", str(self.bot.thread_id))
        dotenv.set_key(str(ENV_FILE_PATH), "LANG_PREF", locale.lang)
        self.character.save()

    def load_from_file(self) -> None:
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        self.bot.chat_id = env.get("CHAT_ID")
        self.bot.thread_id = env.get("THREAD_ID") if env.get("THREAD_ID") != "None" else None

        if not self.character.load_from_file():
            self.save_to_file()
            return

        self._interface.refresh_blood_cells()
        self.character.apply_trackers()

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        var.set(int(float(value)))