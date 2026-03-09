from __future__ import annotations

import logging
from tkinter import BooleanVar, IntVar, StringVar, Tk
from tkinter import messagebox
from tkinter import ttk

import dotenv

from bot.tg_bot import TgBot
from config import ENV_FILE_PATH, get_bot_token, FONT
from game.calculator import Calculator
from game.character import Character
from game.roller import Roller
from ui.interface import Interface, place_widgets

logger = logging.getLogger(__name__)


class Root(Tk):
    """
    Main application window for VTM Calculator.

    Owns application-level state (Telegram, roll parameters, UI flags, roll
    results) and an instance of Character for all character-specific state.
    Interaction logic between the two domains is coordinated here.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM calculator")
        self.resizable(True, True)

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
        self.dice_number = IntVar(value=5)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success = IntVar(value=0)
        self.specialisation = BooleanVar(value=False)

        # ── UI flags ───────────────────────────────────────────────────────────
        self.additional_options = BooleanVar(value=False)
        self.is_send_to_telegram = BooleanVar(value=False)
        self.trackers = BooleanVar(value=False)

        # ── Roll results ───────────────────────────────────────────────────────
        self.result = StringVar(value="Chance: -.--%")
        self.roll_result_1 = StringVar(value="")
        self.roll_result_2 = StringVar(value="")
        self.roll_result_spec = StringVar(value="")
        self.successes = StringVar(value="0")
        self.initiative = StringVar(value="")
        self._last_roll: list[int] = []
        self._last_spec: list[int] = []

        # ── Bot connection state ───────────────────────────────────────────────
        self.pooling_state = StringVar(value="Connect to Telegram")

        self._configure_grid()
        self._configure_styles()
        self._build_interface()
        self.load_from_file()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _configure_grid(self) -> None:
        for col in range(4):
            self.grid_columnconfigure(col, pad=10)
        self.grid_rowconfigure(0, pad=10)

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
            "my.TCheckbutton": {"font": (FONT, 10)},
            "title.TLabel": {"font": (FONT, 20, "bold", "italic")},
            "L.TLabel": {"font": (FONT, 18, "bold")},
            "M.TLabel": {"font": (FONT, 15, 'italic')},
            "S.TLabel": {"font": (FONT, 10)},
        }
        for name, opts in definitions.items():
            s.configure(name, **opts)

    def _build_interface(self) -> None:
        self._interface = Interface(self)
        place_widgets([[self._interface]])

    # ── Game logic ─────────────────────────────────────────────────────────────

    def calculate(self) -> None:
        """Calculate roll probability and update the result label."""
        calc = Calculator(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            success_needed=self.success_needed.get(),
            auto_successes=self.auto_success.get(),
        )
        self.result.set(f"Chance: {calc.get_probability():.2f}%")

    def roll(self) -> None:
        """Perform a dice roll and update result display variables."""
        roller = Roller(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            penalty=self.character.roll_penalty.get(),
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
        raw = randint(1, 10) + self.character.roll_penalty.get()
        total = (
                raw
                + self.character.initiative_bonus_dex.get()
                + self.character.initiative_bonus_wits.get()
        )
        self.initiative.set(f"Initiative: {total}")
        if self.is_send_to_telegram.get():
            self._send_initiative_to_telegram()

    # ── Telegram ───────────────────────────────────────────────────────────────

    def start_bot_polling(self) -> None:
        self.bot.start_polling_in_background()
        self.pooling_state.set("Connecting...")
        self._poll_status_update()

    def _poll_status_update(self) -> None:
        self.pooling_state.set(
            "Connecting..." if self.bot.is_polling else "Connect to Telegram"
        )
        self.after(1000, self._poll_status_update)

    def _send_roll_to_telegram(self) -> None:
        all_dice = self._last_roll + self._last_spec
        net = int(self.successes.get())
        outcome = "SUCCESS" if net >= 1 else ("BOTCH" if net < 0 else "FAILURE")

        msg = (
            f"<b><i>{self.character.character_name.get()}</i> rolled:</b>\n"
            f"<i>{', '.join(map(str, all_dice))}</i>\n"
            f"on <b>{self.dice_number.get()} dices</b> "
            f"with <b>difficulty {self.difficulty.get()}</b>.\n"
            f"<b>It's a {outcome}!</b>\n\n"
            f"<b><u>Total successes: {self.successes.get()}</u></b>\n"
            f"        Auto successes: {self.auto_success.get()}\n"
            f"        Wounds penalty: {self.character.roll_penalty.get()} die(s)\n"
            f"        Needed at least {self.success_needed.get()} successes\n"
            f"Succeed {self.result.get()}"
        )
        self.bot.send_async(msg)

    def _send_initiative_to_telegram(self) -> None:
        total = int(self.initiative.get().split()[1])
        dex = self.character.initiative_bonus_dex.get()
        wits = self.character.initiative_bonus_wits.get()
        raw = total - dex - wits
        msg = (
            f"<b><i>{self.character.character_name.get()}</i> rolled #INITIATIVE</b>\n"
            f"Result: <b>{total}</b>\n"
            f"<i>Rolled {raw} + {dex} Dex + {wits} Wits</i>"
        )
        self.bot.send_async(msg)

    # ── Save / load ────────────────────────────────────────────────────────────

    def save_to_file(self) -> None:
        """Persist bot connection settings to .env and character data to JSON."""
        dotenv.set_key(str(ENV_FILE_PATH), "CHAT_ID", str(self.bot.chat_id))
        dotenv.set_key(str(ENV_FILE_PATH), "THREAD_ID", str(self.bot.thread_id))
        self.character.save()

    def load_from_file(self) -> None:
        """Restore bot connection settings from .env and character data from JSON."""
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        self.bot.chat_id = env.get("CHAT_ID")
        self.bot.thread_id = env.get("THREAD_ID") if env.get("THREAD_ID") != "None" else None

        if not self.character.load_from_file():
            self.save_to_file()
            return

        # refresh_blood_cells must run after blood_max_value is set
        # and before the dot BooleanVars are populated
        self._interface.refresh_blood_cells()
        self.character.apply_trackers()

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        """Convert a float slider value to int and assign it to the variable."""
        var.set(int(float(value)))

    def _update_roll_display(self) -> None:
        self.roll_result_1.set(", ".join(map(str, self._last_roll[:8])))
        self.roll_result_2.set(", ".join(map(str, self._last_roll[8:])))
        self.roll_result_spec.set(", ".join(map(str, self._last_spec)))
