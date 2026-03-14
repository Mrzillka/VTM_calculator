from __future__ import annotations

import logging
from dataclasses import dataclass
from tkinter import BooleanVar, IntVar, Tk
from tkinter import ttk
from typing import Callable

import dotenv

from config import ENV_FILE_PATH, FONT
from game.calculator import Calculator
from game.roller import Roller
from lang import locale
from ui.storyteller.interface import Interface
from ui.utils import place_widgets

logger = logging.getLogger(__name__)


@dataclass
class RollRecord:
    """Single roll entry stored in the history."""
    dice_number: int
    difficulty: int
    auto_success: int
    dice: list[int]
    spec_dice: list[int]
    successes: int
    probability: float

    @property
    def outcome(self) -> str:
        if self.successes >= 1:
            return "SUCCESS"
        if self.successes < 0:
            return "BOTCH"
        return "FAILURE"


class Root(Tk):
    """
    Main window for the Storyteller application.

    Owns roll parameters and result state; delegates rendering to Interface.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM Storyteller")
        self.resizable(True, True)

        self._restore_lang_pref()

        # ── Roll parameters ────────────────────────────────────────────────────
        self.dice_number = IntVar(value=5)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success = IntVar(value=0)
        self.specialisation = BooleanVar(value=False)
        self.additional_options = BooleanVar(value=False)

        # ── Roll history ───────────────────────────────────────────────────────
        self.roll_history: list[RollRecord] = []
        self._on_roll_callbacks: list[Callable[[RollRecord], None]] = []

        locale.on_change(self._on_locale_change)

        self._configure_styles()
        self._build_interface()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _restore_lang_pref(self) -> None:
        """Read persisted language from .env and apply it before the UI is built."""
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        saved = env.get("LANG_PREF", "en")
        if saved != locale.lang:
            locale.set_lang(saved)

    def _configure_styles(self) -> None:
        s = ttk.Style()
        definitions = {
            "flat.TFrame": {"relief": "flat"},
            "solid.TFrame": {"relief": "solid"},
            "L.TButton": {"font": (FONT, 15)},
            "M.TButton": {"font": (FONT, 12, "italic")},
            "S.TButton": {"font": (FONT, 10)},
            "my.TEntry": {"font": (FONT, 10)},
            "my.Horizontal.TScale": {"font": (FONT, 10)},
            "my.TSpinbox": {"font": (FONT, 10)},
            "title.TLabel": {"font": (FONT, 20, "bold", "italic")},
            "L.TLabel": {"font": (FONT, 18, "bold")},
            "M.TLabel": {"font": (FONT, 15, "italic")},
            "S.TLabel": {"font": (FONT, 10)},
            "HistoryMeta.TLabel": {"font": (FONT, 9), "foreground": "gray"},
            "HistoryDice.TLabel": {"font": (FONT, 10)},
            "Success.TLabel": {"font": (FONT, 13, "bold"), "foreground": "#2e7d32"},
            "Failure.TLabel": {"font": (FONT, 13, "bold"), "foreground": "#757575"},
            "Botch.TLabel": {"font": (FONT, 13, "bold"), "foreground": "#c62828"},
            "SuccessCount.TLabel": {"font": (FONT, 11, "bold"), "foreground": "#2e7d32"},
            "FailureCount.TLabel": {"font": (FONT, 11, "bold"), "foreground": "#757575"},
            "BotchCount.TLabel": {"font": (FONT, 11, "bold"), "foreground": "#c62828"},
        }
        for name, opts in definitions.items():
            s.configure(name, **opts)

    def _build_interface(self) -> None:
        self._interface = Interface(self)
        place_widgets([[self._interface]])

    # ── Locale ─────────────────────────────────────────────────────────────────

    def _on_locale_change(self) -> None:
        pass

    # ── Roll callbacks ─────────────────────────────────────────────────────────

    def on_roll(self, callback: Callable[[RollRecord], None]) -> None:
        """Register a callback invoked with the new RollRecord after each roll."""
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
        """Persist the active language to .env."""
        dotenv.set_key(str(ENV_FILE_PATH), "LANG_PREF", locale.lang)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        """Convert a float slider value to int and write it to the variable."""
        var.set(int(float(value)))