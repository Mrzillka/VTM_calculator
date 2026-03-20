from __future__ import annotations

import logging
import queue
import secrets
from tkinter import BooleanVar, IntVar, StringVar, Tk
from tkinter import ttk
from typing import Callable

import dotenv

from config import ENV_FILE_PATH
from game.calculator import Calculator
from game.models import RollRecord
from game.roller import Roller
from lang import locale
from network.protocol import dict_to_roll_record, roll_record_to_dict
from network.session import NtfySession
from ui.storyteller.interface import Interface
from ui.styles import configure_main_styles
from ui.utils import place_widgets

logger = logging.getLogger(__name__)

from ui.storyteller.constants import NO_ROLLER  # noqa: E402


def _generate_topic() -> str:
    """Generate a random session topic name."""
    return "vtm-" + secrets.token_hex(6)


class Root(Tk):
    """Main window for the Storyteller application."""

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM Storyteller")
        self.resizable(True, True)

        self._restore_lang_pref()

        self.dice_number        = IntVar(value=5)
        self.difficulty         = IntVar(value=6)
        self.success_needed     = IntVar(value=1)
        self.auto_success       = IntVar(value=0)
        self.specialisation     = BooleanVar(value=False)
        self.additional_options = BooleanVar(value=False)
        self.active_roller      = StringVar(value=NO_ROLLER)

        # Currently active session topic; empty means no session running.
        self.session_topic = StringVar(value="")

        self.roll_history: list[RollRecord] = []
        self._on_roll_callbacks: list[Callable[[RollRecord], None]] = []

        self._net_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._session: NtfySession | None = None

        locale.on_change(self._on_locale_change)

        self._configure_styles()
        self._build_interface()
        self.after(100, self._poll_net_queue)

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

        display = self.active_roller.get()
        roller_name = "" if display == NO_ROLLER else display

        record = RollRecord(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            dice=result.dice,
            spec_dice=result.specialisation_dice,
            successes=result.successes,
            probability=probability,
            roller_name=roller_name,
        )
        self.roll_history.append(record)
        self._emit_roll(record)

        if self._session is not None:
            self._session.publish("roll", roll_record_to_dict(record))

    def roll_initiative(self) -> None:
        from random import randint
        total = randint(1, 10) + self.dice_number.get()
        self._interface.show_initiative(total)

    # ── Session management ─────────────────────────────────────────────────────

    def new_session(self) -> None:
        """Stop any existing session and start a new one with a fresh topic."""
        if self._session is not None:
            self._session.stop()
        topic = _generate_topic()
        self._session = NtfySession(topic=topic, event_queue=self._net_queue)
        self._session.start()
        self.session_topic.set(topic)

    # ── Network queue polling ──────────────────────────────────────────────────

    def _poll_net_queue(self) -> None:
        try:
            while True:
                event_type, data = self._net_queue.get_nowait()

                if event_type == "roll":
                    record = dict_to_roll_record(data)  # type: ignore[arg-type]
                    self.roll_history.append(record)
                    self._emit_roll(record)

                elif event_type == "sheet":
                    self._interface._pc_panel.on_sheet_received(data)  # type: ignore[arg-type]

                elif event_type == "sheet_trackers":
                    self._interface._pc_panel.on_trackers_received(data)  # type: ignore[arg-type]

        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_net_queue)

    # ── Persistence ────────────────────────────────────────────────────────────

    def save_lang_pref(self) -> None:
        dotenv.set_key(str(ENV_FILE_PATH), "LANG_PREF", locale.lang)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        var.set(int(float(value)))