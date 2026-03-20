from __future__ import annotations

import logging
from tkinter import BooleanVar, IntVar, Tk
from tkinter import ttk
from typing import Callable

import dotenv

from config import ENV_FILE_PATH
from game.calculator import Calculator
from game.models import RollRecord
from game.roller import Roller
from lang import locale
from ui.storyteller.interface import Interface
from ui.styles import configure_main_styles
from ui.utils import place_widgets

logger = logging.getLogger(__name__)


class Root(Tk):
    """Main window for the Storyteller application."""

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM Storyteller")
        self.resizable(True, True)

        self._restore_lang_pref()

        self.dice_number      = IntVar(value=5)
        self.difficulty       = IntVar(value=6)
        self.success_needed   = IntVar(value=1)
        self.auto_success     = IntVar(value=0)
        self.specialisation   = BooleanVar(value=False)
        self.additional_options = BooleanVar(value=False)

        self.roll_history: list[RollRecord] = []
        self._on_roll_callbacks: list[Callable[[RollRecord], None]] = []

        locale.on_change(self._on_locale_change)

        self._configure_styles()
        self._build_interface()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _restore_lang_pref(self) -> None:
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        saved = env.get("LANG_PREF", "en")
        if saved != locale.lang:
            locale.set_lang(saved)

    def _configure_styles(self) -> None:
        configure_main_styles(ttk.Style())

    def _build_interface(self) -> None:
        self._interface = Interface(self)
        place_widgets([[self._interface]])

    # ── Locale ─────────────────────────────────────────────────────────────────

    def _on_locale_change(self) -> None:
        pass

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

    def roll_initiative(self) -> None:
        from random import randint
        total = randint(1, 10) + self.dice_number.get()
        self._interface.show_initiative(total)

    def save_lang_pref(self) -> None:
        dotenv.set_key(str(ENV_FILE_PATH), "LANG_PREF", locale.lang)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        var.set(int(float(value)))