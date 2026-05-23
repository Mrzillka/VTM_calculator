from __future__ import annotations

import tkinter as tk
from tkinter import BooleanVar, IntVar, StringVar
from tkinter import ttk
from typing import Callable

from config import BLOOD_COLS, BLOOD_ROWS, DISCIPLINE_PATHS, FLAWS, MAX_BLOOD_POOL, MAX_DOT_TRACKER, MERITS, SPEC_MIN_DOTS, WOUND_LEVELS
from lang import locale
from ui.theme import theme
from ui.utils import frm, place_widgets


# ── Attributes & Abilities ────────────────────────────────────────────────────

class _AttributesMixin:

    @frm(padding=5)
    def _frm_attributes(self, frm: ttk.Frame) -> None:
        char = self.character
        boost_map = {
            "Strength":  char.str_boost,
            "Dexterity": char.dex_boost,
            "Stamina":   char.sta_boost,
        }
        categories = char.attributes
        headers = [
            self._tlabel(frm, f"sheet.attr_categories.{name}", style="sheet.M.TLabel")
            for name in categories
        ]
        contents = [
            self._frm_stat_lines(
                frm, data, "sheet.attr_names",
                boost_map=(boost_map if cat == "Physical" else None),
            )
            for cat, data in categories.items()
        ]
        place_widgets([headers, contents])
        for col in range(len(categories)):
            frm.grid_columnconfigure(col, pad=14)

    @frm(padding=5)
    def _frm_abilities(self, frm: ttk.Frame) -> None:
        char = self.character
        category_names = list(char.abilities.keys())

        headers = [
            self._tlabel(frm, f"sheet.ability_categories.{name}", style="sheet.M.TLabel")
            for name in category_names
        ]
        contents = [
            self._frm_stat_lines(
                frm,
                char.abilities[cat],
                "sheet.ability_names",
                char.custom_abilities.get(cat, []),
            )
            for cat in category_names
        ]
        place_widgets([headers, contents])
        for col in range(len(category_names)):
            frm.grid_columnconfigure(col, pad=14)

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
        custom_entries: list[dict] | None = None,
        boost_map: dict[str, IntVar] | None = None,
    ) -> None:
        """
        Build all stat rows directly in one shared grid so tkinter aligns
        columns uniformly across standard and custom rows.

        Standard rows: right-aligned Label (col 0), spec Entry (col 1), dots (col 2).
        Custom rows:   editable Entry (col 0), spec Entry (col 1), dots (col 2).
        """
        row_idx = 0

        for label, values in data.items():
            name_lbl = self._tlabel(frm, f"{name_prefix}.{label}",
                                    width=15, anchor="e", style="sheet.S.TLabel")
            spec_entry = ttk.Entry(frm, textvariable=values["spec"],
                                   width=15, style="sheet.TEntry")
            if boost_map and label in boost_map:
                dots = self._frm_dots_with_boost(frm, values["vars"], boost_map[label])
            else:
                dots = self._frm_dots(frm, values["vars"])

            self._lockable.append(spec_entry)
            self._wire_spec_state(spec_entry, values["vars"], values["spec"])

            name_lbl.grid(row=row_idx, column=0, sticky="e", pady=1)
            spec_entry.grid(row=row_idx, column=1, padx=(2, 0), pady=1)
            dots.grid(row=row_idx, column=2, padx=(2, 0), pady=1)
            row_idx += 1

        for entry in (custom_entries or []):
            name_entry = ttk.Entry(frm, textvariable=entry["name"],
                                   width=15, style="sheet.TEntry")
            spec_entry = ttk.Entry(frm, textvariable=entry["spec"],
                                   width=15, style="sheet.TEntry")
            dots = self._frm_dots(frm, entry["vars"])

            self._lockable.extend([name_entry, spec_entry])
            self._wire_spec_state(spec_entry, entry["vars"], entry["spec"])

            name_entry.grid(row=row_idx, column=0, sticky="ew", pady=1)
            spec_entry.grid(row=row_idx, column=1, padx=(2, 0), pady=1)
            dots.grid(row=row_idx, column=2, padx=(2, 0), pady=1)
            row_idx += 1

    def _wire_spec_state(
        self,
        spec_entry: ttk.Entry,
        variables: list[BooleanVar],
        spec_var: StringVar,
    ) -> None:
        """Disable the specialisation entry until at least 4 dots are filled."""
        def _update(*_) -> None:
            # Guard against stale traces that fire after the widget is destroyed.
            try:
                exists = spec_entry.winfo_exists()
            except tk.TclError:
                return
            if not exists or self.root.locked.get():
                return
            if sum(v.get() for v in variables) >= SPEC_MIN_DOTS:
                spec_entry.configure(state="normal")
            else:
                spec_var.set("")
                spec_entry.configure(state="disabled")

        self._spec_updaters.append(_update)
        for var in variables:
            var.trace_add("write", _update)
        _update()


# ── Advantages ────────────────────────────────────────────────────────────────

class _AdvantagesMixin:

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
        names = list((locale.raw("sheet.backgrounds") or {}).values())
        for cb in getattr(self, "_bg_comboboxes", []):
            cb.configure(values=names)

    @frm(padding=2)
    def _frm_adv_disciplines(self, frm: ttk.Frame) -> None:
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

        place_widgets(rows)

        for e, cb_path in zip(self.character.disciplines, self._path_comboboxes):
            self._bind_disc_path(e["name"], e["path"], cb_path)
        self._refresh_disc_values()
        locale.on_change(self._refresh_disc_values)

    def _bind_disc_path(
        self,
        name_var: StringVar,
        path_var: StringVar,
        cb_path: ttk.Combobox,
    ) -> None:
        def _update(*_) -> None:
            # Guard against stale traces referencing a destroyed combobox.
            try:
                exists = cb_path.winfo_exists()
            except tk.TclError:
                return
            if not exists or self._translating:
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

        trace_id = name_var.trace_add("write", _update)
        # Remove the trace when the combobox is destroyed to prevent accumulation.
        cb_path.bind(
            "<Destroy>",
            lambda e, tid=trace_id: name_var.trace_remove("write", tid),
        )
        _update()

    def _disc_display_to_en(self, display_name: str) -> str:
        # Search across all locales so EN names resolve correctly on a RU interface
        # and vice versa.
        return locale.reverse_lookup_en("sheet.disciplines", display_name)

    def _refresh_disc_values(self) -> None:
        names = list((locale.raw("sheet.disciplines") or {}).values())
        for cb in getattr(self, "_disc_comboboxes", []):
            cb.configure(values=names)

    def _refresh_translations(self) -> None:
        self._translating = True
        try:
            self._translate_disciplines()
            self._translate_simple_entries(self.character.backgrounds, "sheet.backgrounds")
            self._translate_simple_entries(self.character.merits,      "sheet.merits")
            self._translate_simple_entries(self.character.flaws,       "sheet.flaws")
        finally:
            self._translating = False

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
        for entry in self.character.disciplines:
            old_name = entry["name"].get()
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
        for entry in entries:
            old = entry["name"].get()
            new = locale.translate_known(section, old)
            if new != old:
                entry["name"].set(new)

    @frm(padding=2)
    def _frm_adv_virtues(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, textvariable=e["name"], width=30,
                       style="sheet.S.TLabel", anchor="w"),
             self._frm_dots(frm, e["vars"])]
            for e in self.character.virtues
        ])

    def _sync_virtue_names(self) -> None:
        virtue_names = locale.raw("sheet.virtue_names")
        if not isinstance(virtue_names, list):
            return
        for i, entry in enumerate(self.character.virtues):
            if i < len(virtue_names):
                entry["name"].set(virtue_names[i])


# ── Trackers, Merits & Flaws ──────────────────────────────────────────────────

class _TrackersMixin:

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
        pts_lbl = self._tlabel(frm, "sheet.mf.pts", style="sheet.S.TLabel")
        rows: list[list] = [[
            self._tlabel(frm, title_key, style="sheet.M.TLabel"),
            pts_lbl,
        ]]

        comboboxes: list[ttk.Combobox] = []
        for entry in entries:
            self._bind_autofill_locale(entry["name"], entry["cost"], en_lookup, locale_section)
            cb = ttk.Combobox(frm, textvariable=entry["name"], width=25)
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
        def _on_name_change(*_) -> None:
            en_key = locale.reverse_lookup_en(locale_section, name_var.get())
            if en_key in en_lookup:
                cost_var.set(en_lookup[en_key])
        name_var.trace_add("write", _on_name_change)

    def _setup_mf_totals(self) -> None:
        for entry in self.character.merits + self.character.flaws:
            entry["cost"].trace_add("write", lambda *_: self._refresh_mf_totals())
        self._refresh_mf_totals()

    def _refresh_mf_totals(self) -> None:
        if self._merit_total_lbl is None:
            return
        m = sum(e["cost"].get() for e in self.character.merits)
        f = sum(e["cost"].get() for e in self.character.flaws)
        self._merit_sum = m
        self._flaw_sum = f

        self._merit_total_lbl.configure(text=locale.t("sheet.mf.cost").format(n=m))
        self._flaw_total_lbl.configure(text=locale.t("sheet.mf.gain").format(n=f))

        net = f - m
        color = theme.palette["virtue_fg"] if net > 0 else (theme.palette["disabled_fg"] if net < 0 else "")
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
                                      max_to=MAX_DOT_TRACKER)],
            [self._frm_wp_cells(frm)],
            [self._tlabel(frm, "sheet.sheet_trackers.humanity", style="sheet.M.TLabel")],
            [self._frm_humanity_cells(frm)],
            [self._frm_tracker_header(frm, "sheet.sheet_trackers.blood_pool",
                                      self.character.blood_max_value,
                                      self._refresh_sheet_blood_cells,
                                      max_to=MAX_BLOOD_POOL)],
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
        self._willpower_labels = self._build_tracker_dot_row(frm, MAX_DOT_TRACKER, self._click_will)

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
        if not self._willpower_labels:
            return
        try:
            if not self._willpower_labels[0].winfo_exists():
                self._willpower_labels = []
                return
        except tk.TclError:
            self._willpower_labels = []
            return
        char = self.character
        courage = sum(v.get() for v in char.virtues[2]["vars"])
        current = char.will_value.get()
        max_val = char.willpower_max.get()

        for i, lbl in enumerate(self._willpower_labels):
            if i >= max_val:
                lbl.configure(text="○", foreground=theme.palette["disabled_fg"], cursor="")
                lbl.unbind("<Button-1>")
            elif i < current:
                color = theme.palette["virtue_fg"] if i < courage else ""
                lbl.configure(text="●", foreground=color, cursor="hand2")
                lbl.bind("<Button-1>", lambda e, x=i: self._click_will(x))
            else:
                lbl.configure(text="○", foreground="", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, x=i: self._click_will(x))

    # ── Humanity cells ────────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_humanity_cells(self, frm: ttk.Frame) -> None:
        char = self.character
        self._humanity_dot_labels = self._build_tracker_dot_row(frm, MAX_DOT_TRACKER, char.set_humanity)

        char.humanity_value.trace_add("write", lambda *_: self._refresh_humanity_cells())
        for v in char.virtues[0]["vars"]:
            v.trace_add("write", lambda *_: self._refresh_humanity_cells())

        self._refresh_humanity_cells()

    def _refresh_humanity_cells(self) -> None:
        if not self._humanity_dot_labels:
            return
        try:
            if not self._humanity_dot_labels[0].winfo_exists():
                self._humanity_dot_labels = []
                return
        except tk.TclError:
            self._humanity_dot_labels = []
            return
        char = self.character
        conscience = sum(v.get() for v in char.virtues[0]["vars"])
        current = char.humanity_value.get()

        for i, lbl in enumerate(self._humanity_dot_labels):
            if i < current:
                color = theme.palette["virtue_fg"] if i < conscience else ""
                lbl.configure(text="●", foreground=color)
            else:
                lbl.configure(text="○", foreground="")

    # ── Blood cells (sheet) ───────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_sheet_blood_cells(self, frm: ttk.Frame) -> None:
        self._sheet_blood_labels = []
        char = self.character

        for i in range(BLOOD_ROWS):
            row_labels: list[ttk.Label] = []
            for j in range(BLOOD_COLS):
                var = char.blood[i][j]
                lbl = ttk.Label(
                    frm, text="●" if var.get() else "○",
                    width=2, style="sheet.Dot.TLabel", cursor="hand2",
                )
                var.trace_add("write", self._make_dot_trace(lbl, var))
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
        try:
            if not self._sheet_blood_labels[0][0].winfo_exists():
                self._sheet_blood_labels = []
                return
        except tk.TclError:
            self._sheet_blood_labels = []
            return
        char = self.character
        max_blood = char.blood_max_value.get()

        for i, row in enumerate(self._sheet_blood_labels):
            for j, lbl in enumerate(row):
                active = i * BLOOD_COLS + j < max_blood
                if active:
                    lbl.configure(cursor="hand2", foreground="")
                    lbl.bind("<Button-1>", lambda e, r=i, c=j: char.set_blood(r, c))
                else:
                    lbl.configure(cursor="", foreground=theme.palette["disabled_fg"])
                    lbl.unbind("<Button-1>")
                    char.blood[i][j].set(False)

        if char.blood_value.get() > max_blood:
            char.blood_value.set(max_blood)
            char.set_blood(load=True)
