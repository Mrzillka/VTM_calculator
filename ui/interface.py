from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, StringVar, Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from config import WOUND_LEVELS
from lang import locale
from ui.base_interface import BaseInterface
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from ui.root import Root


class Interface(BaseInterface):
    """Root widget of the main application interface."""

    def __init__(self, root: "Root") -> None:
        super().__init__(root)
        self.root = root

        self._trackers_frame: ttk.Frame | None = None
        self._additional_row: list[Widget] = []
        self._sheet_window = None
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
        if self._sheet_window is not None and self._sheet_window.winfo_exists():
            self._sheet_window.lift()
            self._sheet_window.focus_force()
            return
        from ui.charsheet.root import Root as CharacterSheet
        self._sheet_window = CharacterSheet(
            character=self.root.character,
            send_sheet_callback=self.root.send_sheet_to_server,
        )

    def _switch_language(self) -> None:
        locale.switch()
        self.root.save_to_file()

    # ── Center block ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_center(self, frm: ttk.Frame) -> None:
        self._trackers_frame = self._frm_trackers(frm)
        place_widgets([[
            self._frm_main(frm),
            self._frm_history(frm),
            self._frm_sidebar(frm),
            self._trackers_frame,
        ]])
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

        self._additional_row = [
            self._tlabel(frm, "controls.success_needed", width=16, style="M.TLabel", anchor="e"),
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
            self._tbutton(frm, "controls.damage_soak", style="M.TButton",
                          command=self.root.roll_damage_soak),
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
            [self._tbutton(frm, "controls.load_character", style="S.TButton",
                           command=self.root.load_character_dialog)],
            [lang_btn],
        ])

    # ── Roll history ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_history(self, frm: ttk.Frame) -> None:
        lbl = ttk.Label(frm, text=locale.t("roll_history"), style="M.TLabel")
        lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        locale.register(lbl, "roll_history")
        self._build_scrollable_history(frm, width=300, height=340)

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
            [self._frm_physical_attributes(frm)],
            [self._frm_humanity(frm)],
            [self._frm_will(frm)],
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
            [self._frm_max_blood(frm)],
            [per_turn_frm],
        ])

    @frm(padding=5)
    def _frm_blood_cells(self, frm: ttk.Frame) -> None:
        self._blood_cells = []
        char = self.root.character

        for i in range(5):
            row_labels: list[ttk.Label] = []
            for j in range(10):
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
                frm, from_=1, to=50,
                textvariable=self.root.character.blood_max_value,
                command=self._disable_blood_cells,
                width=3, style="my.TSpinbox",
            ),
        ]])

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
            for i in range(10)
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
            self._frm_session(frm),
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
        dex_lbl  = ttk.Label(frm, textvariable=char.dex_value,  width=3, style="S.TLabel", anchor="e")
        wits_lbl = ttk.Label(frm, textvariable=char.wits_value, width=3, style="S.TLabel", anchor="e")
        place_widgets([
            [self._tlabel(frm, "stats.dex",  width=5, anchor="e", style="S.TLabel"), dex_lbl],
            [self._tlabel(frm, "stats.wits", width=5, anchor="e", style="S.TLabel"), wits_lbl],
        ])

    @frm(padding=5)
    def _frm_action_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Button(frm, textvariable=self.root.pooling_state,
                        command=self.root.start_bot_polling, style="S.TButton")],
            [self._tbutton(frm, "controls.save",
                           command=self.root.save_to_file, style="S.TButton")],
        ])

    @frm(padding=5)
    def _frm_session(self, frm: ttk.Frame) -> None:
        """Session code field + Join/Leave button."""
        root = self.root

        self._tlabel(frm, "controls.session_code",
                     style="S.TLabel", anchor="e").grid(row=0, column=0, sticky="e")
        ttk.Entry(frm, textvariable=root.session_code,
                  width=16, style="my.TEntry").grid(row=0, column=1, padx=(4, 0))

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

        ttk.Button(frm, textvariable=btn_var, command=_on_click,
                   style="S.TButton").grid(row=1, column=0, columnspan=2, pady=(4, 0))

    @frm(padding=2, style="solid.TFrame")
    def _frm_stat_label(self, frm: ttk.Frame, title_key: str, var) -> None:
        place_widgets([
            [self._tlabel(frm, title_key, width=14, anchor="center", style="M.TLabel")],
            [ttk.Label(frm, textvariable=var, width=14, anchor="center", style="S.TLabel")],
        ])