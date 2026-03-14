from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from config import WOUND_LEVELS
from lang import locale
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from game.models import RollRecord
    from ui.root import Root

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
    """
    Root widget of the application interface.

    Composes all child frames and delegates logic to the Root object.
    Toggle-able sections (trackers, additional options) are built once
    and shown/hidden via grid_remove() / grid() to avoid full redraws.
    """

    def __init__(self, root: "Root") -> None:
        super().__init__(root)
        self.root = root

        self._trackers_frame: ttk.Frame | None = None
        self._additional_row: list[Widget] = []
        self._sheet_window = None
        self._blood_cells: list[list[ttk.Label]] = []
        self._initiative_var = tk.StringVar(value="")

        self._build()
        root.on_roll(self._append_roll_entry)

    def _build(self) -> None:
        place_widgets([
            [self._frm_center()],
            [self._frm_bottom()],
        ])

    def refresh_blood_cells(self) -> None:
        """Re-evaluate which blood cells are active based on current blood_max_value."""
        self._disable_blood_cells()

    # ── Locale helpers ────────────────────────────────────────────────────────

    def _tlabel(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Label:
        """Create a ttk.Label bound to a locale key; updates on language switch."""
        lbl = ttk.Label(parent, text=locale.t(key), **kwargs)
        locale.register(lbl, key)
        return lbl

    def _tbutton(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Button:
        """Create a ttk.Button bound to a locale key; updates on language switch."""
        btn = ttk.Button(parent, text=locale.t(key), **kwargs)
        locale.register(btn, key)
        return btn

    # ── Dot helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _dot_toggle(
            parent: ttk.Frame,
            text: str,
            var: BooleanVar,
            command=None,
            locale_key: str | None = None,
    ) -> ttk.Frame:
        """
        Dot-label toggle — a click-driven replacement for ttk.Checkbutton.

        Pass *locale_key* to keep the label text in sync with language switches.
        """
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

    def _toggle_trackers(self) -> None:
        if self._trackers_frame is None:
            return
        if self.root.trackers.get():
            self._trackers_frame.grid()
        else:
            self._trackers_frame.grid_remove()

    def _toggle_additional_options(self) -> None:
        if self.root.additional_options.get():
            for col_idx, widget in enumerate(self._additional_row):
                widget.grid(column=col_idx, row=4)
                widget.update()
        else:
            for widget in self._additional_row:
                widget.grid_remove()

    def _open_character_sheet(self) -> None:
        """Open or focus the character sheet window."""
        if self._sheet_window is not None and self._sheet_window.winfo_exists():
            self._sheet_window.lift()
            self._sheet_window.focus_force()
            return
        from ui.charsheet.root import Root as CharacterSheet
        self._sheet_window = CharacterSheet(character=self.root.character)

    def _switch_language(self) -> None:
        """Toggle active language and save preference."""
        locale.switch()
        self.root.save_to_file()

    # ── Center block ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_center(self, frm: ttk.Frame) -> None:
        self._trackers_frame = self._frm_trackers(frm)
        widgets = [
            self._frm_main(frm),
            self._frm_history(frm),
            self._frm_sidebar(frm),
            self._trackers_frame,
        ]
        place_widgets([widgets])
        if not self.root.trackers.get():
            self._trackers_frame.grid_remove()

    @frm(padding=5)
    def _frm_main(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._tlabel(frm, "app.title", anchor="n", style="title.TLabel")],
            [self._frm_controls(frm)],
            [self._frm_main_buttons(frm)],
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
            ttk.Label(frm, textvariable=root.character.roll_penalty, width=3, style="S.TLabel"),
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
            self._dot_toggle(frm, locale.t("controls.send_telegram"),
                             root.is_send_to_telegram,
                             locale_key="controls.send_telegram"),
            self._dot_toggle(frm, "∨", root.additional_options,
                             command=self._toggle_additional_options),
        ])

        place_widgets(rows)

        success_lbl = self._tlabel(frm, "controls.success_needed",
                                   width=16, style="M.TLabel", anchor="e")
        self._additional_row = [
            success_lbl,
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
    def _frm_main_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._tbutton(frm, "controls.roll", style="L.TButton",
                          command=self.root.roll_and_calculate),
            self._tbutton(frm, "controls.initiative", style="M.TButton",
                          command=self.root.roll_initiative),
        ]])

    @frm(padding=5)
    def _frm_sidebar(self, frm: ttk.Frame) -> None:
        lang_btn = ttk.Button(frm, text=locale.t("lang_btn"), style="S.TButton",
                              command=self._switch_language)
        locale.register(lang_btn, "lang_btn")

        place_widgets([
            [self._dot_toggle(frm, locale.t("controls.trackers"),
                              self.root.trackers,
                              command=self._toggle_trackers,
                              locale_key="controls.trackers")],
            [self._tbutton(frm, "controls.sheet", style="S.TButton",
                           command=self._open_character_sheet)],
            [lang_btn],
            [ttk.Label(frm, textvariable=self._initiative_var,
                       style="M.TLabel", anchor="center")],
        ])

    # ── Roll history ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_history(self, frm: ttk.Frame) -> None:
        ttk.Label(frm, text="⚄  Roll History", style="M.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        canvas = tk.Canvas(frm, width=300, height=340, highlightthickness=0)
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

    def _append_roll_entry(self, record: "RollRecord") -> None:
        """Prepend a new roll entry at the top of the history panel."""
        parent = self._history_inner

        for child in parent.winfo_children():
            info = child.grid_info()
            if info:
                child.grid(row=int(info["row"]) + 1)

        entry = self._build_roll_entry(parent, record)
        entry.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        parent.grid_columnconfigure(0, weight=1)

        self._history_canvas.after(
            50, lambda: self._history_canvas.yview_moveto(0))

    def _build_roll_entry(self, parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        """Build a single roll entry frame."""
        frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
        frame.grid_columnconfigure(0, weight=1)

        outcome = record.outcome
        outcome_style = _OUTCOME_STYLE[outcome]
        count_style = _COUNT_STYLE[outcome]

        meta_text = (
            f"{record.dice_number}d  •  diff {record.difficulty}"
            + (f"  •  auto +{record.auto_success}" if record.auto_success else "")
        )
        ttk.Label(frame, text=meta_text, style="HistoryMeta.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(frame, text=outcome, style=outcome_style).grid(
            row=0, column=1, sticky="e", padx=(8, 0))

        dice_frame = self._build_dice_display(frame, record)
        dice_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        if record.spec_dice:
            spec_text = "spec: " + "  ".join(map(str, sorted(record.spec_dice, reverse=True)))
            ttk.Label(frame, text=spec_text, style="HistoryMeta.TLabel").grid(
                row=2, column=0, sticky="w")

        count_row = 2 if not record.spec_dice else 3
        successes_text = f"{record.successes:+d}" if record.successes != 0 else "0"
        ttk.Label(frame, text=successes_text, style=count_style).grid(
            row=count_row, column=1, sticky="e")
        ttk.Label(frame, text=f"{record.probability:.1f}%", style="HistoryMeta.TLabel").grid(
            row=count_row, column=0, sticky="w")

        return frame

    @staticmethod
    def _build_dice_display(parent: ttk.Frame, record: "RollRecord") -> ttk.Frame:
        """Build a row of coloured die-value labels."""
        frame = ttk.Frame(parent, style="flat.TFrame")
        for col, value in enumerate(sorted(record.dice, reverse=True)):
            if value == 1:
                fg = _BOTCH_FG
            elif value >= record.difficulty:
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
        """Display initiative result in the sidebar."""
        self._initiative_var.set(f"{locale.t('controls.initiative')}: {total}")

    # ── Trackers ──────────────────────────────────────────────────────────────

    @frm(padding=5, style="solid.TFrame")
    def _frm_trackers(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._frm_blood_humanity_will(frm),
            self._frm_wounds(frm),
        ]])

    @frm(padding=5)
    def _frm_blood_humanity_will(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._frm_blood(frm)],
            [self._frm_humanity(frm)],
            [self._frm_will(frm)],
        ])

    @frm(padding=5)
    def _frm_blood(self, frm: ttk.Frame) -> None:
        cells_frm = self._frm_blood_cells(frm)
        self._disable_blood_cells()
        place_widgets([
            [self._tlabel(frm, "trackers.blood", width=12, anchor="n", style="M.TLabel")],
            [cells_frm],
            [self._frm_max_blood(frm)],
        ])

    @frm(padding=5)
    def _frm_blood_cells(self, frm: ttk.Frame) -> None:
        self._blood_cells = []
        char = self.root.character

        for i in range(4):
            row_labels: list[ttk.Label] = []
            for j in range(10):
                var = char.blood[i][j]
                lbl = ttk.Label(
                    frm,
                    text="●" if var.get() else "○",
                    width=2,
                    style="S.TLabel",
                    cursor="hand2",
                )
                lbl.grid(row=i, column=j)
                var.trace_add(
                    "write",
                    lambda *_, l=lbl, v=var: l.configure(text="●" if v.get() else "○"),
                )
                lbl.bind("<Button-1>", lambda e, r=i, c=j: char.set_blood(r, c))
                row_labels.append(lbl)
            self._blood_cells.append(row_labels)

    def _disable_blood_cells(self) -> None:
        char = self.root.character
        max_blood = char.blood_max_value.get()
        for i, row in enumerate(self._blood_cells):
            for j, lbl in enumerate(row):
                active = i * 10 + j < max_blood
                if active:
                    lbl.configure(cursor="hand2", foreground="")
                    lbl.bind("<Button-1>", lambda e, r=i, c=j: char.set_blood(r, c))
                else:
                    lbl.configure(cursor="", foreground="gray")
                    lbl.unbind("<Button-1>")
                    char.blood[i][j].set(False)
        if char.blood_value.get() > max_blood:
            char.blood_value.set(max_blood)
            char.set_blood(load=True)

    @frm(padding=5)
    def _frm_max_blood(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._tlabel(frm, "trackers.max_blood", width=12, anchor="n", style="S.TLabel"),
            ttk.Spinbox(
                frm, from_=1, to=40,
                textvariable=self.root.character.blood_max_value,
                command=self._disable_blood_cells,
                width=3, style="my.TSpinbox",
            ),
        ]])

    @frm(padding=5)
    def _frm_wounds(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [self._tlabel(frm, "trackers.wounds", width=12, anchor="n", style="M.TLabel")],
            [self._frm_wounds_cells(frm)],
            [self._tbutton(frm, "trackers.heal", command=char.heal, style="M.TButton")],
        ])

    @frm(padding=5)
    def _frm_wounds_cells(self, frm: ttk.Frame) -> None:
        char = self.root.character
        rows = []
        for i, level in enumerate(WOUND_LEVELS):
            var = char.wounds[i]
            dot = ttk.Label(
                frm,
                text="●" if var.get() else "○",
                style="S.TLabel",
                cursor="hand2",
            )
            var.trace_add(
                "write",
                lambda *_, l=dot, v=var: l.configure(text="●" if v.get() else "○"),
            )
            dot.bind("<Button-1>", lambda e, y=i: char.set_wounds(y))

            name_lbl = ttk.Label(frm, text=locale.t(f"wound_levels.{level.name}"),
                                 width=15, anchor="e", style="S.TLabel")
            locale.register(name_lbl, f"wound_levels.{level.name}")

            rows.append([
                name_lbl,
                ttk.Label(frm, text=str(level.penalty or ""), anchor="w", style="S.TLabel"),
                dot,
            ])
        place_widgets(rows)

    @frm(padding=5)
    def _frm_humanity(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [self._tlabel(frm, "trackers.humanity_path", style="M.TLabel")],
            [self._frm_dot_tracker(frm, char.humanity, lambda x: char.set_humanity(x))],
        ])
        char.set_humanity(load=True)

    @frm(padding=5)
    def _frm_will(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [self._tlabel(frm, "trackers.will", style="M.TLabel")],
            [self._frm_will_cells(frm)],
        ])
        char.set_will(load=True)

    @frm(padding=5)
    def _frm_will_cells(self, frm: ttk.Frame) -> None:
        """Will dot tracker that respects willpower_max."""
        char = self.root.character
        labels = [
            ttk.Label(frm, text=str(i + 1), width=2, anchor="w", style="S.TLabel")
            for i in range(10)
        ]
        self._will_dots: list[ttk.Label] = []
        for i, var in enumerate(char.will):
            dot = ttk.Label(frm, text="●" if var.get() else "○",
                            width=2, style="S.TLabel", cursor="hand2")
            var.trace_add(
                "write",
                lambda *_, l=dot, v=var: l.configure(text="●" if v.get() else "○"),
            )
            self._will_dots.append(dot)
        place_widgets([labels, self._will_dots])

        char.will_value.trace_add("write", lambda *_: self._refresh_will_dots())
        char.willpower_max.trace_add("write", lambda *_: self._refresh_will_dots())
        self._refresh_will_dots()

    def _refresh_will_dots(self) -> None:
        """Enable or disable will dots based on willpower_max."""
        if not hasattr(self, "_will_dots"):
            return
        char = self.root.character
        max_val = char.willpower_max.get()
        for i, dot in enumerate(self._will_dots):
            if i >= max_val:
                dot.configure(cursor="", foreground="gray")
                dot.unbind("<Button-1>")
            else:
                dot.configure(cursor="hand2", foreground="")
                dot.bind("<Button-1>", lambda e, x=i: char.set_will(x))

    @frm(padding=5)
    def _frm_dot_tracker(self, frm: ttk.Frame, variables: list[BooleanVar], command) -> None:
        """Generic dot-tracker widget (Humanity)."""
        labels = [
            ttk.Label(frm, text=str(i + 1), width=2, anchor="w", style="S.TLabel")
            for i in range(10)
        ]
        dots = []
        for i, var in enumerate(variables):
            dot = ttk.Label(
                frm,
                text="●" if var.get() else "○",
                width=2,
                style="S.TLabel",
                cursor="hand2",
            )
            var.trace_add(
                "write",
                lambda *_, l=dot, v=var: l.configure(text="●" if v.get() else "○"),
            )
            dot.bind("<Button-1>", lambda e, x=i: command(x))
            dots.append(dot)
        place_widgets([labels, dots])

    # ── Bottom block ──────────────────────────────────────────────────────────

    @frm(padding=5, style="solid.TFrame")
    def _frm_bottom(self, frm) -> None:
        char = self.root.character
        place_widgets([[
            self._frm_options(frm),
            self._frm_stat_label(frm, "stats.blood",    char.blood_value),
            self._frm_stat_label(frm, "stats.wounds",   char.wounds_display),
            self._frm_stat_label(frm, "stats.humanity", char.humanity_value),
            self._frm_stat_label(frm, "stats.will",     char.will_value),
        ]])

    @frm(padding=5)
    def _frm_options(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._frm_name(frm),
            self._frm_initiative_spinboxes(frm),
            self._frm_action_buttons(frm),
        ]])

    @frm(padding=5)
    def _frm_name(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._tlabel(frm, "stats.character_name", anchor="e", style="M.TLabel")],
            [ttk.Entry(frm, textvariable=self.root.character.character_name, width=20,
                       style="my.TEntry")],
        ])

    @frm(padding=5)
    def _frm_initiative_spinboxes(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [self._tlabel(frm, "stats.dex", width=5, anchor="e", style="S.TLabel"),
             ttk.Spinbox(frm, from_=0, to=10, textvariable=char.initiative_bonus_dex,
                         width=3, style="my.TSpinbox")],
            [self._tlabel(frm, "stats.wits", width=5, anchor="e", style="S.TLabel"),
             ttk.Spinbox(frm, from_=0, to=10, textvariable=char.initiative_bonus_wits,
                         width=3, style="my.TSpinbox")],
        ])

    @frm(padding=5)
    def _frm_action_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Button(frm, textvariable=self.root.pooling_state,
                        command=self.root.start_bot_polling, style="S.TButton")],
            [self._tbutton(frm, "controls.save",
                           command=self.root.save_to_file, style="S.TButton")],
        ])

    @frm(padding=2, style='solid.TFrame')
    def _frm_stat_label(self, frm: ttk.Frame, title_key: str, var) -> None:
        """Small widget displaying a single tracker value with a localised title."""
        title = self._tlabel(frm, title_key, width=14, anchor="center", style="M.TLabel")
        place_widgets([
            [title],
            [ttk.Label(frm, textvariable=var, width=14, anchor="center", style="S.TLabel")],
        ])