from __future__ import annotations

from tkinter import BooleanVar, IntVar, StringVar
from tkinter import ttk
from typing import Callable

from config import DISCIPLINE_PATHS, FLAWS, MERITS, WOUND_LEVELS
from game.character import Character
from lang import locale
from ui.utils import frm, place_widgets

_VIRTUE_COLOR = "crimson"
_DISABLED_COLOR = "gray"


class Interface(ttk.Frame):
    """Main content frame for the character sheet."""

    def __init__(self, parent: ttk.Frame, root) -> None:
        super().__init__(parent)
        self.root = root
        self.character: Character = root.character

        # Editable widgets toggled by the lock checkbox (Entry, Spinbox, Combobox).
        self._lockable: list[ttk.Widget] = []

        # Callbacks that restore spec-entry enabled state after unlock.
        self._spec_refreshers: list[Callable] = []

        # Cached label lists for virtue-aware trackers
        self._wp_labels: list[ttk.Label] = []
        self._humanity_labels: list[ttk.Label] = []
        self._sheet_blood_labels: list[list[ttk.Label]] = []

        # Wound level name labels — updated on locale change
        self._wound_name_labels: list[ttk.Label] = []

        # Merit / flaw total labels — updated on locale change and value change
        self._merit_total_lbl: ttk.Label | None = None
        self._flaw_total_lbl: ttk.Label | None = None
        self._net_lbl: ttk.Label | None = None
        self._merit_sum: int = 0
        self._flaw_sum: int = 0

        # Guard that prevents _bind_disc_path traces from clearing path_var
        # while _refresh_translations is updating values programmatically.
        self._translating: bool = False

        self._build()

        self._sync_virtue_names()
        locale.on_change(self._sync_virtue_names)
        locale.on_change(self._refresh_mf_totals)
        locale.on_change(self._refresh_wound_names)
        # Must be registered last so combobox value lists are already updated
        # before we translate the selected values.
        locale.on_change(self._refresh_translations)

    # ── Locale helpers ────────────────────────────────────────────────────────

    def _tlabel(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Label:
        """Create a ttk.Label bound to a locale key; reconfigures on language switch."""
        lbl = ttk.Label(parent, text=locale.t(key), **kwargs)
        locale.register(lbl, key)
        return lbl

    def _tbutton(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Button:
        """Create a ttk.Button bound to a locale key; reconfigures on language switch."""
        btn = ttk.Button(parent, text=locale.t(key), **kwargs)
        locale.register(btn, key)
        return btn

    def _tcheckbutton(self, parent: ttk.Frame, key: str, **kwargs) -> ttk.Checkbutton:
        """Create a ttk.Checkbutton bound to a locale key; reconfigures on language switch."""
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

    # ── Lock ──────────────────────────────────────────────────────────────────

    def _apply_lock(self) -> None:
        """Disable or restore all lockable widgets based on the locked flag."""
        locked = self.root.locked.get()
        state = "disabled" if locked else "normal"
        for widget in self._lockable:
            widget.configure(state=state)
        if not locked:
            for refresh in self._spec_refreshers:
                refresh()

    def _collapsible_header(self, title_key: str, content: ttk.Frame) -> ttk.Label:
        """Return a clickable label that toggles visibility of *content*."""
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

    # ── Header ───────────────────────────────────────────────────────────────

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

    @frm(padding=5)
    def _frm_field_group(self, frm: ttk.Frame, fields: list[tuple[str, StringVar]]) -> None:
        rows = []
        for field_key, var in fields:
            lbl = self._tlabel(frm, f"sheet.header.{field_key}",
                               width=10, anchor="e", style="sheet.S.TLabel")
            entry = ttk.Entry(frm, textvariable=var, width=20, style="sheet.TEntry")
            self._lockable.append(entry)
            rows.append([lbl, entry])
        place_widgets(rows)

    # ── Attributes & Abilities ────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_attributes(self, frm: ttk.Frame) -> None:
        self._place_stat_columns(frm, self.character.attributes, "sheet.attr_categories",
                                 "sheet.attr_names")

    @frm(padding=5)
    def _frm_abilities(self, frm: ttk.Frame) -> None:
        self._place_stat_columns(frm, self.character.abilities, "sheet.ability_categories",
                                 "sheet.ability_names")

    def _place_stat_columns(
        self,
        parent: ttk.Frame,
        categories: dict,
        cat_prefix: str,
        name_prefix: str,
    ) -> None:
        headers = [
            self._tlabel(parent, f"{cat_prefix}.{name}", style="sheet.M.TLabel")
            for name in categories
        ]
        contents = [
            self._frm_stat_lines(parent, data, name_prefix)
            for data in categories.values()
        ]
        place_widgets([headers, contents])
        for col in range(len(categories)):
            parent.grid_columnconfigure(col, pad=14)

    @frm(padding=0)
    def _frm_stat_lines(
        self,
        frm: ttk.Frame,
        data: dict[str, dict[str, StringVar | list[BooleanVar]]],
        name_prefix: str,
    ) -> None:
        place_widgets([
            [self._frm_line(frm, label, name_prefix, values["vars"], values["spec"])]
            for label, values in data.items()
        ])

    # ── Advantages ────────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_advantages(self, frm: ttk.Frame) -> None:
        headers = [
            self._tlabel(frm, f"sheet.adv_columns.{t}", style="sheet.M.TLabel")
            for t in ("Backgrounds", "Disciplines", "Virtues")
        ]
        cols = [
            self._frm_adv_backgrounds(frm),
            self._frm_adv_disciplines(frm),
            self._frm_adv_virtues(frm),
        ]
        place_widgets([headers, cols])
        for col in range(3):
            frm.grid_columnconfigure(col, pad=14)

    @frm(padding=2)
    def _frm_adv_backgrounds(self, frm: ttk.Frame) -> None:
        rows = []
        self._bg_comboboxes: list[ttk.Combobox] = []
        for e in self.character.backgrounds:
            cb = ttk.Combobox(frm, textvariable=e["name"], width=20)
            self._lockable.append(cb)
            self._bg_comboboxes.append(cb)
            rows.append([cb, self._frm_dots(frm, e["vars"])])
        place_widgets(rows)
        self._refresh_bg_values()
        locale.on_change(self._refresh_bg_values)

    def _refresh_bg_values(self) -> None:
        """Update background combobox option lists to the active language."""
        names = list((locale.raw("sheet.backgrounds") or {}).values())
        for cb in getattr(self, "_bg_comboboxes", []):
            cb.configure(values=names)

    @frm(padding=2)
    def _frm_adv_disciplines(self, frm: ttk.Frame) -> None:
        """
        Disciplines column.

        Each row: [discipline combobox] [path combobox — only when discipline
        has paths] [dots].  The path combobox is always present in the grid
        but hidden via grid_remove() when not applicable.
        """
        rows = []
        self._disc_comboboxes: list[ttk.Combobox] = []
        self._path_comboboxes: list[ttk.Combobox] = []

        for e in self.character.disciplines:
            cb_disc = ttk.Combobox(frm, textvariable=e["name"], width=16)
            cb_path = ttk.Combobox(frm, textvariable=e["path"], width=16)
            self._lockable.append(cb_disc)
            self._lockable.append(cb_path)
            self._disc_comboboxes.append(cb_disc)
            self._path_comboboxes.append(cb_path)

            rows.append([cb_disc, cb_path, self._frm_dots(frm, e["vars"])])
            self._bind_disc_path(e["name"], e["path"], cb_path)

        place_widgets(rows)
        self._refresh_disc_values()
        locale.on_change(self._refresh_disc_values)

    def _bind_disc_path(
        self,
        name_var: StringVar,
        path_var: StringVar,
        cb_path: ttk.Combobox,
    ) -> None:
        """
        Keep the path combobox in sync with the selected discipline.

        Shows / populates the path combobox when the discipline has paths;
        hides it and clears path_var otherwise.  Skipped while
        self._translating is True so that bulk translation updates are
        not interrupted.
        """
        def _update(*_) -> None:
            if self._translating:
                return
            disc_display = name_var.get()
            en_key = self._disc_display_to_en(disc_display)
            paths_en = DISCIPLINE_PATHS.get(en_key, ())

            if paths_en:
                path_names = [
                    locale.t(f"sheet.discipline_paths.{en_key}.{p}") for p in paths_en
                ]
                cb_path.configure(values=path_names)
                cb_path.grid()
            else:
                path_var.set("")
                cb_path.configure(values=[])
                cb_path.grid_remove()

        name_var.trace_add("write", _update)
        _update()

    def _disc_display_to_en(self, display_name: str) -> str:
        """Convert a discipline display name (active language) to its English canonical key."""
        disc_map: dict = locale.raw("sheet.disciplines") or {}
        reverse = {v: k for k, v in disc_map.items()}
        return reverse.get(display_name, display_name)

    def _refresh_disc_values(self) -> None:
        """Update discipline combobox option lists to the active language."""
        names = list((locale.raw("sheet.disciplines") or {}).values())
        for cb in getattr(self, "_disc_comboboxes", []):
            cb.configure(values=names)

    def _refresh_translations(self) -> None:
        """
        Translate all known selected values to the active language.

        Called after every language switch (registered last so option lists
        are already updated).  User-entered custom strings are left untouched.
        """
        self._translating = True
        try:
            self._translate_disciplines()
            self._translate_simple_entries(self.character.backgrounds, "sheet.backgrounds")
            self._translate_simple_entries(self.character.merits,      "sheet.merits")
            self._translate_simple_entries(self.character.flaws,       "sheet.flaws")
        finally:
            self._translating = False

        # Re-evaluate path combobox visibility and option lists now that
        # discipline names are in the new language.
        for entry, cb_path in zip(
            self.character.disciplines,
            getattr(self, "_path_comboboxes", []),
        ):
            disc_en = locale.reverse_lookup_en("sheet.disciplines", entry["name"].get())
            paths_en = DISCIPLINE_PATHS.get(disc_en, ())
            if paths_en:
                path_names = [
                    locale.t(f"sheet.discipline_paths.{disc_en}.{p}") for p in paths_en
                ]
                cb_path.configure(values=path_names)
                cb_path.grid()
            else:
                cb_path.configure(values=[])
                cb_path.grid_remove()

    def _translate_disciplines(self) -> None:
        """Translate discipline name and path StringVars to the active language."""
        for entry in self.character.disciplines:
            old_name = entry["name"].get()
            # Find English key while old_name is still in the previous language.
            disc_en = locale.reverse_lookup_en("sheet.disciplines", old_name)
            new_name = locale.translate_known("sheet.disciplines", old_name)

            old_path = entry["path"].get()
            new_path = locale.translate_known(
                f"sheet.discipline_paths.{disc_en}", old_path
            )

            if new_name != old_name:
                entry["name"].set(new_name)
            if new_path != old_path:
                entry["path"].set(new_path)

    @staticmethod
    def _translate_simple_entries(entries: list[dict], section: str) -> None:
        """Translate the 'name' StringVar of each entry using *section*."""
        for entry in entries:
            old = entry["name"].get()
            new = locale.translate_known(section, old)
            if new != old:
                entry["name"].set(new)

    @frm(padding=2)
    def _frm_adv_virtues(self, frm: ttk.Frame) -> None:
        """Virtues column uses StringVars that are kept in sync with the locale."""
        place_widgets([
            [ttk.Label(frm, textvariable=e["name"], width=30,
                       style="sheet.S.TLabel", anchor="w"),
             self._frm_dots(frm, e["vars"])]
            for e in self.character.virtues
        ])

    def _sync_virtue_names(self) -> None:
        """Update virtue name StringVars to match the active language."""
        virtue_names = locale.raw("sheet.virtue_names")
        if not isinstance(virtue_names, list):
            return
        for i, entry in enumerate(self.character.virtues):
            if i < len(virtue_names):
                entry["name"].set(virtue_names[i])

    # ── Bottom: Merits/Flaws + Trackers ───────────────────────────────────────

    @frm(padding=5, style="solid.TFrame")
    def _frm_bottom(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._frm_merits_flaws(frm),
            self._frm_sheet_trackers(frm),
            self._frm_wounds_weakness(frm),
        ]])
        for col in range(3):
            frm.grid_columnconfigure(col, pad=18)

    # ── Merits & Flaws ────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_merits_flaws(self, frm: ttk.Frame) -> None:
        merit_col = self._frm_mf_column(frm, "sheet.mf.merits", self.character.merits,
                                        MERITS, "sheet.merits", max_cost=7)
        flaw_col = self._frm_mf_column(frm, "sheet.mf.flaws", self.character.flaws,
                                       FLAWS, "sheet.flaws", max_cost=5)

        self._merit_total_lbl = ttk.Label(frm, style="sheet.S.TLabel")
        self._flaw_total_lbl = ttk.Label(frm, style="sheet.S.TLabel")
        self._net_lbl = ttk.Label(frm, style="sheet.S.TLabel")

        place_widgets([
            [merit_col, flaw_col],
            [self._merit_total_lbl, self._flaw_total_lbl],
            [self._net_lbl],
        ])

        self._setup_mf_totals()

    @frm(padding=2)
    def _frm_mf_column(
        self,
        frm: ttk.Frame,
        title_key: str,
        entries: list[dict],
        en_lookup: dict[str, int],
        locale_section: str,
        max_cost: int,
    ) -> None:
        """Single Merits or Flaws column with locale-aware combobox values and autofill."""
        pts_lbl = self._tlabel(frm, "sheet.mf.pts", style="sheet.S.TLabel")
        rows: list[list] = [[
            self._tlabel(frm, title_key, style="sheet.M.TLabel"),
            pts_lbl,
        ]]

        comboboxes: list[ttk.Combobox] = []
        for entry in entries:
            self._bind_autofill_locale(entry["name"], entry["cost"], en_lookup, locale_section)
            cb = ttk.Combobox(frm, textvariable=entry["name"], width=15)
            sp = ttk.Spinbox(frm, from_=0, to=max_cost,
                             textvariable=entry["cost"],
                             width=3, style="sheet.TSpinbox")
            self._lockable.extend([cb, sp])
            comboboxes.append(cb)
            rows.append([cb, sp])
        place_widgets(rows)

        def _refresh_values() -> None:
            names = list((locale.raw(locale_section) or {}).values())
            for cb in comboboxes:
                cb.configure(values=names)

        _refresh_values()
        locale.on_change(_refresh_values)

    @staticmethod
    def _bind_autofill_locale(
        name_var: StringVar,
        cost_var: IntVar,
        en_lookup: dict[str, int],
        locale_section: str,
    ) -> None:
        """
        Auto-fill cost when a known name is selected.

        Uses reverse_lookup_en so autofill works regardless of the active language.
        """
        def _on_name_change(*_) -> None:
            en_key = locale.reverse_lookup_en(locale_section, name_var.get())
            if en_key in en_lookup:
                cost_var.set(en_lookup[en_key])
        name_var.trace_add("write", _on_name_change)

    def _setup_mf_totals(self) -> None:
        """Wire total labels to update whenever any merit/flaw cost changes."""
        for entry in self.character.merits + self.character.flaws:
            entry["cost"].trace_add("write", lambda *_: self._refresh_mf_totals())
        self._refresh_mf_totals()

    def _refresh_mf_totals(self) -> None:
        """Recompute and re-render merit/flaw totals in the active language."""
        if self._merit_total_lbl is None:
            return
        m = sum(e["cost"].get() for e in self.character.merits)
        f = sum(e["cost"].get() for e in self.character.flaws)
        self._merit_sum = m
        self._flaw_sum = f

        self._merit_total_lbl.configure(text=locale.t("sheet.mf.cost").format(n=m))
        self._flaw_total_lbl.configure(text=locale.t("sheet.mf.gain").format(n=f))

        net = f - m
        color = _VIRTUE_COLOR if net > 0 else (_DISABLED_COLOR if net < 0 else "")
        self._net_lbl.configure(
            text=locale.t("sheet.mf.free").format(n=net),
            foreground=color,
        )

    # ── Sheet trackers ────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_sheet_trackers(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._frm_tracker_header(frm, "sheet.sheet_trackers.willpower",
                                      self.character.willpower_max,
                                      self._refresh_wp_cells,
                                      max_to=10)],
            [self._frm_wp_cells(frm)],
            [self._tlabel(frm, "sheet.sheet_trackers.humanity", style="sheet.M.TLabel")],
            [self._frm_humanity_cells(frm)],
            [self._frm_tracker_header(frm, "sheet.sheet_trackers.blood_pool",
                                      self.character.blood_max_value,
                                      self._refresh_sheet_blood_cells)],
            [self._frm_sheet_blood_cells(frm)],
        ])

    @frm(padding=5)
    def _frm_wounds_weakness(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._tlabel(frm, "sheet.sheet_trackers.health", style="sheet.M.TLabel")],
            [self._frm_sheet_wounds(frm)],
        ])

    @frm(padding=0)
    def _frm_sheet_wounds(self, frm: ttk.Frame) -> None:
        """Health levels table: name | penalty | clickable dot."""
        char = self.character
        self._wound_name_labels = []
        rows: list[list] = []
        for i, level in enumerate(WOUND_LEVELS):
            var = char.wounds[i]
            dot = ttk.Label(frm, text="●" if var.get() else "○",
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add(
                "write",
                lambda *_, l=dot, v=var: l.configure(text="●" if v.get() else "○"),
            )
            dot.bind("<Button-1>", lambda e, y=i: char.set_wounds(y))

            name_lbl = ttk.Label(frm, text=locale.t(f"wound_levels.{level.name}"),
                                 width=15, anchor="e", style="sheet.S.TLabel")
            self._wound_name_labels.append((name_lbl, level.name))

            penalty_text = str(level.penalty) if level.penalty else ""
            rows.append([
                name_lbl,
                ttk.Label(frm, text=penalty_text, width=2,
                          anchor="center", style="sheet.S.TLabel"),
                dot,
            ])
        place_widgets(rows)

    def _refresh_wound_names(self) -> None:
        """Update wound level name labels to the active language."""
        for lbl, name in self._wound_name_labels:
            try:
                lbl.configure(text=locale.t(f"wound_levels.{name}"))
            except Exception:
                pass

    @frm(padding=0)
    def _frm_tracker_header(
        self,
        frm: ttk.Frame,
        title_key: str,
        max_var: IntVar,
        refresh_cmd,
        max_to: int = 40,
    ) -> None:
        sp = ttk.Spinbox(frm, from_=1, to=max_to, textvariable=max_var,
                         command=refresh_cmd, width=3, style="sheet.TSpinbox")
        self._lockable.append(sp)
        place_widgets([[
            self._tlabel(frm, title_key, style="sheet.M.TLabel"),
            self._tlabel(frm, "sheet.sheet_trackers.max", style="sheet.S.TLabel"),
            sp,
        ]])

    # ── Virtue-colored tracker helpers ───────────────────────────────────────

    def _build_tracker_dot_row(
        self,
        parent: ttk.Frame,
        count: int,
        click_fn,
    ) -> list[ttk.Label]:
        labels = [
            ttk.Label(parent, text="○", style="sheet.Dot.TLabel", cursor="hand2")
            for _ in range(count)
        ]
        for i, lbl in enumerate(labels):
            lbl.bind("<Button-1>", lambda e, x=i: click_fn(x))
        place_widgets([labels])
        return labels

    # ── Willpower cells ───────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_wp_cells(self, frm: ttk.Frame) -> None:
        char = self.character
        self._wp_labels = self._build_tracker_dot_row(frm, 10, self._click_will)

        char.will_value.trace_add("write", lambda *_: self._refresh_wp_cells())
        char.willpower_max.trace_add("write", lambda *_: self._refresh_wp_cells())
        for v in char.virtues[2]["vars"]:
            v.trace_add("write", lambda *_: self._refresh_wp_cells())

        self._refresh_wp_cells()

    def _click_will(self, clicked: int) -> None:
        char = self.character
        if clicked >= char.willpower_max.get():
            return
        char.set_will(clicked)

    def _refresh_wp_cells(self) -> None:
        if not self._wp_labels:
            return
        char = self.character
        courage = sum(v.get() for v in char.virtues[2]["vars"])
        current = char.will_value.get()
        max_val = char.willpower_max.get()

        for i, lbl in enumerate(self._wp_labels):
            if i >= max_val:
                lbl.configure(text="○", foreground=_DISABLED_COLOR, cursor="")
                lbl.unbind("<Button-1>")
            elif i < current:
                color = _VIRTUE_COLOR if i < courage else ""
                lbl.configure(text="●", foreground=color, cursor="hand2")
                lbl.bind("<Button-1>", lambda e, x=i: self._click_will(x))
            else:
                lbl.configure(text="○", foreground="", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, x=i: self._click_will(x))

    # ── Humanity cells ────────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_humanity_cells(self, frm: ttk.Frame) -> None:
        char = self.character
        self._humanity_labels = self._build_tracker_dot_row(frm, 10, char.set_humanity)

        char.humanity_value.trace_add("write", lambda *_: self._refresh_humanity_cells())
        for v in char.virtues[0]["vars"]:
            v.trace_add("write", lambda *_: self._refresh_humanity_cells())

        self._refresh_humanity_cells()

    def _refresh_humanity_cells(self) -> None:
        if not self._humanity_labels:
            return
        char = self.character
        conscience = sum(v.get() for v in char.virtues[0]["vars"])
        current = char.humanity_value.get()

        for i, lbl in enumerate(self._humanity_labels):
            if i < current:
                color = _VIRTUE_COLOR if i < conscience else ""
                lbl.configure(text="●", foreground=color)
            else:
                lbl.configure(text="○", foreground="")

    # ── Blood cells (sheet) ───────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_sheet_blood_cells(self, frm: ttk.Frame) -> None:
        self._sheet_blood_labels = []
        char = self.character

        for i in range(4):
            row_labels: list[ttk.Label] = []
            for j in range(10):
                var = char.blood[i][j]
                lbl = ttk.Label(
                    frm, text="●" if var.get() else "○",
                    width=2, style="sheet.Dot.TLabel", cursor="hand2",
                )
                var.trace_add(
                    "write",
                    lambda *_, l=lbl, v=var: l.configure(text="●" if v.get() else "○"),
                )
                lbl.bind("<Button-1>", lambda e, r=i, c=j: char.set_blood(r, c))
                row_labels.append(lbl)
            self._sheet_blood_labels.append(row_labels)

        place_widgets(self._sheet_blood_labels)

        char.blood_max_value.trace_add(
            "write", lambda *_: self._refresh_sheet_blood_cells())
        self._refresh_sheet_blood_cells()

    def _refresh_sheet_blood_cells(self) -> None:
        if not self._sheet_blood_labels:
            return
        char = self.character
        max_blood = char.blood_max_value.get()

        for i, row in enumerate(self._sheet_blood_labels):
            for j, lbl in enumerate(row):
                active = i * 10 + j < max_blood
                if active:
                    lbl.configure(cursor="hand2", foreground="")
                    lbl.bind("<Button-1>", lambda e, r=i, c=j: char.set_blood(r, c))
                else:
                    lbl.configure(cursor="", foreground=_DISABLED_COLOR)
                    lbl.unbind("<Button-1>")
                    char.blood[i][j].set(False)

        if char.blood_value.get() > max_blood:
            char.blood_value.set(max_blood)
            char.set_blood(load=True)

    # ── Stat line ────────────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_line(
        self,
        frm: ttk.Frame,
        label: str,
        name_prefix: str,
        variables: list[BooleanVar],
        spec_var: StringVar,
    ) -> None:
        spec_entry = ttk.Entry(frm, textvariable=spec_var,
                               width=15, style="sheet.TEntry")
        self._lockable.append(spec_entry)

        def _update_spec_state(*_) -> None:
            if self.root.locked.get():
                return
            filled = sum(v.get() for v in variables)
            if filled >= 4:
                spec_entry.configure(state="normal")
            else:
                spec_var.set("")
                spec_entry.configure(state="disabled")

        self._spec_refreshers.append(_update_spec_state)

        for var in variables:
            var.trace_add("write", _update_spec_state)
        _update_spec_state()

        name_lbl = self._tlabel(frm, f"{name_prefix}.{label}",
                                width=15, anchor="e", style="sheet.S.TLabel")
        place_widgets([[name_lbl, spec_entry, self._frm_dots(frm, variables)]])

    @frm(padding=0)
    def _frm_dots(self, frm: ttk.Frame, variables: list[BooleanVar]) -> None:
        row: list[ttk.Label] = []
        for idx, var in enumerate(variables):
            lbl = ttk.Label(frm, text="●" if var.get() else "○",
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write",
                          lambda *_, l=lbl, v=var: l.configure(
                              text="●" if v.get() else "○"))
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
    def _set_dots(variables: list[BooleanVar], clicked: int) -> None:
        filled = sum(v.get() for v in variables)
        threshold = clicked if filled == clicked + 1 else clicked + 1
        for i, var in enumerate(variables):
            var.set(i < threshold)