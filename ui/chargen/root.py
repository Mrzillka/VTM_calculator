from __future__ import annotations

import tkinter as tk
from tkinter import Toplevel, ttk

from game.character import Character
from lang import locale
from ui.chargen.wizard import Wizard
from ui.theme import theme
from ui.utils import apply_icon

WIZARD_WIDTH  = 580
WIZARD_HEIGHT = 680


class Root(Toplevel):
    """Character creation wizard window."""

    def __init__(self, parent=None, character: Character | None = None, on_finish=None) -> None:
        super().__init__(parent)
        self.title(locale.t("chargen.title"))
        self.resizable(False, False)
        self.geometry(f"{WIZARD_WIDTH}x{WIZARD_HEIGHT}")

        apply_icon(self, "icon.ico", inherit=False)

        self.character = character if character is not None else Character()
        self._wizard = Wizard(self, self.character, on_finish=on_finish)
        self._wizard.pack(fill="both", expand=True)

        def _on_theme() -> None:
            try:
                if self.winfo_exists():
                    self.configure(bg=theme.palette["bg"])
            except tk.TclError:
                pass

        theme.on_change(_on_theme)
        _on_theme()
