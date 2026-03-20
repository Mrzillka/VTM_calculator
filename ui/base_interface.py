from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

from lang import locale
from ui.utils import place_widgets

if TYPE_CHECKING:
    from game.models import RollRecord

_HIT_FG    = "#1b5e20"
_BOTCH_FG  = "#b71c1c"
_NORMAL_FG = ""

_OUTCOME_STYLE: dict[str, str] = {
    "SUCCESS": "Success.TLabel",
    "FAILURE": "Failure.TLabel",
    "BOTCH":   "Botch.TLabel",
}
_COUNT_STYLE: dict[str, str] = {
    "SUCCESS": "SuccessCount.TLabel",
    "FAILURE": "FailureCount.TLabel",
    "BOTCH":   "BotchCount.TLabel",
}


class BaseInterface(ttk.Frame):
    """
    Shared helpers and roll-history widget used by all interface variants.

    Subclasses that use the history panel must call _build_scrollable_history()
    during construction; subclasses that use show_initiative() must initialise
    self._initiative_var before it is called.
    """

    _history_canvas: tk.Canvas
    _history_inner: ttk.Frame
    _history_win_id: int
    _initiative_var: tk.StringVar

    # ── Locale helpers ────────────────────────────────────────────────────────

    def _tlabel(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Label:
        lbl = ttk.Label(parent, text=locale.t(key), **kwargs)
        locale.register(lbl, key)
        return lbl

    def _tbutton(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Button:
        btn = ttk.Button(parent, text=locale.t(key), **kwargs)
        locale.register(btn, key)
        return btn

    # ── Dot toggle ────────────────────────────────────────────────────────────

    @staticmethod
    def _dot_toggle(
        parent: ttk.Frame,
        text: str,
        var: BooleanVar,
        command: Callable | None = None,
        locale_key: str | None = None,
    ) -> ttk.Frame:
        frame = ttk.Frame(parent, style="flat.TFrame")
        dot = ttk.Label(frame, text="●" if var.get() else "○", style="S.TLabel", cursor="hand2")
        lbl = ttk.Label(frame, text=text, style="S.TLabel", cursor="hand2")

        if locale_key:
            locale.register(lbl, locale_key)

        def _toggle(e=None) -> None:
            var.set(not var.get())
            if command:
                command()

        var.trace_add("write", lambda *_: dot.configure(text="●" if var.get() else "○"))
        dot.bind("<Button-1>", _toggle)
        lbl.bind("<Button-1>", _toggle)

        dot.grid(row=0, column=0, padx=(0, 2))
        lbl.grid(row=0, column=1)
        return frame

    # ── Mousewheel ────────────────────────────────────────────────────────────

    @staticmethod
    def _bind_mousewheel(canvas: tk.Canvas) -> None:
        def _scroll(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _scroll))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", lambda _: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda _: canvas.yview_scroll(1, "units"))

    # ── Scrollable history panel ──────────────────────────────────────────────

    def _build_scrollable_history(
        self, parent: ttk.Frame, *, width: int, height: int
    ) -> None:
        """Set up the scrollable canvas at row=1 of *parent*; populates history attributes."""
        canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

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
        self._bind_mousewheel(canvas)

        self._history_canvas = canvas
        self._history_inner = inner
        self._history_win_id = win_id

    def _append_roll_entry(self, record: "RollRecord") -> None:
        parent = self._history_inner
        for child in parent.winfo_children():
            info = child.grid_info()
            if info:
                child.grid(row=int(info["row"]) + 1)

        entry = self._build_roll_entry(parent, record)
        entry.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        parent.grid_columnconfigure(0, weight=1)

        self._history_canvas.after(50, lambda: self._history_canvas.yview_moveto(0))

    def _build_roll_entry(self, parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
        frame.grid_columnconfigure(0, weight=1)

        outcome = record.outcome
        current_row = 0

        # Optional roller name header (NPC or character name).
        if record.roller_name:
            ttk.Label(frame, text=record.roller_name, style="M.TLabel", anchor="w").grid(
                row=current_row, column=0, columnspan=2, sticky="w"
            )
            current_row += 1

        meta_text = (
            f"{record.dice_number}d  •  diff {record.difficulty}"
            + (f"  •  auto +{record.auto_success}" if record.auto_success else "")
        )
        ttk.Label(frame, text=meta_text, style="HistoryMeta.TLabel").grid(
            row=current_row, column=0, sticky="w")
        ttk.Label(frame, text=outcome, style=_OUTCOME_STYLE[outcome]).grid(
            row=current_row, column=1, sticky="e", padx=(8, 0))
        current_row += 1

        self._build_dice_display(frame, record).grid(
            row=current_row, column=0, columnspan=2, sticky="w", pady=(2, 0))
        current_row += 1

        if record.spec_dice:
            spec_text = "spec: " + "  ".join(map(str, sorted(record.spec_dice, reverse=True)))
            ttk.Label(frame, text=spec_text, style="HistoryMeta.TLabel").grid(
                row=current_row, column=0, sticky="w")
            current_row += 1

        successes_text = f"{record.successes:+d}" if record.successes != 0 else "0"
        ttk.Label(frame, text=successes_text, style=_COUNT_STYLE[outcome]).grid(
            row=current_row, column=1, sticky="e")
        ttk.Label(frame, text=f"{record.probability:.1f}%", style="HistoryMeta.TLabel").grid(
            row=current_row, column=0, sticky="w")

        return frame

    @staticmethod
    def _build_dice_display(parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        frame = ttk.Frame(parent, style="flat.TFrame")
        for col, value in enumerate(sorted(record.dice, reverse=True)):
            fg = (
                _BOTCH_FG if value == 1
                else _HIT_FG if value >= record.difficulty
                else _NORMAL_FG
            )
            lbl = ttk.Label(frame, text=str(value), style="HistoryDice.TLabel",
                            width=2, anchor="center")
            if fg:
                lbl.configure(foreground=fg)
            lbl.grid(row=0, column=col, padx=1)
        return frame

    # ── Initiative display ────────────────────────────────────────────────────

    def show_initiative(self, total: int) -> None:
        self._initiative_var.set(f"{locale.t('controls.initiative')}: {total}")