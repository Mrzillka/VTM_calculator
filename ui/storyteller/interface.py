from __future__ import annotations

import tkinter as tk
from tkinter import Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from lang import locale
from ui.base_interface import BaseInterface
from ui.storyteller.panels import NPCPanel, PCPanel
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from ui.storyteller.root import Root


class Interface(BaseInterface):
    """Root widget for the Storyteller interface."""

    def __init__(self, root: "Root") -> None:
        super().__init__(root)
        self.root = root

        self._additional_row: list[Widget] = []
        self._initiative_var = tk.StringVar(value="")

        self._build()
        root.on_roll(self._append_roll_entry)

    def _build(self) -> None:
        pc_panel = PCPanel(self)
        npc_panel = NPCPanel(self)
        place_widgets([[
            self._frm_controls_panel(),
            self._frm_history_panel(),
            pc_panel,
            npc_panel,
        ]])

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

    # ── Roll history panel ────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_history_panel(self, frm: ttk.Frame) -> None:
        ttk.Label(frm, text="⚄  Roll History", style="M.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self._build_scrollable_history(frm, width=380, height=420)