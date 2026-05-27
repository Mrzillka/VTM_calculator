from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from lang import locale
from ui.base_interface import BaseInterface
from ui.theme import theme
from ui.constants import (
    AUTO_SUCCESS_MAX, DICE_MAX, DICE_MIN, DIFFICULTY_MAX, DIFFICULTY_MIN,
    SUCCESS_NEEDED_MAX,
)
from ui.storyteller.panels import NPCPanel, PCPanel
from ui.storyteller.constants import NO_ROLLER
from ui.utils import frm

if TYPE_CHECKING:
    from ui.storyteller.root import StorytellerRoot


class StorytellerInterface(BaseInterface):
    """Storyteller interface — toolbar + tabbed character panel + history."""

    def __init__(self, root: "StorytellerRoot") -> None:
        super().__init__(root)
        self.root = root
        self._roller_cb: ttk.Combobox | None = None
        self._pc_panel: PCPanel | None = None
        self._npc_panel: NPCPanel | None = None
        self._settings_win: tk.Toplevel | None = None
        self._build()
        root.on_roll(self._append_roll_entry)

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._frm_toolbar().grid(row=0, column=0, sticky="ew")
        self._frm_body().grid(row=1, column=0, sticky="nsew")
        self._refresh_roller_combobox()

    # ── Toolbar ───────────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_toolbar(self, frm: ttk.Frame) -> None:
        root = self.root

        self._roller_cb = ttk.Combobox(
            frm, textvariable=root.active_roller,
            values=[NO_ROLLER], width=18, state="readonly",
        )
        self._roller_cb.grid(row=0, column=0, padx=(0, 12))

        self._tlabel(frm, "controls.dice_short", style="S.TLabel").grid(
            row=0, column=1, padx=(0, 2))
        ttk.Spinbox(
            frm, from_=DICE_MIN, to=DICE_MAX,
            textvariable=root.dice_number, width=3, style="my.TSpinbox",
        ).grid(row=0, column=2, padx=(0, 8))

        self._tlabel(frm, "controls.diff_short", style="S.TLabel").grid(
            row=0, column=3, padx=(0, 2))
        ttk.Spinbox(
            frm, from_=DIFFICULTY_MIN, to=DIFFICULTY_MAX,
            textvariable=root.difficulty, width=3, style="my.TSpinbox",
        ).grid(row=0, column=4, padx=(0, 8))

        self._dot_toggle(
            frm, locale.t("controls.specialisation"),
            root.specialisation,
            locale_key="controls.specialisation",
        ).grid(row=0, column=5, padx=(0, 12))

        self._tbutton(frm, "controls.roll", style="L.TButton",
                      command=root.roll_and_calculate).grid(row=0, column=6, padx=(0, 4))
        self._tbutton(frm, "controls.initiative", style="M.TButton",
                      command=root.roll_initiative).grid(row=0, column=7, padx=(0, 4))
        self._tbutton(frm, "controls.damage_soak", style="M.TButton",
                      command=root.roll_damage_soak).grid(row=0, column=8, padx=(0, 4))

        ttk.Button(frm, text="⚙", style="S.TButton",
                   command=self._open_settings_panel).grid(row=0, column=9)

    # ── Body ──────────────────────────────────────────────────────────────────

    @frm(padding=4)
    def _frm_body(self, frm: ttk.Frame) -> None:
        frm.grid_rowconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self._frm_char_panel(frm).grid(row=0, column=0, sticky="ns", padx=(0, 4))
        self._frm_history_panel(frm).grid(row=0, column=1, sticky="nsew")

    @frm(padding=0, style="solid.TFrame")
    def _frm_char_panel(self, outer: ttk.Frame) -> None:
        nb = ttk.Notebook(outer)
        nb.pack(fill="both", expand=True)

        self._pc_panel = PCPanel(nb)
        self._npc_panel = NPCPanel(
            nb,
            on_roster_change=self._refresh_roller_combobox,
            on_set_roller=lambda name: self.root.active_roller.set(name),
            on_quick_roll=lambda rname, pool, no_botch: self.root.npc_quick_roll(rname, pool, no_botch),
        )
        nb.add(self._pc_panel, text=locale.t("panels.players"))
        nb.add(self._npc_panel, text=locale.t("panels.npcs"))

        def _update_tab_labels() -> None:
            nb.tab(0, text=locale.t("panels.players"))
            nb.tab(1, text=locale.t("panels.npcs"))

        locale.on_change(_update_tab_labels)

    @frm(padding=4, style="solid.TFrame")
    def _frm_history_panel(self, frm: ttk.Frame) -> None:
        lbl = ttk.Label(frm, text=locale.t("roll_history"), style="M.TLabel")
        lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        locale.register(lbl, "roll_history")
        self._build_scrollable_history(frm, width=400, height=200)

    # ── Roller combobox ───────────────────────────────────────────────────────

    def _refresh_roller_combobox(self) -> None:
        if self._roller_cb is None or self._npc_panel is None:
            return
        names = [NO_ROLLER] + [
            e["char"].character_name.get() for e in self._npc_panel.get_npc_entries()
        ]
        self._roller_cb.configure(values=names)
        if self.root.active_roller.get() not in names:
            self.root.active_roller.set(NO_ROLLER)

    # ── Settings panel ────────────────────────────────────────────────────────

    def _open_settings_panel(self) -> None:
        if self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.lift()
            return
        win = tk.Toplevel(self)
        win.title(locale.t("controls.settings"))
        win.resizable(False, False)
        self._settings_win = win
        self._build_settings_toplevel(win)

    def _build_settings_toplevel(self, win: tk.Toplevel) -> None:
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)
        frm.grid_columnconfigure(1, weight=1)

        # Advanced roll options
        self._tlabel(frm, "controls.auto_success", style="S.TLabel").grid(
            row=0, column=0, sticky="e", pady=3)
        ttk.Spinbox(frm, from_=0, to=AUTO_SUCCESS_MAX,
                    textvariable=self.root.auto_success,
                    width=4, style="my.TSpinbox").grid(
            row=0, column=1, sticky="w", padx=(6, 0))

        self._tlabel(frm, "controls.success_needed", style="S.TLabel").grid(
            row=1, column=0, sticky="e", pady=3)
        ttk.Spinbox(frm, from_=1, to=SUCCESS_NEEDED_MAX,
                    textvariable=self.root.success_needed,
                    width=4, style="my.TSpinbox").grid(
            row=1, column=1, sticky="w", padx=(6, 0))

        ttk.Separator(frm, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=8)

        # Language button
        lang_btn = ttk.Button(frm, text=locale.t("lang_btn"), style="S.TButton",
                              command=self._switch_language)
        locale.register(lang_btn, "lang_btn")
        lang_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=3)

        # Theme button
        theme_var = tk.StringVar()

        def _upd_theme(*_) -> None:
            if not win.winfo_exists():
                return
            key = "controls.dark_mode" if theme.mode == "light" else "controls.light_mode"
            theme_var.set(locale.t(key))

        _upd_theme()
        locale.on_change(_upd_theme)
        theme.on_change(_upd_theme)

        ttk.Button(frm, textvariable=theme_var, style="S.TButton",
                   command=self.root.toggle_theme).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=3)

        ttk.Separator(frm, orient="horizontal").grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=8)

        # Session block
        self._tbutton(frm, "controls.new_session", style="S.TButton",
                      command=self.root.new_session).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        ttk.Label(frm, textvariable=self.root.session_topic,
                  style="S.TLabel", anchor="center").grid(
            row=7, column=0, sticky="ew")

        self._tbutton(frm, "controls.copy_code", style="S.TButton",
                      command=self._copy_session_code).grid(
            row=7, column=1, padx=(6, 0))

    # ── Locale / helpers ──────────────────────────────────────────────────────

    def _switch_language(self) -> None:
        locale.switch()
        self.root.save_lang_pref()

    def _copy_session_code(self) -> None:
        code = self.root.session_topic.get()
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)
