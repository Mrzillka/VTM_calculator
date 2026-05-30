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

_XP_DOT_COLOR: str = "#C8A84B"
_CHARGEN_HEADER_KEYS: frozenset[str] = frozenset({"Name", "Nature", "Demeanor", "Clan", "Generation"})


class CharsheetInterface(ttk.Frame, _AttributesMixin, _AdvantagesMixin, _TrackersMixin, LocaleWidgetsMixin):
    """Main content frame for the character sheet."""

    def __init__(self, parent: ttk.Frame, root) -> None:
        super().__init__(parent)
        self.root = root
        self.character: Character = root.character

        self._lockable: list[ttk.Widget] = []
        self._permanent_locked: list[ttk.Widget] = []
        self._spec_updaters: list[Callable] = []
        self._willpower_labels: list[ttk.Label] = []
        self._humanity_dot_labels: list[ttk.Label] = []
        self._sheet_blood_labels: list[list[ttk.Label]] = []
        self._wound_name_labels: list[ttk.Label] = []
        self._merit_total_lbl: ttk.Label | None = None
        self._flaw_total_lbl: ttk.Label | None = None
        self._net_lbl: ttk.Label | None = None
        self._xp_label: ttk.Label | None = None
        self._xp_remaining_label: ttk.Label | None = None
        self._merit_sum: int = 0
        self._flaw_sum: int = 0
        self._translating: bool = False

        self._build()
        self._apply_permanent_locks()

        char = self.character
        char.willpower_max.trace_add("write", lambda *_: self._refresh_xp())
        char.humanity_value.trace_add("write", lambda *_: self._refresh_xp())
        char.xp_total.trace_add("write", lambda *_: self._update_xp_label())
        self._refresh_xp()

        self._sync_virtue_names()
        locale.on_change(self._sync_virtue_names)
        locale.on_change(self._refresh_mf_totals)
        locale.on_change(self._refresh_wound_names)
        locale.on_change(self._refresh_translations)
        locale.on_change(self._update_xp_label)

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

        combo = self._frm_combo_disciplines()
        rows.append([self._collapsible_header("sheet.sections.combo_disciplines", combo)])
        rows.append([combo])

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

    def _apply_permanent_locks(self) -> None:
        for widget in self._permanent_locked:
            try:
                widget.configure(state="disabled")
            except tk.TclError:
                pass

    # ── XP tracker ────────────────────────────────────────────────────────────

    def _update_xp_label(self) -> None:
        if self._xp_label is None:
            return
        try:
            if not self._xp_label.winfo_exists():
                return
        except tk.TclError:
            return
        n = self.root.xp_spent.get()
        if n > 0:
            self._xp_label.configure(text=locale.t("sheet.xp_label").format(n=n))
        else:
            self._xp_label.configure(text="")

        if self._xp_remaining_label is not None:
            try:
                if not self._xp_remaining_label.winfo_exists():
                    return
            except tk.TclError:
                return
            remaining = self.character.xp_total.get() - n
            self._xp_remaining_label.configure(
                text=locale.t("sheet.xp_remaining").format(n=remaining)
            )

    def _refresh_xp(self) -> None:
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return

        snap = self.character.chargen_snapshot
        if snap is None:
            self.root.xp_spent.set(0)
            self._update_xp_label()
            return

        from game.xp_rules import xp_for_increase
        from game.chargen import CLAN_DISCIPLINES

        char = self.character
        inclan_discs = set(CLAN_DISCIPLINES.get(char.clan.get(), ()))
        total = 0

        for category, attrs in char.attributes.items():
            snap_cat = snap.get("attributes", {}).get(category, {})
            for attr_name, values in attrs.items():
                baseline = snap_cat.get(attr_name, 0)
                current = sum(v.get() for v in values["vars"])
                total += xp_for_increase("attribute", baseline, current)

        for category, abilities in char.abilities.items():
            snap_cat = snap.get("abilities", {}).get(category, {})
            for ability_name, values in abilities.items():
                baseline = snap_cat.get(ability_name, 0)
                current = sum(v.get() for v in values["vars"])
                total += xp_for_increase("ability", baseline, current)

        snap_custom = snap.get("custom_abilities", {})
        for category, entries in char.custom_abilities.items():
            snap_entries = snap_custom.get(category, [])
            for i, entry in enumerate(entries):
                baseline = snap_entries[i]["dots"] if i < len(snap_entries) else 0
                current = sum(v.get() for v in entry["vars"])
                total += xp_for_increase("secondary_ability", baseline, current)

        snap_discs = snap.get("advantages", {}).get("disciplines", [])
        for i, entry in enumerate(char.disciplines):
            baseline = snap_discs[i]["dots"] if i < len(snap_discs) else 0
            current = sum(v.get() for v in entry["vars"])
            disc_en = locale.reverse_lookup_en("sheet.disciplines", entry["name"].get())
            is_inclan = disc_en in inclan_discs or entry["name"].get() in inclan_discs
            total += xp_for_increase("discipline", baseline, current, is_inclan=is_inclan)

        snap_bgs = snap.get("advantages", {}).get("backgrounds", [])
        for i, entry in enumerate(char.backgrounds):
            baseline = snap_bgs[i]["dots"] if i < len(snap_bgs) else 0
            current = sum(v.get() for v in entry["vars"])
            total += xp_for_increase("background", baseline, current)

        snap_virtues = snap.get("advantages", {}).get("virtues", [])
        for i, entry in enumerate(char.virtues):
            baseline = snap_virtues[i] if i < len(snap_virtues) else 0
            current = sum(v.get() for v in entry["vars"])
            total += xp_for_increase("virtue", baseline, current)

        snap_trackers = snap.get("trackers", {})
        wp_baseline = snap_trackers.get("willpower_max", 0)
        total += xp_for_increase("willpower", wp_baseline, char.willpower_max.get())

        hum_baseline = snap_trackers.get("humanity_value", 0)
        total += xp_for_increase("humanity", hum_baseline, char.humanity_value.get())

        from game.discipline_rules import COMBO_DISCIPLINES as _COMBOS
        snap_combos_en = {
            locale.reverse_lookup_en("sheet.combo_disciplines", name)
            for name in snap.get("advantages", {}).get("combo_disciplines", [])
            if name
        }
        combo_by_en = {c.name: c for c in _COMBOS}
        for sv in char.combo_disciplines:
            name_en = locale.reverse_lookup_en("sheet.combo_disciplines", sv.get())
            if name_en and name_en not in snap_combos_en:
                combo = combo_by_en.get(name_en)
                if combo:
                    total += combo.xp_cost

        self.root.xp_spent.set(total)
        self._update_xp_label()

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
        has_snapshot = self.character.chargen_snapshot is not None
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
            if has_snapshot and field_key in _CHARGEN_HEADER_KEYS:
                self._permanent_locked.append(widget)
            else:
                self._lockable.append(widget)
            rows.append([lbl, widget])
        place_widgets(rows)

    # ── Dots ─────────────────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_dots_with_boost(
        self, frm: ttk.Frame, variables: list[BooleanVar], boost_var: IntVar,
        baseline: int | None = None,
    ) -> None:
        """Like _frm_dots but appends green boost-dot slots after the base dots."""
        row: list[ttk.Label] = []
        for idx, var in enumerate(variables):
            filled = var.get()
            fg = _XP_DOT_COLOR if (filled and baseline is not None and idx >= baseline) else ""
            lbl = ttk.Label(frm, text="●" if filled else "○",
                            foreground=fg,
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write", self._make_dot_trace(lbl, var, idx, baseline))
            var.trace_add("write", lambda *_: self._refresh_xp())
            lbl.bind(
                "<Button-1>",
                lambda e, i=idx, v=variables, b=baseline: (
                    None if self.root.locked.get() else self._set_dots(v, i, b or 0)
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
    def _frm_dots(self, frm: ttk.Frame, variables: list[BooleanVar], baseline: int | None = None) -> None:
        row: list[ttk.Label] = []
        for idx, var in enumerate(variables):
            filled = var.get()
            fg = _XP_DOT_COLOR if (filled and baseline is not None and idx >= baseline) else ""
            lbl = ttk.Label(frm, text="●" if filled else "○",
                            foreground=fg,
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write", self._make_dot_trace(lbl, var, idx, baseline))
            var.trace_add("write", lambda *_: self._refresh_xp())
            lbl.bind(
                "<Button-1>",
                lambda e, i=idx, v=variables, b=baseline: (
                    None if self.root.locked.get() else self._set_dots(v, i, b or 0)
                ),
            )
            row.append(lbl)
            if idx == 4:
                row.append(ttk.Label(frm, text="·", style="sheet.Sep.TLabel"))
        place_widgets([row])

    @staticmethod
    def _make_dot_trace(
        label: ttk.Label, var: BooleanVar, idx: int = 0, baseline: int | None = None
    ) -> Callable:
        """Return a write-trace callback for a dot label, guarded against widget destruction.

        Pass baseline (int) to enable XP-dot amber coloring for dots at idx >= baseline.
        Omit baseline (or pass None) for tracker dots that need no XP coloring.
        """
        def _cb(*_) -> None:
            try:
                if label.winfo_exists():
                    if baseline is None:
                        # Tracker dots: preserve externally managed foreground (e.g. disabled_fg)
                        label.configure(text="●" if var.get() else "○")
                    elif var.get():
                        fg = _XP_DOT_COLOR if idx >= baseline else ""
                        label.configure(text="●", foreground=fg)
                    else:
                        label.configure(text="○", foreground="")
            except tk.TclError:
                pass
        return _cb

    @staticmethod
    def _set_dots(variables: list[BooleanVar], clicked: int, baseline: int = 0) -> None:
        filled = sum(v.get() for v in variables)
        threshold = clicked if filled == clicked + 1 else clicked + 1
        threshold = max(threshold, baseline)  # chargen dots are the permanent minimum
        for i, var in enumerate(variables):
            var.set(i < threshold)
