from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

from lang import locale
from ui.constants import MOUSEWHEEL_DIVISOR
from ui.theme import theme
from ui.utils import place_widgets

if TYPE_CHECKING:
    from game.models import RollRecord

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


class LocaleWidgetsMixin:
    """Mixin providing locale-aware widget factory methods."""

    def _tlabel(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Label:
        lbl = ttk.Label(parent, text=locale.t(key), **kwargs)
        locale.register(lbl, key)
        return lbl

    def _tbutton(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Button:
        btn = ttk.Button(parent, text=locale.t(key), **kwargs)
        locale.register(btn, key)
        return btn


class BaseInterface(ttk.Frame, LocaleWidgetsMixin):
    """
    Shared helpers and roll-history widget used by all interface variants.

    Subclasses that use the history panel must call _build_scrollable_history()
    during construction.
    """

    _history_canvas: tk.Canvas
    _history_inner: ttk.Frame
    _history_win_id: int

    # ── Dot labels ────────────────────────────────────────────────────────────

    @staticmethod
    def _dot_trace(label: ttk.Label, var: BooleanVar) -> Callable:
        """Return a write-trace callback that re-renders a ●/○ dot label.

        Guarded against widget destruction: if *label* has been destroyed while
        *var* lives on (e.g. the stats tab rebuilds its children), the callback is
        a no-op instead of raising ``TclError``.  Only the text is touched —
        foreground is left to external managers (disable / grey-out logic).
        """
        def _cb(*_) -> None:
            try:
                if label.winfo_exists():
                    label.configure(text="●" if var.get() else "○")
            except tk.TclError:
                pass
        return _cb

    def _make_dot(
        self, parent: ttk.Frame, var: BooleanVar,
        *, command: Callable | None = None, **label_kwargs,
    ) -> ttk.Label:
        """Create a ●/○ label bound to *var* via a guarded trace.

        *command* is bound to ``<Button-1>`` when given.  Extra keyword args are
        forwarded to ``ttk.Label`` (``style`` and ``cursor`` default to the
        clickable-dot look).
        """
        label_kwargs.setdefault("style", "S.TLabel")
        label_kwargs.setdefault("cursor", "hand2")
        lbl = ttk.Label(parent, text="●" if var.get() else "○", **label_kwargs)
        var.trace_add("write", self._dot_trace(lbl, var))
        if command is not None:
            lbl.bind("<Button-1>", command)
        return lbl

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

        var.trace_add("write", BaseInterface._dot_trace(dot, var))
        dot.bind("<Button-1>", _toggle)
        lbl.bind("<Button-1>", _toggle)

        dot.grid(row=0, column=0, padx=(0, 2))
        lbl.grid(row=0, column=1)
        return frame

    # ── Mousewheel ────────────────────────────────────────────────────────────

    @staticmethod
    def _bind_mousewheel(canvas: tk.Canvas) -> None:
        def _scroll(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / MOUSEWHEEL_DIVISOR)), "units")

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _scroll))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", lambda _: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda _: canvas.yview_scroll(1, "units"))

    # ── Scrollable history panel ──────────────────────────────────────────────

    def _build_scrollable_history(
        self, parent: ttk.Frame, *, width: int, height: int
    ) -> None:
        """Set up the scrollable canvas at row=1 of *parent*; populates history attributes."""
        canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0,
                           bg=theme.palette["bg"])
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _update_canvas_bg() -> None:
            try:
                if canvas.winfo_exists():
                    canvas.configure(bg=theme.palette["bg"])
            except tk.TclError:
                pass
        theme.on_change(_update_canvas_bg)

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
        if record.roll_type == "INITIATIVE":
            return self._build_initiative_entry(parent, record)
        return self._build_dice_entry(parent, record)

    def _build_initiative_entry(self, parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        """History card for an initiative roll."""
        frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
        frame.grid_columnconfigure(0, weight=1)

        if record.roller_name:
            ttk.Label(frame, text=record.roller_name, style="M.TLabel", anchor="w").grid(
                row=0, column=0, columnspan=2, sticky="w"
            )

        ttk.Label(
            frame,
            text=locale.t("controls.initiative"),
            style="HistoryMeta.TLabel",
        ).grid(row=1, column=0, sticky="w")

        # dice[0] is the raw d10 result; auto_success carries dex+wits bonus.
        raw = record.dice[0] if record.dice else 0
        bonus = record.auto_success
        detail = f"d10={raw}  +{bonus}"
        ttk.Label(frame, text=detail, style="HistoryMeta.TLabel").grid(
            row=2, column=0, sticky="w"
        )

        ttk.Label(
            frame,
            text=str(record.successes),
            style="SuccessCount.TLabel",
        ).grid(row=2, column=1, sticky="e")

        return frame

    def _build_dice_entry(self, parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        """History card for a normal or damage/soak roll."""
        frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
        frame.grid_columnconfigure(0, weight=1)

        outcome = record.outcome
        current_row = 0

        if record.roller_name:
            ttk.Label(frame, text=record.roller_name, style="M.TLabel", anchor="w").grid(
                row=current_row, column=0, columnspan=2, sticky="w"
            )
            current_row += 1

        meta_text = (
            f"{record.dice_number}d  •  diff {record.difficulty}"
            + (f"  •  auto +{record.auto_success}" if record.auto_success else "")
        )
        if record.roll_type == "DAMAGE":
            meta_text += f"  •  {locale.t('controls.damage_soak')}"
        elif record.roll_type == "QUICK":
            meta_text += f"  •  {locale.t('controls.quick_rolls')}"

        ttk.Label(frame, text=meta_text, style="HistoryMeta.TLabel").grid(
            row=current_row, column=0, sticky="w")
        ttk.Label(frame, text=outcome, style=_OUTCOME_STYLE[outcome]).grid(
            row=current_row, column=1, sticky="e", padx=(8, 0))
        current_row += 1

        self._build_dice_display(frame, record).grid(
            row=current_row, column=0, columnspan=2, sticky="w", pady=(2, 0))
        current_row += 1

        if record.specialisation_dice:
            spec_text = "spec: " + "  ".join(map(str, sorted(record.specialisation_dice, reverse=True)))
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
        palette = theme.palette
        frame = ttk.Frame(parent, style="flat.TFrame")
        for col, value in enumerate(sorted(record.dice, reverse=True)):
            is_hit   = value >= record.difficulty
            is_botch = value == 1 and record.roll_type != "DAMAGE"
            fg = (
                palette["botch_fg"] if is_botch
                else palette["hit_fg"] if is_hit
                else palette["normal_fg"]
            )
            lbl = ttk.Label(frame, text=str(value), style="HistoryDice.TLabel",
                            width=2, anchor="center")
            if fg:
                lbl.configure(foreground=fg)
            lbl.grid(row=0, column=col, padx=1)
        return frame