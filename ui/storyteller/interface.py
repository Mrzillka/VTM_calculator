from __future__ import annotations

import tkinter as tk
from tkinter import Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from lang import locale
from ui.base_interface import BaseInterface
from ui.theme import theme
from ui.constants import (
    AUTO_SUCCESS_MAX, DICE_MAX, DICE_MIN, DIFFICULTY_MAX, DIFFICULTY_MIN,
    SCALE_LENGTH, ST_HISTORY_HEIGHT, ST_HISTORY_WIDTH, SUCCESS_NEEDED_MAX,
)
from ui.storyteller.panels import NPCPanel, PCPanel
from ui.storyteller.constants import NO_ROLLER
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from ui.storyteller.root import Root


class Interface(BaseInterface):
    """Root widget for the Storyteller interface."""

    def __init__(self, root: "Root") -> None:
        super().__init__(root)
        self.root = root

        self._additional_widgets: list[Widget] = []
        self._roller_cb: ttk.Combobox | None = None

        self._pc_panel = PCPanel(self)
        self._npc_panel = NPCPanel(self, on_roster_change=self._refresh_roller_combobox)

        self._build()
        root.on_roll(self._append_roll_entry)

    def _build(self) -> None:
        place_widgets([[
            self._frm_controls_panel(),
            self._frm_history_panel(),
            self._pc_panel,
            self._npc_panel,
        ]])

    # ── Roller combobox ───────────────────────────────────────────────────────

    def _refresh_roller_combobox(self) -> None:
        if self._roller_cb is None:
            return
        names = [NO_ROLLER] + [
            e["char"].character_name.get() for e in self._npc_panel.get_npc_entries()
        ]
        self._roller_cb.configure(values=names)
        if self.root.active_roller.get() not in names:
            self.root.active_roller.set(NO_ROLLER)

    # ── Toggle handlers ───────────────────────────────────────────────────────

    def _toggle_additional_options(self) -> None:
        if self.root.additional_options.get():
            for col_idx, widget in enumerate(self._additional_widgets):
                widget.grid(column=col_idx, row=5)
                widget.update()
        else:
            for widget in self._additional_widgets:
                widget.grid_remove()

    def _switch_language(self) -> None:
        locale.switch()
        self.root.save_lang_pref()

    # ── Left panel ────────────────────────────────────────────────────────────

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
            ttk.Scale(frm, from_=DICE_MIN, to=DICE_MAX, length=SCALE_LENGTH,
                      variable=root.dice_number, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.dice_number)),
            ttk.Spinbox(frm, from_=DICE_MIN, to=50, textvariable=root.dice_number,
                        width=3, style="my.TSpinbox"),
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
            self._dot_toggle(frm, "∨", root.additional_options,
                             command=self._toggle_additional_options),
        ])

        roller_lbl = self._tlabel(frm, "controls.roller", style="M.TLabel", anchor="e", width=22)
        self._roller_cb = ttk.Combobox(
            frm,
            textvariable=root.active_roller,
            values=[NO_ROLLER],
            width=20,
            state="readonly",
        )
        self._roller_cb.grid(column=1, row=4, columnspan=2, sticky="w")
        roller_lbl.grid(column=0, row=4, sticky="e")
        self._refresh_roller_combobox()

        place_widgets(rows)

        self._additional_widgets = [
            self._tlabel(frm, "controls.success_needed",
                         width=16, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=1, to=SUCCESS_NEEDED_MAX, length=SCALE_LENGTH,
                      variable=root.success_needed, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.success_needed)),
            ttk.Spinbox(frm, from_=1, to=SUCCESS_NEEDED_MAX, textvariable=root.success_needed,
                        width=3, style="my.TSpinbox"),
        ]
        for col_idx, widget in enumerate(self._additional_widgets):
            widget.grid(column=col_idx, row=5)
            widget.update()
        if not root.additional_options.get():
            for widget in self._additional_widgets:
                widget.grid_remove()

    @frm(padding=5)
    def _frm_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._tbutton(frm, "controls.roll", style="L.TButton",
                          command=self.root.roll_and_calculate),
            self._tbutton(frm, "controls.initiative", style="M.TButton",
                          command=self.root.roll_initiative),
            self._tbutton(frm, "controls.damage_soak", style="M.TButton",
                          command=self.root.roll_damage_soak),
        ]])

    @frm(padding=2)
    def _frm_sidebar(self, frm: ttk.Frame) -> None:
        lang_btn = ttk.Button(frm, text=locale.t("lang_btn"), style="S.TButton",
                              command=self._switch_language)
        locale.register(lang_btn, "lang_btn")
        lang_btn.grid(row=0, column=0, padx=4)

        theme_var = tk.StringVar()

        def _upd_theme_btn(*_) -> None:
            key = "controls.dark_mode" if theme.mode == "light" else "controls.light_mode"
            theme_var.set(locale.t(key))

        _upd_theme_btn()
        locale.on_change(_upd_theme_btn)
        theme.on_change(_upd_theme_btn)

        theme_btn = ttk.Button(frm, textvariable=theme_var, style="S.TButton",
                               command=self.root.toggle_theme)
        theme_btn.grid(row=0, column=1, padx=4)

        # Session block
        new_btn = self._tbutton(frm, "controls.new_session", style="S.TButton",
                                command=self.root.new_session)
        new_btn.grid(row=1, column=0, columnspan=2, pady=(8, 2), sticky="ew")

        code_lbl = ttk.Label(frm, textvariable=self.root.session_topic,
                             style="S.TLabel", anchor="center")
        code_lbl.grid(row=2, column=0, sticky="ew")

        copy_btn = self._tbutton(frm, "controls.copy_code", style="S.TButton",
                                 command=self._copy_session_code)
        copy_btn.grid(row=2, column=1, padx=(4, 0))

    def _copy_session_code(self) -> None:
        """Copy the current session code to the system clipboard."""
        code = self.root.session_topic.get()
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)

    # ── Roll history panel ────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_history_panel(self, frm: ttk.Frame) -> None:
        lbl = ttk.Label(frm, text=locale.t("roll_history"), style="M.TLabel")
        lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        locale.register(lbl, "roll_history")
        self._build_scrollable_history(frm, width=ST_HISTORY_WIDTH, height=ST_HISTORY_HEIGHT)