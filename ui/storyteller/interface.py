from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from lang import locale
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from ui.storyteller.root import Root, RollRecord

# Dice faces highlighted when >= difficulty (used to colour individual results)
_HIT_FG = "#1b5e20"
_BOTCH_FG = "#b71c1c"
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


class Interface(ttk.Frame):
    """Root widget for the Storyteller interface."""

    def __init__(self, root: "Root") -> None:
        super().__init__(root)
        self.root = root

        self._additional_row: list[Widget] = []
        self._initiative_var = tk.StringVar(value="")

        self._build()
        root.on_roll(self._append_roll_entry)

    def _build(self) -> None:
        place_widgets([[
            self._frm_controls_panel(),
            self._frm_history_panel(),
        ]])

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
        command=None,
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

    # ── Toggle handlers ───────────────────────────────────────────────────────

    def _toggle_additional_options(self) -> None:
        if self.root.additional_options.get():
            for col_idx, widget in enumerate(self._additional_row):
                widget.grid(column=col_idx, row=4)
                widget.update()
        else:
            for widget in self._additional_row:
                widget.grid_remove()

    def _switch_language(self) -> None:
        locale.switch()
        self.root.save_lang_pref()

    # ── Left panel: title + controls + buttons ────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_controls_panel(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._tlabel(frm, "app.title", anchor="center", style="title.TLabel")],
            [self._frm_controls(frm)],
            [self._frm_buttons(frm)],
            [self._frm_sidebar(frm)],
        ])

    @frm(padding=5)
    def _frm_controls(self, frm: ttk.Frame) -> None:
        root = self.root
        rows: list[list[Any]] = []

        rows.append([
            self._tlabel(frm, "controls.dice", width=22, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=1, to=15, length=125,
                      variable=root.dice_number, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.dice_number)),
            ttk.Spinbox(frm, from_=1, to=50, textvariable=root.dice_number,
                        width=3, style="my.TSpinbox"),
        ])
        rows.append([
            self._tlabel(frm, "controls.difficulty", width=22, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=2, to=10, length=125,
                      variable=root.difficulty, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.difficulty)),
            ttk.Spinbox(frm, from_=2, to=10, textvariable=root.difficulty,
                        width=3, style="my.TSpinbox"),
        ])
        rows.append([
            self._tlabel(frm, "controls.auto_success", width=22, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=0, to=5, length=125,
                      variable=root.auto_success, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.auto_success)),
            ttk.Spinbox(frm, from_=0, to=5, textvariable=root.auto_success,
                        width=3, style="my.TSpinbox"),
        ])
        rows.append([
            self._dot_toggle(frm, locale.t("controls.specialisation"),
                             root.specialisation,
                             locale_key="controls.specialisation"),
            self._dot_toggle(frm, "∨", root.additional_options,
                             command=self._toggle_additional_options),
        ])
        place_widgets(rows)

        self._additional_row = [
            self._tlabel(frm, "controls.success_needed",
                         width=16, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=1, to=10, length=125,
                      variable=root.success_needed, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.success_needed)),
            ttk.Spinbox(frm, from_=1, to=10, textvariable=root.success_needed,
                        width=3, style="my.TSpinbox"),
        ]
        for col_idx, widget in enumerate(self._additional_row):
            widget.grid(column=col_idx, row=4)
            widget.update()
        if not root.additional_options.get():
            for widget in self._additional_row:
                widget.grid_remove()

    @frm(padding=5)
    def _frm_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._tbutton(frm, "controls.roll", style="L.TButton",
                          command=self.root.roll_and_calculate),
            self._tbutton(frm, "controls.initiative", style="M.TButton",
                          command=self.root.roll_initiative),
        ]])

    @frm(padding=2)
    def _frm_sidebar(self, frm: ttk.Frame) -> None:
        lang_btn = ttk.Button(frm, text=locale.t("lang_btn"), style="S.TButton",
                              command=self._switch_language)
        locale.register(lang_btn, "lang_btn")

        ttk.Label(frm, textvariable=self._initiative_var,
                  style="M.TLabel", anchor="center").grid(row=0, column=0, padx=8)
        lang_btn.grid(row=0, column=1, padx=4)

    # ── Right panel: scrollable roll history ──────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_history_panel(self, frm: ttk.Frame) -> None:
        ttk.Label(frm, text="⚄  Roll History", style="M.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        canvas = tk.Canvas(frm, width=380, height=420, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frm, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        frm.grid_rowconfigure(1, weight=1)
        frm.grid_columnconfigure(0, weight=1)

        self._history_canvas = canvas
        self._history_inner = ttk.Frame(canvas)
        self._history_win_id = canvas.create_window(
            (0, 0), window=self._history_inner, anchor="nw")

        self._history_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self._history_win_id, width=e.width),
        )
        self._bind_mousewheel(canvas)

    def _bind_mousewheel(self, canvas: tk.Canvas) -> None:
        def _scroll(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _scroll))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", lambda _: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda _: canvas.yview_scroll(1, "units"))

    # ── Roll entry widget ─────────────────────────────────────────────────────

    def _append_roll_entry(self, record: "RollRecord") -> None:
        """Prepend a new roll entry at the top of the history panel."""
        parent = self._history_inner

        # Shift all existing children down by one row
        for child in parent.winfo_children():
            info = child.grid_info()
            if info:
                child.grid(row=int(info["row"]) + 1)

        entry = self._build_roll_entry(parent, record)
        entry.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))

        parent.grid_columnconfigure(0, weight=1)

        # Scroll to top to show the new entry
        self._history_canvas.after(
            50, lambda: self._history_canvas.yview_moveto(0))

    def _build_roll_entry(self, parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        """Build a single roll entry frame."""
        frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
        frame.grid_columnconfigure(0, weight=1)

        outcome = record.outcome
        outcome_style = _OUTCOME_STYLE[outcome]
        count_style = _COUNT_STYLE[outcome]

        # ── Row 0: meta (dice / difficulty) + outcome label ───────────────────
        meta_text = (
            f"{record.dice_number}d  •  diff {record.difficulty}"
            + (f"  •  auto +{record.auto_success}" if record.auto_success else "")
        )
        ttk.Label(frame, text=meta_text, style="HistoryMeta.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(frame, text=outcome, style=outcome_style).grid(
            row=0, column=1, sticky="e", padx=(8, 0))

        # ── Row 1: dice results ───────────────────────────────────────────────
        dice_frame = self._build_dice_display(frame, record)
        dice_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # ── Row 2: spec dice (if any) + success count ─────────────────────────
        if record.spec_dice:
            spec_text = "spec: " + "  ".join(map(str, sorted(record.spec_dice, reverse=True)))
            ttk.Label(frame, text=spec_text, style="HistoryMeta.TLabel").grid(
                row=2, column=0, sticky="w")

        count_row = 2 if not record.spec_dice else 3
        successes_text = (
            f"{record.successes:+d}" if record.successes != 0 else "0"
        )
        ttk.Label(frame, text=successes_text, style=count_style).grid(
            row=count_row, column=1, sticky="e")

        prob_text = f"{record.probability:.1f}%"
        ttk.Label(frame, text=prob_text, style="HistoryMeta.TLabel").grid(
            row=count_row, column=0, sticky="w")

        return frame

    @staticmethod
    def _build_dice_display(parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        """Build a row of coloured die-value labels."""
        frame = ttk.Frame(parent, style="flat.TFrame")
        difficulty = record.difficulty

        for col, value in enumerate(sorted(record.dice, reverse=True)):
            if value == 1:
                fg = _BOTCH_FG
            elif value >= difficulty:
                fg = _HIT_FG
            else:
                fg = _NORMAL_FG

            lbl = ttk.Label(frame, text=str(value), style="HistoryDice.TLabel",
                            width=2, anchor="center")
            if fg:
                lbl.configure(foreground=fg)
            lbl.grid(row=0, column=col, padx=1)

        return frame

    # ── Public helpers ────────────────────────────────────────────────────────

    def show_initiative(self, total: int) -> None:
        """Display an initiative result next to the language button."""
        self._initiative_var.set(f"{locale.t('controls.initiative')}: {total}")