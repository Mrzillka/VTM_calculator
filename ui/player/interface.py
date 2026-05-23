from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, StringVar
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from config import BLOOD_COLS, BLOOD_ROWS, MAX_DOT_TRACKER, SPEC_MIN_DOTS, WOUND_LEVELS
from lang import locale
from ui.base_interface import BaseInterface
from ui.theme import theme
from ui.constants import (
    AUTO_SUCCESS_MAX, DICE_MAX, DICE_MIN, DIFFICULTY_MAX, DIFFICULTY_MIN,
    HISTORY_HEIGHT, HISTORY_WIDTH, SCALE_LENGTH, SUCCESS_NEEDED_MAX,
)
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from ui.player.root import PlayerRoot


class PlayerInterface(BaseInterface):
    """Root widget of the main application interface."""

    def __init__(self, root: "PlayerRoot") -> None:
        super().__init__(root)
        self.root = root

        self._sheet_window = None
        self._chargen_window = None
        self._blood_cells: list[list[ttk.Label]] = []

        self._build()
        root.on_roll(self._append_roll_entry)

    def _build(self) -> None:
        place_widgets([
            [self._frm_center()],
            [self._frm_bottom()],
        ])

    def refresh_blood_cells(self) -> None:
        self._disable_blood_cells()

    # ── Toggle handlers ───────────────────────────────────────────────────────

    def _open_character_sheet(self) -> None:
        if self._sheet_window is not None and self._sheet_window.winfo_exists():
            self._sheet_window.lift()
            self._sheet_window.focus_force()
            return
        from ui.charsheet.root import CharsheetWindow
        self._sheet_window = CharsheetWindow(
            character=self.root.character,
            send_sheet_callback=self.root.send_sheet_to_server,
        )

    def _open_chargen(self) -> None:
        if self._chargen_window is not None and self._chargen_window.winfo_exists():
            self._chargen_window.lift()
            self._chargen_window.focus_force()
            return
        from game.character import Character
        from ui.chargen.root import ChargenWindow
        self._chargen_window = ChargenWindow(
            character=Character(),
            on_finish=self._on_chargen_finish,
            min_will_var=self.root.chargen_min_will,
        )

    def _on_chargen_finish(self, new_char) -> None:
        data = new_char.to_dict()
        self.root.character.load(data)
        self.refresh_blood_cells()
        self.root.character.apply_trackers()
        self.root.save_to_file()

    def _switch_language(self) -> None:
        locale.switch()
        self.root.save_to_file()

    # ── Center block ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_center(self, frm: ttk.Frame) -> None:
        nb = self._build_tabs(frm)
        place_widgets([[self._frm_main(frm), nb]])

    def _build_tabs(self, parent: ttk.Frame) -> ttk.Notebook:
        nb = ttk.Notebook(parent)

        # Tab 1: Roll History
        hist_tab = self._frm_history(nb)
        nb.add(hist_tab, text=locale.t("roll_history"))

        # Tab 2: Trackers
        track_tab = self._frm_trackers(nb)
        nb.add(track_tab, text=locale.t("controls.trackers"))

        # Tab 3: Stats (read-only attribute/ability snapshot)
        stats_tab = self._frm_stats_tab(nb)
        nb.add(stats_tab, text=locale.t("controls.stats_tab"))

        # Tab 4: Settings
        settings_tab = self._frm_settings_tab(nb)
        nb.add(settings_tab, text=locale.t("controls.settings"))

        def _update_tab_titles() -> None:
            nb.tab(0, text=locale.t("roll_history"))
            nb.tab(1, text=locale.t("controls.trackers"))
            nb.tab(2, text=locale.t("controls.stats_tab"))
            nb.tab(3, text=locale.t("controls.settings"))
            self._rebuild_stats_tab()

        locale.on_change(_update_tab_titles)
        return nb

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
            ttk.Scale(frm, from_=DICE_MIN, to=DICE_MAX, length=SCALE_LENGTH,
                      variable=root.dice_number, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.dice_number)),
            ttk.Spinbox(frm, from_=DICE_MIN, to=50, textvariable=root.dice_number,
                        width=3, style="my.TSpinbox"),
            ttk.Label(frm, textvariable=root.character.roll_penalty, width=3, style="S.TLabel"),
        ])
        rows.append([
            self._tlabel(frm, "controls.difficulty", width=22, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=DIFFICULTY_MIN, to=DIFFICULTY_MAX, length=SCALE_LENGTH,
                      variable=root.difficulty, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.difficulty)),
            ttk.Spinbox(frm, from_=DIFFICULTY_MIN, to=DIFFICULTY_MAX, textvariable=root.difficulty,
                        width=3, style="my.TSpinbox"),
        ])
        rows.append([
            self._tlabel(frm, "controls.auto_success", width=22, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=0, to=AUTO_SUCCESS_MAX, length=SCALE_LENGTH,
                      variable=root.auto_success, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.auto_success)),
            ttk.Spinbox(frm, from_=0, to=AUTO_SUCCESS_MAX, textvariable=root.auto_success,
                        width=3, style="my.TSpinbox"),
        ])
        rows.append([
            self._dot_toggle(frm, locale.t("controls.specialisation"),
                             root.specialisation,
                             locale_key="controls.specialisation"),
        ])
        rows.append([
            self._tlabel(frm, "controls.success_needed", width=22, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=1, to=SUCCESS_NEEDED_MAX, length=SCALE_LENGTH,
                      variable=root.success_needed, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.success_needed)),
            ttk.Spinbox(frm, from_=1, to=SUCCESS_NEEDED_MAX, textvariable=root.success_needed,
                        width=3, style="my.TSpinbox"),
        ])
        place_widgets(rows)

    @frm(padding=5)
    def _frm_main_buttons(self, frm: ttk.Frame) -> None:
        char = self.root.character
        initiative_var = StringVar()

        def _update_initiative_text(*_) -> None:
            bonus = char.dex_value.get() + char.dex_boost.get() + char.wits_value.get()
            initiative_var.set(f"{locale.t('controls.initiative')} (+{bonus})")

        for var in (char.dex_value, char.dex_boost, char.wits_value):
            var.trace_add("write", _update_initiative_text)
        locale.on_change(_update_initiative_text)
        _update_initiative_text()

        place_widgets([[
            self._tbutton(frm, "controls.roll", style="L.TButton",
                          command=self.root.roll_and_calculate),
            ttk.Button(frm, textvariable=initiative_var, style="M.TButton",
                       command=self.root.roll_initiative),
            self._tbutton(frm, "controls.damage_soak", style="M.TButton",
                          command=self.root.roll_damage_soak),
        ]])

    # ── Stats tab ─────────────────────────────────────────────────────────────

    @frm(padding=0, style="solid.TFrame")
    def _frm_stats_tab(self, outer: ttk.Frame) -> None:
        canvas = tk.Canvas(outer, highlightthickness=0, bg=theme.palette["bg"])
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        inner = ttk.Frame(canvas, padding=5)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        self._bind_mousewheel(canvas)

        self._stats_tab_frame = inner
        self._stats_rebuild_pending = False
        self._build_stats_content(inner)

        def _update_stats_canvas_bg() -> None:
            try:
                if canvas.winfo_exists():
                    canvas.configure(bg=theme.palette["bg"])
            except tk.TclError:
                pass

        def _on_theme_stats() -> None:
            try:
                if self._stats_tab_frame.winfo_exists():
                    self._rebuild_stats_tab()
            except tk.TclError:
                pass

        theme.on_change(_update_stats_canvas_bg)
        theme.on_change(_on_theme_stats)

        char = self.root.character
        for cat_data in char.attributes.values():
            for stat_data in cat_data.values():
                for var in stat_data["vars"]:
                    var.trace_add("write", self._schedule_stats_rebuild)
        for cat_data in char.abilities.values():
            for stat_data in cat_data.values():
                for var in stat_data["vars"]:
                    var.trace_add("write", self._schedule_stats_rebuild)
        for cat_rows in char.custom_abilities.values():
            for row in cat_rows:
                for var in row["vars"]:
                    var.trace_add("write", self._schedule_stats_rebuild)

    def _schedule_stats_rebuild(self, *_) -> None:
        if not self._stats_rebuild_pending:
            self._stats_rebuild_pending = True
            self._stats_tab_frame.after(0, self._rebuild_stats_tab)

    def _rebuild_stats_tab(self) -> None:
        self._stats_rebuild_pending = False
        frm = self._stats_tab_frame
        for child in frm.winfo_children():
            child.destroy()
        self._build_stats_content(frm)

    def _build_stats_content(self, parent: ttk.Frame) -> None:
        char = self.root.character

        def _stat_row(col_frame: ttk.Frame, name: str, count: int, spec: str = "") -> None:
            row = ttk.Frame(col_frame, style="flat.TFrame")
            row.pack(anchor="w", fill="x", pady=(1, 0))
            ttk.Label(row, text=name, width=13, anchor="e", style="S.TLabel").pack(side="left")
            dot_lbl = ttk.Label(row, text="●" * count, anchor="w", style="S.TLabel")
            dot_lbl.configure(foreground=theme.palette["dot_fg"])
            dot_lbl.pack(side="left", padx=(3, 0))
            if spec and count >= SPEC_MIN_DOTS:
                spec_row = ttk.Frame(col_frame, style="flat.TFrame")
                spec_row.pack(anchor="w", fill="x", pady=(0, 2))
                ttk.Label(spec_row, width=13, style="S.TLabel").pack(side="left")
                spec_lbl = ttk.Label(spec_row, text=f"({spec})", anchor="w", style="S.TLabel")
                spec_lbl.configure(foreground=theme.palette["spec_fg"],
                                   font=("TkDefaultFont", 8, "italic"))
                spec_lbl.pack(side="left", padx=(3, 0))

        def _build_section(
            categories: dict,
            cat_locale_prefix: str,
            name_locale_prefix: str,
            row_offset: int,
        ) -> None:
            for col_idx, (cat_name, cat_data) in enumerate(categories.items()):
                col_frame = ttk.Frame(parent, style="flat.TFrame")
                col_frame.grid(row=row_offset, column=col_idx, sticky="nw", padx=4, pady=(0, 4))
                ttk.Label(
                    col_frame,
                    text=locale.t(f"{cat_locale_prefix}.{cat_name}"),
                    style="M.TLabel",
                ).pack(anchor="center", pady=(0, 2))
                for stat_name, stat_data in cat_data.items():
                    count = sum(v.get() for v in stat_data["vars"])
                    if count > 0:
                        _stat_row(col_frame, locale.t(f"{name_locale_prefix}.{stat_name}"), count, stat_data["spec"].get())

        _build_section(char.attributes, "sheet.attr_categories", "sheet.attr_names", 0)

        ttk.Separator(parent, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=4,
        )

        _build_section(char.abilities, "sheet.ability_categories", "sheet.ability_names", 2)

        for col_idx, cat_name in enumerate(char.abilities):
            slaves = parent.grid_slaves(row=2, column=col_idx)
            if not slaves:
                continue
            col_frame = slaves[0]
            for row in char.custom_abilities.get(cat_name, []):
                name = row["name"].get().strip()
                count = sum(v.get() for v in row["vars"])
                if name and count > 0:
                    _stat_row(col_frame, name, count, row["spec"].get())

    # ── Roll history ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_history(self, frm: ttk.Frame) -> None:
        self._build_scrollable_history(frm, width=HISTORY_WIDTH, height=HISTORY_HEIGHT)

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
            [self._frm_blood(frm),     self._frm_physical_attributes(frm)],
            [self._frm_humanity(frm),  self._frm_will(frm)],
        ])

    @frm(padding=5)
    def _frm_blood(self, frm: ttk.Frame) -> None:
        char = self.root.character
        cells_frm = self._frm_blood_cells(frm)
        self._disable_blood_cells()

        per_turn_frm = ttk.Frame(frm, style="flat.TFrame")
        self._tlabel(per_turn_frm, "trackers.blood_per_turn",
                     style="S.TLabel", anchor="e").grid(row=0, column=0, sticky="e")
        ttk.Label(per_turn_frm, textvariable=char.blood_per_turn,
                  style="S.TLabel", width=2).grid(row=0, column=1, sticky="w", padx=(4, 0))

        place_widgets([
            [self._tlabel(frm, "trackers.blood", width=12, anchor="n", style="M.TLabel")],
            [cells_frm],
            [per_turn_frm],
        ])

    @frm(padding=5)
    def _frm_blood_cells(self, frm: ttk.Frame) -> None:
        self._blood_cells = []
        char = self.root.character

        for i in range(BLOOD_ROWS):
            row_labels: list[ttk.Label] = []
            for j in range(BLOOD_COLS):
                var = char.blood[i][j]
                lbl = ttk.Label(
                    frm, text="●" if var.get() else "○",
                    width=2, style="S.TLabel", cursor="hand2",
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
                active = i * BLOOD_COLS + j < max_blood
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
    def _frm_physical_attributes(self, frm: ttk.Frame) -> None:
        char = self.root.character
        attrs = [
            ("Str", char.str_boost, char.attributes["Physical"]["Strength"]["vars"]),
            ("Dex", char.dex_boost, char.attributes["Physical"]["Dexterity"]["vars"]),
            ("Sta", char.sta_boost, char.attributes["Physical"]["Stamina"]["vars"]),
        ]

        self._tlabel(frm, "trackers.physical", style="M.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        for row_idx, (label, boost_var, base_vars) in enumerate(attrs, start=1):
            display_var = StringVar()

            def _refresh(*_, bv=boost_var, bvars=base_vars, dv=display_var) -> None:
                base  = sum(v.get() for v in bvars)
                boost = bv.get()
                dv.set(f"{base}+{boost}={base + boost}")

            for bv in base_vars:
                bv.trace_add("write", _refresh)
            boost_var.trace_add("write", _refresh)
            _refresh()

            ttk.Label(frm, text=label, style="S.TLabel", width=4, anchor="e").grid(
                row=row_idx, column=0, sticky="e"
            )
            ttk.Label(frm, textvariable=display_var, style="S.TLabel",
                      width=8, anchor="center").grid(row=row_idx, column=1)
            ttk.Button(
                frm, text="+1",
                command=lambda bv=boost_var, bvars=base_vars: char.boost_attribute(bv, bvars),
                style="S.TButton", width=3,
            ).grid(row=row_idx, column=2, padx=(4, 0))

        end_row = len(attrs) + 1
        self._tbutton(frm, "trackers.end_scene",
                      command=char.end_scene, style="M.TButton").grid(
            row=end_row, column=0, columnspan=3, sticky="ew", pady=(6, 0)
        )

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
            dot = ttk.Label(frm, text="●" if var.get() else "○",
                            style="S.TLabel", cursor="hand2")
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
        char = self.root.character
        labels = [
            ttk.Label(frm, text=str(i + 1), width=2, anchor="w", style="S.TLabel")
            for i in range(MAX_DOT_TRACKER)
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
        labels = [
            ttk.Label(frm, text=str(i + 1), width=2, anchor="w", style="S.TLabel")
            for i in range(MAX_DOT_TRACKER)
        ]
        dots = []
        for i, var in enumerate(variables):
            dot = ttk.Label(frm, text="●" if var.get() else "○",
                            width=2, style="S.TLabel", cursor="hand2")
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
        self._frm_quick_rolls(frm).grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._frm_stats_row(frm).grid(row=0, column=1, sticky="ew")
        self._frm_info_row(frm).grid(row=1, column=1, sticky="ew")
        frm.grid_columnconfigure(1, weight=1)

    @frm(padding=4, style="solid.TFrame")
    def _frm_quick_rolls(self, frm: ttk.Frame) -> None:
        root = self.root

        self._tlabel(frm, "controls.quick_rolls", style="S.TLabel").grid(
            row=0, column=0, columnspan=5, sticky="w")

        pen_var = StringVar()
        def _upd_pen(*_):
            pen_var.set(f"Pen: {root.quick_penalty.get()}")
        root.quick_penalty.trace_add("write", _upd_pen)
        _upd_pen()
        ttk.Label(frm, textvariable=pen_var, style="S.TLabel").grid(
            row=0, column=5, padx=(6, 2))

        self._qr_attr_cbs: list[ttk.Combobox] = []
        self._qr_abil_cbs: list[ttk.Combobox] = []

        for i, (attr_var, abil_var, diff_var, spec_var) in enumerate(root.quick_rolls):
            r = i + 1
            attr_cb = ttk.Combobox(
                frm, textvariable=attr_var,
                state="readonly", width=12,
            )
            attr_cb.grid(row=r, column=0, padx=2, pady=1)
            self._qr_attr_cbs.append(attr_cb)

            _prev_attr = [attr_var.get()]

            def _on_attr_sel(event, var=attr_var, prev=_prev_attr):
                val = var.get()
                if val.startswith("──"):
                    var.set(prev[0])
                else:
                    prev[0] = val

            attr_cb.bind("<<ComboboxSelected>>", _on_attr_sel)

            abil_cb = ttk.Combobox(
                frm, textvariable=abil_var, state="readonly", width=18,
            )
            abil_cb.configure(
                postcommand=lambda cb=abil_cb: cb.configure(
                    values=self._build_abil_cb_values()
                )
            )
            abil_cb.grid(row=r, column=1, padx=2, pady=1, sticky="ew")
            self._qr_abil_cbs.append(abil_cb)

            _prev_abil = [abil_var.get()]

            def _on_abil_sel(event, var=abil_var, prev=_prev_abil):
                val = var.get()
                if val.startswith("──"):
                    var.set(prev[0])
                else:
                    prev[0] = val

            abil_cb.bind("<<ComboboxSelected>>", _on_abil_sel)

            ttk.Spinbox(
                frm, textvariable=diff_var,
                from_=DIFFICULTY_MIN, to=DIFFICULTY_MAX,
                width=3, style="my.TSpinbox",
            ).grid(row=r, column=2, padx=2)

            spec_dot = ttk.Label(frm, text="●" if spec_var.get() else "○",
                                 style="S.TLabel", cursor="hand2")
            spec_var.trace_add("write",
                               lambda *_, d=spec_dot, v=spec_var: d.configure(
                                   text="●" if v.get() else "○"))
            spec_dot.bind("<Button-1>", lambda e, v=spec_var: v.set(not v.get()))
            spec_dot.grid(row=r, column=3, padx=(4, 0))

            ttk.Button(
                frm, text="▶", width=2,
                command=lambda idx=i: root.quick_roll(idx),
                style="S.TButton",
            ).grid(row=r, column=4, padx=(2, 0))

        ttk.Scale(
            frm, from_=5, to=0, orient=tk.VERTICAL,
            variable=root.quick_penalty, length=88,
            style="Vertical.TScale",
            command=lambda s: root.scaler(s, root.quick_penalty),
        ).grid(row=1, column=5, rowspan=4, padx=(6, 2), sticky="ns")

        frm.grid_columnconfigure(1, weight=1)

        locale.on_change(self._refresh_qr_values)
        self._refresh_qr_values()

    def _build_attr_cb_values(self) -> list[str]:
        values: list[str] = []
        for cat_name, cat_data in self.root.character.attributes.items():
            values.append(f"── {locale.t(f'sheet.attr_categories.{cat_name}')} ──")
            for name in cat_data:
                values.append(locale.translate_known("sheet.attr_names", name))
        return values

    def _build_abil_cb_values(self) -> list[str]:
        char = self.root.character
        values: list[str] = []
        seen: set[str] = set()

        for cat_name, cat_data in char.abilities.items():
            values.append(f"── {locale.t(f'sheet.ability_categories.{cat_name}')} ──")
            for name in cat_data:
                values.append(locale.translate_known("sheet.ability_names", name))
                seen.add(name)

        custom_names = []
        for cat_rows in char.custom_abilities.values():
            for row in cat_rows:
                n = row["name"].get().strip()
                if n and n not in seen:
                    custom_names.append(locale.translate_known("sheet.ability_names", n))
                    seen.add(n)
        if custom_names:
            values.append("── Custom ──")
            values.extend(custom_names)

        disc_names = [row["name"].get().strip() for row in char.disciplines if row["name"].get().strip()]
        if disc_names:
            values.append(f"── {locale.t('sheet.adv_columns.Disciplines')} ──")
            values.extend(disc_names)

        bg_names = [row["name"].get().strip() for row in char.backgrounds if row["name"].get().strip()]
        if bg_names:
            values.append(f"── {locale.t('sheet.adv_columns.Backgrounds')} ──")
            values.extend(bg_names)

        return values

    def _refresh_qr_values(self) -> None:
        root = self.root
        attr_vals = self._build_attr_cb_values()
        abil_vals = self._build_abil_cb_values()
        for (attr_var, abil_var, *_), attr_cb, abil_cb in zip(
            root.quick_rolls, self._qr_attr_cbs, self._qr_abil_cbs
        ):
            attr_cb.configure(values=attr_vals)
            abil_cb.configure(values=abil_vals)
            attr_var.set(locale.translate_known("sheet.attr_names", attr_var.get()))
            abil_var.set(locale.translate_known("sheet.ability_names", abil_var.get()))

    @frm(padding=2, style="flat.TFrame")
    def _frm_stats_row(self, frm: ttk.Frame) -> None:
        char = self.root.character
        stats = [
            self._frm_stat_label(frm, "stats.blood",    char.blood_value),
            self._frm_stat_label(frm, "stats.wounds",   char.wounds_display),
            self._frm_stat_label(frm, "stats.humanity", char.humanity_value),
            self._frm_stat_label(frm, "stats.will",     char.will_value),
        ]
        for col, w in enumerate(stats):
            w.grid(row=0, column=col, sticky="nsew")
            frm.grid_columnconfigure(col, weight=1)

    @frm(padding=2, style="flat.TFrame")
    def _frm_info_row(self, frm: ttk.Frame) -> None:
        self._frm_probability(frm).grid(row=0, column=0, sticky="nsew")
        self._frm_options(frm).grid(row=0, column=1, sticky="w")
        self._frm_roll_stats(frm).grid(row=0, column=2, sticky="nsew")
        frm.grid_columnconfigure(1, weight=1)

    @frm(padding=5, style="solid.TFrame")
    def _frm_probability(self, frm: ttk.Frame) -> None:
        from game.calculator import Calculator
        prob_var = StringVar(value="—")

        def _update(*_) -> None:
            root = self.root
            try:
                calc = Calculator(
                    dice_number=root.dice_number.get(),
                    difficulty=root.difficulty.get(),
                    success_needed=root.success_needed.get(),
                    auto_successes=root.auto_success.get(),
                    specialisation=root.specialisation.get(),
                )
                prob_var.set(f"{calc.get_probability():.1f}%")
            except Exception:
                prob_var.set("—")

        for var in (
            self.root.dice_number, self.root.difficulty,
            self.root.success_needed, self.root.auto_success,
            self.root.specialisation,
        ):
            var.trace_add("write", lambda *_: _update())
        _update()

        place_widgets([
            [self._tlabel(frm, "controls.chance", style="S.TLabel", anchor="center")],
            [ttk.Label(frm, textvariable=prob_var, style="M.TLabel", anchor="center", width=8)],
        ])

    @frm(padding=5, style="solid.TFrame")
    def _frm_roll_stats(self, frm: ttk.Frame) -> None:
        summary_var = StringVar(value="—")
        rates_var   = StringVar(value="")
        delta_var   = StringVar(value="")
        delta_lbl   = ttk.Label(frm, textvariable=delta_var, style="M.TLabel", anchor="center")

        def _update(_record=None) -> None:
            history = [r for r in self.root.roll_history if r.roll_type in ("NORMAL", "QUICK")]
            total = len(history)
            if total == 0:
                summary_var.set("—")
                rates_var.set("")
                delta_var.set("")
                return
            hits     = sum(1 for r in history if r.successes >= 1)
            actual   = hits / total * 100
            expected = sum(r.probability for r in history) / total
            delta    = actual - expected
            summary_var.set(f"{total} rolls · {hits} hits")
            rates_var.set(f"Exp: {expected:.1f}%  Got: {actual:.1f}%")
            sign = "+" if delta >= 0 else ""
            delta_var.set(f"{sign}{delta:.1f}%")
            delta_lbl.configure(
                foreground=theme.palette["delta_pos"] if delta >= 0 else theme.palette["delta_neg"]
            )

        self.root.on_roll(_update)

        place_widgets([
            [self._tlabel(frm, "stats.roll_stats", style="S.TLabel", anchor="center")],
            [ttk.Label(frm, textvariable=summary_var, style="S.TLabel", anchor="center", width=22)],
            [ttk.Label(frm, textvariable=rates_var,   style="S.TLabel", anchor="center", width=22)],
            [delta_lbl],
        ])

    @frm(padding=5)
    def _frm_options(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._frm_name(frm),
            self._frm_nav_buttons(frm),
        ]])

    @frm(padding=5)
    def _frm_name(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._tlabel(frm, "stats.character_name", anchor="e", style="M.TLabel")],
            [ttk.Entry(frm, textvariable=self.root.character.character_name, width=20,
                       style="my.TEntry")],
        ])

    @frm(padding=5)
    def _frm_nav_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._tbutton(frm, "controls.sheet", style="S.TButton",
                           command=self._open_character_sheet)],
        ])

    @frm(padding=8, style="solid.TFrame")
    def _frm_settings_tab(self, frm: ttk.Frame) -> None:
        root = self.root

        def _section(key: str) -> ttk.LabelFrame:
            lf = ttk.LabelFrame(frm, text=locale.t(key), padding=(8, 4))
            locale.on_change(lambda *_: lf.configure(text=locale.t(key)))
            lf.pack(fill="x", pady=(0, 6))
            lf.grid_columnconfigure(0, weight=1)
            return lf

        # ── Character ─────────────────────────────────────────────────────────
        char_lf = _section("controls.settings_character")
        self._tbutton(char_lf, "controls.load_character", style="S.TButton",
                      command=root.load_character_dialog).grid(
            row=0, column=0, sticky="ew", padx=(0, 3), pady=2)
        self._tbutton(char_lf, "chargen.btn_create", style="S.TButton",
                      command=self._open_chargen).grid(
            row=0, column=1, sticky="ew", padx=(3, 0), pady=2)
        char_lf.grid_columnconfigure(1, weight=1)

        # ── Session ───────────────────────────────────────────────────────────
        sess_lf = _section("controls.settings_session")
        self._tlabel(sess_lf, "controls.session_code", style="S.TLabel").grid(
            row=0, column=0, sticky="w", pady=2)
        ttk.Entry(sess_lf, textvariable=root.session_code,
                  width=12, style="my.TEntry").grid(row=0, column=1, sticky="ew", padx=(4, 4), pady=2)

        btn_var = tk.StringVar(value=locale.t("controls.join_session"))

        def _update_btn(*_) -> None:
            key = "controls.leave_session" if root.is_connected.get() else "controls.join_session"
            btn_var.set(locale.t(key))

        root.is_connected.trace_add("write", _update_btn)
        locale.on_change(_update_btn)

        def _on_click() -> None:
            if root.is_connected.get():
                root.leave_session()
            else:
                root.join_session()

        ttk.Button(sess_lf, textvariable=btn_var, command=_on_click,
                   style="S.TButton").grid(row=0, column=2, pady=2)
        sess_lf.grid_columnconfigure(1, weight=1)

        # ── Telegram ──────────────────────────────────────────────────────────
        tg_lf = _section("controls.settings_telegram")
        ttk.Button(tg_lf, textvariable=root.pooling_state,
                   command=root.start_bot_polling,
                   style="S.TButton").grid(row=0, column=0, sticky="ew", pady=2)
        self._dot_toggle(tg_lf, locale.t("controls.send_telegram"),
                         root.is_send_to_telegram,
                         locale_key="controls.send_telegram").grid(
            row=1, column=0, sticky="w", pady=2)

        # ── App ───────────────────────────────────────────────────────────────
        app_lf = _section("controls.settings_app")

        theme_var = tk.StringVar()

        def _upd_theme_btn(*_) -> None:
            key = "controls.dark_mode" if theme.mode == "light" else "controls.light_mode"
            theme_var.set(locale.t(key))

        _upd_theme_btn()
        locale.on_change(_upd_theme_btn)
        theme.on_change(_upd_theme_btn)
        ttk.Button(app_lf, textvariable=theme_var, style="S.TButton",
                   command=root.toggle_theme).grid(
            row=0, column=0, sticky="ew", padx=(0, 3), pady=2)

        lang_btn = ttk.Button(app_lf, text=locale.t("lang_btn"), style="S.TButton",
                              command=self._switch_language)
        locale.register(lang_btn, "lang_btn")
        lang_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=2)

        self._dot_toggle(app_lf, locale.t("controls.unskilled_penalty"),
                         root.default_skill_penalty,
                         locale_key="controls.unskilled_penalty").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=2)
        self._dot_toggle(app_lf, locale.t("controls.chargen_min_will"),
                         root.chargen_min_will,
                         locale_key="controls.chargen_min_will").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=2)
        app_lf.grid_columnconfigure(1, weight=1)

    @frm(padding=2, style="solid.TFrame")
    def _frm_stat_label(self, frm: ttk.Frame, title_key: str, var) -> None:
        place_widgets([
            [self._tlabel(frm, title_key, width=14, anchor="center", style="M.TLabel")],
            [ttk.Label(frm, textvariable=var, width=14, anchor="center", style="S.TLabel")],
        ])
