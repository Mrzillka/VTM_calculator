from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, Toplevel
from tkinter import ttk

from game.character import Character
from ui.charsheet.interface import Interface
from ui.styles import configure_sheet_styles


class Root(Toplevel):
    """Character sheet window with a vertically scrollable interface."""

    def __init__(self, parent=None, character: Character | None = None) -> None:
        super().__init__(parent)
        self.title("Character Sheet")
        self.resizable(True, False)
        self.geometry("1150x750")
        self.minsize(700, 450)

        self.character = character if character is not None else Character()
        self.locked = BooleanVar(value=False)

        self._configure_styles()
        self._build_scrollable()

    def _configure_styles(self) -> None:
        configure_sheet_styles(ttk.Style())

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
        """
        Bind mousewheel scrolling while the cursor is anywhere inside the window.

        Binds to the Toplevel rather than the canvas so that the <Enter> event
        fires reliably when the window is opened or re-focused.
        """
        def _scroll_win(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _scroll_up(e: tk.Event) -> None:
            canvas.yview_scroll(-1, "units")

        def _scroll_down(e: tk.Event) -> None:
            canvas.yview_scroll(1, "units")

        def _bind(e: tk.Event = None) -> None:
            self.bind_all("<MouseWheel>", _scroll_win)
            self.bind_all("<Button-4>", _scroll_up)
            self.bind_all("<Button-5>", _scroll_down)

        def _unbind(e: tk.Event = None) -> None:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")

        self.bind("<Enter>", _bind)
        self.bind("<Leave>", _unbind)

    def save(self) -> None:
        """Persist character data to JSON."""
        self.character.save()