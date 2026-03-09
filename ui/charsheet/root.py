from __future__ import annotations

from tkinter import BooleanVar, IntVar, StringVar, Toplevel
from tkinter import ttk

import dotenv

from config import ENV_FILE_PATH, FONT
from game.character import Character
from ui.charsheet.interface import Interface, place_widgets


class Root(Toplevel):
    """

    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.title('Character Sheet')
        self.resizable(True, True)

        self.character = Character()

        self._configure_grid()
        self._configure_styles()
        self._build_interface()
        self.load_from_file()

    def _configure_grid(self) -> None:
        pass

    def _configure_styles(self) -> None:
        s = ttk.Style()
        definitions = {
            "flat.TFrame": {"relief": "flat"},
            "solid.TFrame": {"relief": "solid"},
            "sheet.TButton": {"font": (FONT, 15)},
            "sheet.TEntry": {"font": (FONT, 10)},
            "sheet.TCheckbutton": {"font": (FONT, 10)},
            "sheet.title.TLabel": {"font": (FONT, 15, "bold", "italic")},
            "sheet.L.TLabel": {"font": (FONT, 15, "italic")},
            "sheet.M.TLabel": {"font": (FONT, 12, "italic")},
            "sheet.S.TLabel": {"font": (FONT, 10)},
            "sheet.Dot.TLabel": {"font": (FONT, 12)},
        }
        for name, opts in definitions.items():
            s.configure(name, **opts)

    def _build_interface(self) -> None:
        self._interface = Interface(self)
        place_widgets([[self._interface]])

    def load_from_file(self):
        pass