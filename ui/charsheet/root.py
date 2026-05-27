from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import BooleanVar, IntVar, Toplevel
from tkinter import ttk
from typing import Callable

from game.character import Character
from ui.charsheet.interface import CharsheetInterface
from ui.constants import MOUSEWHEEL_DIVISOR, SHEET_HEIGHT, SHEET_MIN_HEIGHT, SHEET_MIN_WIDTH, SHEET_WIDTH
from ui.styles import configure_sheet_styles
from ui.theme import theme
from ui.utils import apply_icon


class CharsheetWindow(Toplevel):
    """Character sheet window with a vertically scrollable interface."""

    def __init__(
        self,
        parent=None,
        character: Character | None = None,
        *,
        read_only: bool = False,
        save_path: Path | None = None,
        send_sheet_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Character Sheet")
        self.resizable(False, False)
        self.geometry(f"{SHEET_WIDTH}x{SHEET_HEIGHT}")
        self.minsize(SHEET_MIN_WIDTH, SHEET_MIN_HEIGHT)

        apply_icon(self, "icon.ico", inherit=False)

        self._save_path = save_path
        # Callback invoked by the Send button in the toolbar; None = button hidden.
        self._send_sheet_callback = send_sheet_callback
        self.character = character if character is not None else Character()
        self.locked = BooleanVar(value=False)
        self.xp_spent = IntVar(value=0)

        self._configure_styles()
        self._build_scrollable()

        if read_only:
            self.locked.set(True)
            self._interface._apply_lock()

    def _configure_styles(self) -> None:
        configure_sheet_styles(ttk.Style(), theme.palette)

    def _build_scrollable(self) -> None:
        """Wrap the Interface in a Canvas-based scrollable container."""
        canvas = tk.Canvas(self, highlightthickness=0, bg=theme.palette["bg"])
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

        self._interface = CharsheetInterface(inner, self)
        self._interface.pack(fill="both", expand=True)

        def _on_theme_change() -> None:
            try:
                if not self.winfo_exists():
                    return
            except tk.TclError:
                return
            canvas.configure(bg=theme.palette["bg"])
            self.configure(bg=theme.palette["bg"])
            configure_sheet_styles(ttk.Style(), theme.palette)
            self._interface._refresh_mf_totals()
            self._interface._refresh_wp_cells()
            self._interface._refresh_humanity_cells()
            self._interface._refresh_sheet_blood_cells()

        theme.on_change(_on_theme_change)

    def _setup_mousewheel(self, canvas: tk.Canvas) -> None:
        def _scroll_win(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / MOUSEWHEEL_DIVISOR)), "units")

        def _scroll_up(e: tk.Event = None) -> None:
            canvas.yview_scroll(-1, "units")

        def _scroll_down(e: tk.Event = None) -> None:
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
        """Persist character data to JSON, using save_path if provided."""
        self.character.save(path=self._save_path)

    def send_sheet(self) -> None:
        """Invoke the send callback if one is registered."""
        if self._send_sheet_callback is not None:
            self._send_sheet_callback()