from __future__ import annotations

import tkinter as tk
from tkinter import Toplevel
from tkinter import ttk

from config import FONT
from game.character import Character
from ui.charsheet.interface import Interface


class Root(Toplevel):
    """Character sheet window with a vertically scrollable interface."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.title("Character Sheet")
        self.resizable(True, True)
        self.geometry("960x700")
        self.minsize(600, 400)

        self.character = Character()

        self._configure_styles()
        self._build_scrollable()
        self.load_from_file()

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

    def _build_scrollable(self) -> None:
        """Wrap the Interface in a Canvas-based scrollable container."""
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(win_id, width=e.width),
        )

        self._setup_mousewheel(canvas)

        self._interface = Interface(inner, self)
        self._interface.pack(fill="both", expand=True)

    def _setup_mousewheel(self, canvas: tk.Canvas) -> None:
        """Bind mousewheel scrolling to the canvas while the cursor is inside the window."""

        def _scroll_win(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _scroll_up(e: tk.Event) -> None:
            canvas.yview_scroll(-1, "units")

        def _scroll_down(e: tk.Event) -> None:
            canvas.yview_scroll(1, "units")

        def _bind(e: tk.Event = None) -> None:
            canvas.bind_all("<MouseWheel>", _scroll_win)
            canvas.bind_all("<Button-4>", _scroll_up)
            canvas.bind_all("<Button-5>", _scroll_down)

        def _unbind(e: tk.Event = None) -> None:
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind)
        canvas.bind("<Leave>", _unbind)

    def load_from_file(self) -> None:
        pass