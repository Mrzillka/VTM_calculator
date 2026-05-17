from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, IntVar, StringVar
from tkinter import ttk
from typing import Callable

from game.character import Character
from lang import locale
from ui.base_interface import LocaleWidgetsMixin
from ui.theme import theme
from ui.charsheet._section_mixins import _AttributesMixin, _AdvantagesMixin, _TrackersMixin
from ui.utils import frm, place_widgets


class Interface(ttk.Frame, _AttributesMixin, _AdvantagesMixin, _TrackersMixin, LocaleWidgetsMixin):
    """Main content frame for the character sheet."""

    def __init__(self, parent: ttk.Frame, root) -> None:
        super().__init__(parent)
        self.root = root
        self.character: Character = root.character

        self._lockable: list[ttk.Widget] = []
        self._spec_updaters: list[Callable] = []
        self._willpower_labels: list[ttk.Label] = []
        self._humanity_dot_labels: list[ttk.Label] = []
        self._sheet_blood_labels: list[list[ttk.Label]] = []
        self._wound_name_labels: list[ttk.Label] = []
        self._merit_total_lbl: ttk.Label | None = None
        self._flaw_total_lbl: ttk.Label | None = None
        self._net_lbl: ttk.Label | None = None
        self._merit_sum: int = 0
        self._flaw_sum: int = 0
        self._translating: bool = False

        self._build()

        self._sync_virtue_names()
        locale.on_change(self._sync_virtue_names)
        locale.on_change(self._refresh_mf_totals)
        locale.on_change(self._refresh_wound_names)
        locale.on_change(self._refresh_translations)

    # ── Locale helpers ────────────────────────────────────────────────────────

    def _tcheckbutton(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Checkbutton:
        cb = ttk.Checkbutton(parent, text=locale.t(key), **kwargs)
        locale.register(cb, key)
        return cb

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        sections = [
            ("sheet.sections.attributes", self._frm_attributes()),
            ("sheet.sections.abilities",  self._frm_abilities()),
            ("sheet.sections.advantages", self._frm_advantages()),
        ]
        rows: list[list] = [
            [self._frm_toolbar()],
            [self._tlabel(self, "sheet.title", style="sheet.title.TLabel")],
            [self._frm_header()],
        ]
        for title_key, content in sections:
            rows.append([self._collapsible_header(title_key, content)])
            rows.append([content])

        bottom = self._frm_bottom()
        rows.append([self._collapsible_header("sheet.sections.merits_flaws", bottom)])
        rows.append([bottom])
        place_widgets(rows)

    # ── Toolbar ───────────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_toolbar(self, frm: ttk.Frame) -> None:
        save_btn = self._tbutton(frm, "sheet.save", style="sheet.save.TButton",
                                 command=self.root.save)
        lock_cb = self._tcheckbutton(
            frm, "sheet.lock",
            variable=self.root.locked,
            style="sheet.TCheckbutton",
            command=self._apply_lock,
        )
        save_btn.grid(row=0, column=0, sticky="w", padx=(0, 8))
        lock_cb.grid(row=0, column=1, sticky="w")

        if self.root._send_sheet_callback is not None:
            send_btn = self._tbutton(frm, "sheet.send_sheet", style="sheet.save.TButton",
                                     command=self.root.send_sheet)
            send_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))

    # ── Lock ──────────────────────────────────────────────────────────────────

    def _apply_lock(self) -> None:
        locked = self.root.locked.get()
        state = "disabled" if locked else "normal"
        for widget in self._lockable:
            widget.configure(state=state)
        if not locked:
            for refresh in self._spec_updaters:
                refresh()

    def _collapsible_header(self, title_key: str, content: ttk.Frame) -> ttk.Label:
        visible = BooleanVar(value=True)
        lbl = ttk.Label(self, style="sheet.L.TLabel", cursor="hand2")

        def _set_text() -> None:
            arrow = "▼" if visible.get() else "►"
            lbl.configure(text=f"{arrow}  {locale.t(title_key)}")

        def _toggle(e=None) -> None:
            visible.set(not visible.get())
            _set_text()
            if visible.get():
                content.grid()
            else:
                content.grid_remove()

        _set_text()
        lbl.bind("<Button-1>", _toggle)
        locale.on_change(_set_text)
        return lbl

    # ── Header ────────────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_header(self, frm: ttk.Frame) -> None:
        groups = [
            [("Name",       self.character.character_name),
             ("Player",     self.character.player),
             ("Chronicle",  self.character.chronicle)],
            [("Nature",     self.character.nature),
             ("Demeanor",   self.character.demeanor),
             ("Clan",       self.character.clan)],
            [("Generation", self.character.generation),
             ("Heaven",     self.character.heaven),
             ("Concept",    self.character.concept)],
        ]
        place_widgets([[self._frm_field_group(frm, g) for g in groups]])

    _GENERATION_VALUES: tuple[str, ...] = tuple(f"{n}th" for n in range(4, 16))

    @frm(padding=5)
    def _frm_field_group(self, frm: ttk.Frame, fields: list[tuple[str, StringVar]]) -> None:
        rows = []
        for field_key, var in fields:
            lbl = self._tlabel(frm, f"sheet.header.{field_key}",
                               width=10, anchor="e", style="sheet.S.TLabel")
            if field_key == "Generation":
                widget = ttk.Spinbox(
                    frm, values=self._GENERATION_VALUES,
                    textvariable=var, width=6, state="readonly",
                    style="sheet.TSpinbox",
                )
            else:
                widget = ttk.Entry(frm, textvariable=var, width=20, style="sheet.TEntry")
            self._lockable.append(widget)
            rows.append([lbl, widget])
        place_widgets(rows)

    # ── Dots ─────────────────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_dots_with_boost(
        self, frm: ttk.Frame, variables: list[BooleanVar], boost_var: IntVar
    ) -> None:
        """Like _frm_dots but appends green boost-dot slots after the base dots."""
        row: list[ttk.Label] = []
        for idx, var in enumerate(variables):
            lbl = ttk.Label(frm, text="●" if var.get() else "○",
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write", self._make_dot_trace(lbl, var))
            lbl.bind(
                "<Button-1>",
                lambda e, i=idx, v=variables: (
                    None if self.root.locked.get() else self._set_dots(v, i)
                ),
            )
            row.append(lbl)
            if idx == 4:
                row.append(ttk.Label(frm, text="·", style="sheet.Sep.TLabel"))

        boost_dots: list[ttk.Label] = []
        for _ in range(4):
            lbl = ttk.Label(frm, text="○", style="sheet.Dot.TLabel",
                            foreground=theme.palette["boost_dot"])
            boost_dots.append(lbl)
            row.append(lbl)

        place_widgets([row])

        def _refresh_boost(*_) -> None:
            if not boost_dots:
                return
            try:
                if not boost_dots[0].winfo_exists():
                    return
            except tk.TclError:
                return
            boost = boost_var.get()
            for i, lbl in enumerate(boost_dots):
                lbl.configure(text="●" if i < boost else "○")

        def _upd_boost_colors() -> None:
            try:
                if boost_dots and boost_dots[0].winfo_exists():
                    for lbl in boost_dots:
                        lbl.configure(foreground=theme.palette["boost_dot"])
            except tk.TclError:
                pass

        boost_var.trace_add("write", _refresh_boost)
        theme.on_change(_upd_boost_colors)
        _refresh_boost()

    @frm(padding=0)
    def _frm_dots(self, frm: ttk.Frame, variables: list[BooleanVar]) -> None:
        row: list[ttk.Label] = []
        for idx, var in enumerate(variables):
            lbl = ttk.Label(frm, text="●" if var.get() else "○",
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write", self._make_dot_trace(lbl, var))
            lbl.bind(
                "<Button-1>",
                lambda e, i=idx, v=variables: (
                    None if self.root.locked.get() else self._set_dots(v, i)
                ),
            )
            row.append(lbl)
            if idx == 4:
                row.append(ttk.Label(frm, text="·", style="sheet.Sep.TLabel"))
        place_widgets([row])

    @staticmethod
    def _make_dot_trace(label: ttk.Label, var: BooleanVar) -> Callable:
        """Return a write-trace callback for a dot label, guarded against widget destruction."""
        def _cb(*_) -> None:
            try:
                if label.winfo_exists():
                    label.configure(text="●" if var.get() else "○")
            except tk.TclError:
                pass
        return _cb

    @staticmethod
    def _set_dots(variables: list[BooleanVar], clicked: int) -> None:
        filled = sum(v.get() for v in variables)
        threshold = clicked if filled == clicked + 1 else clicked + 1
        for i, var in enumerate(variables):
            var.set(i < threshold)
