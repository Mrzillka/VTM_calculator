from __future__ import annotations

from tkinter import BooleanVar, IntVar, StringVar
from tkinter import ttk

from config import BACKGROUNDS, DISCIPLINES, FLAWS, MERITS, WOUND_LEVELS
from game.character import Character
from ui.utils import frm, place_widgets

# Foreground color applied to dots covered by virtue rating
_VIRTUE_COLOR = "crimson"
_DISABLED_COLOR = "gray"


class Interface(ttk.Frame):
    """Main content frame for the character sheet."""

    def __init__(self, parent: ttk.Frame, root) -> None:
        super().__init__(parent)
        self.root = root
        self.character: Character = root.character

        # Cached label lists for virtue-aware trackers, populated during build
        self._wp_labels: list[ttk.Label] = []
        self._humanity_labels: list[ttk.Label] = []
        self._sheet_blood_labels: list[list[ttk.Label]] = []

        self._build()

    def _build(self) -> None:
        sections = [
            ("Attributes", self._frm_attributes()),
            ("Abilities",  self._frm_abilities()),
            ("Advantages", self._frm_advantages()),
        ]
        rows: list[list] = [
            [ttk.Label(self, text="Vampire the Masquerade", style="sheet.title.TLabel")],
            [self._frm_header()],
        ]
        for title, content in sections:
            rows.append([self._collapsible_header(title, content)])
            rows.append([content])
        rows.append([self._collapsible_header("Merits, Flaws & Trackers",
                                              bottom := self._frm_bottom())])
        rows.append([bottom])
        place_widgets(rows)

    def _collapsible_header(self, title: str, content: ttk.Frame) -> ttk.Label:
        """Return a clickable label that toggles visibility of *content*."""
        visible = BooleanVar(value=True)
        lbl = ttk.Label(self, style="sheet.L.TLabel", cursor="hand2")

        def _toggle(e=None) -> None:
            visible.set(not visible.get())
            lbl.configure(text=f"{'▼' if visible.get() else '►'}  {title}")
            if visible.get():
                content.grid()
            else:
                content.grid_remove()

        lbl.configure(text=f"▼  {title}")
        lbl.bind("<Button-1>", _toggle)
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
        place_widgets([
            [ttk.Label(frm, text=label, width=10, anchor="e", style="sheet.S.TLabel"),
             ttk.Entry(frm, textvariable=var, width=20, style="sheet.TEntry")]
            for label, var in fields
        ])

    # ── Attributes & Abilities ────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_attributes(self, frm: ttk.Frame) -> None:
        self._place_stat_columns(frm, self.character.attributes)

    @frm(padding=5)
    def _frm_abilities(self, frm: ttk.Frame) -> None:
        self._place_stat_columns(frm, self.character.abilities)

    def _place_stat_columns(self, parent: ttk.Frame, categories: dict) -> None:
        """Render category name labels in one row and their stat-line frames below."""
        headers = [ttk.Label(parent, text=name, style="sheet.M.TLabel")
                   for name in categories]
        contents = [self._frm_stat_lines(parent, data)
                    for data in categories.values()]
        place_widgets([headers, contents])
        for col in range(len(categories)):
            parent.grid_columnconfigure(col, pad=14)

    @frm(padding=0)
    def _frm_stat_lines(
        self,
        frm: ttk.Frame,
        data: dict[str, dict[str, StringVar | list[BooleanVar]]],
    ) -> None:
        place_widgets([
            [self._frm_line(frm, label, values["vars"], values["spec"])]
            for label, values in data.items()
        ])

    # ── Advantages ────────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_advantages(self, frm: ttk.Frame) -> None:
        headers = [ttk.Label(frm, text=t, style="sheet.M.TLabel")
                   for t in ("Backgrounds", "Disciplines", "Virtues")]
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
        """
        Backgrounds column: editable Combobox per row so the user can
        either pick a predefined background or type a custom one.
        """
        place_widgets([
            [ttk.Combobox(frm, textvariable=e["name"],
                          values=list(BACKGROUNDS), width=16),
             self._frm_dots(frm, e["vars"])]
            for e in self.character.backgrounds
        ])

    @frm(padding=2)
    def _frm_adv_disciplines(self, frm: ttk.Frame) -> None:
        """Disciplines column: read-only Combobox, selection only."""
        place_widgets([
            [ttk.Combobox(frm, textvariable=e["name"],
                          values=list(DISCIPLINES), width=16, state="readonly"),
             self._frm_dots(frm, e["vars"])]
            for e in self.character.disciplines
        ])

    @frm(padding=2)
    def _frm_adv_virtues(self, frm: ttk.Frame) -> None:
        """Virtues column: three fixed rows defined by VtM rules."""
        place_widgets([
            [ttk.Label(frm, textvariable=e["name"], width=22,
                       style="sheet.S.TLabel", anchor="w"),
             self._frm_dots(frm, e["vars"])]
            for e in self.character.virtues
        ])

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
        merit_names = sorted(MERITS)
        flaw_names = sorted(FLAWS)

        merit_col = self._frm_mf_column(frm, "Merits", self.character.merits,
                                        merit_names, MERITS, max_cost=7)
        flaw_col = self._frm_mf_column(frm, "Flaws", self.character.flaws,
                                       flaw_names, FLAWS, max_cost=5)

        merit_total = ttk.Label(frm, text="Cost: 0 pts", style="sheet.S.TLabel")
        flaw_total = ttk.Label(frm, text="Gain: 0 pts", style="sheet.S.TLabel")
        net_lbl = ttk.Label(frm, text="Free points: 0", style="sheet.S.TLabel")

        place_widgets([
            [merit_col, flaw_col],
            [merit_total, flaw_total],
            [net_lbl],
        ])

        self._setup_mf_totals(merit_total, flaw_total, net_lbl)

    @frm(padding=2)
    def _frm_mf_column(
        self,
        frm: ttk.Frame,
        title: str,
        entries: list[dict],
        names: list[str],
        lookup: dict[str, int],
        max_cost: int,
    ) -> None:
        """Single Merits or Flaws column: header + rows of (combobox, spinbox)."""
        header_row = [
            ttk.Label(frm, text=title, style="sheet.M.TLabel"),
            ttk.Label(frm, text="pts", style="sheet.S.TLabel"),
        ]
        rows: list[list] = [header_row]
        for entry in entries:
            self._bind_autofill(entry["name"], entry["cost"], lookup)
            rows.append([
                ttk.Combobox(frm, textvariable=entry["name"],
                             values=names, width=15),
                ttk.Spinbox(frm, from_=0, to=max_cost,
                            textvariable=entry["cost"],
                            width=3, style="sheet.TSpinbox"),
            ])
        place_widgets(rows)

    @staticmethod
    def _bind_autofill(name_var: StringVar, cost_var: IntVar,
                       lookup: dict[str, int]) -> None:
        """Auto-fill cost spinbox when a known name is selected from the combobox."""
        def _on_name_change(*_) -> None:
            name = name_var.get()
            if name in lookup:
                cost_var.set(lookup[name])
        name_var.trace_add("write", _on_name_change)

    def _setup_mf_totals(
        self,
        merit_lbl: ttk.Label,
        flaw_lbl: ttk.Label,
        net_lbl: ttk.Label,
    ) -> None:
        """Wire total labels to update whenever any merit/flaw cost changes."""
        def _update(*_) -> None:
            m = sum(e["cost"].get() for e in self.character.merits)
            f = sum(e["cost"].get() for e in self.character.flaws)
            merit_lbl.configure(text=f"Cost: {m} pts")
            flaw_lbl.configure(text=f"Gain: {f} pts")
            net = f - m
            color = _VIRTUE_COLOR if net > 0 else (_DISABLED_COLOR if net < 0 else "")
            net_lbl.configure(text=f"Free points: {net:+d}", foreground=color)

        for entry in self.character.merits + self.character.flaws:
            entry["cost"].trace_add("write", lambda *_: _update())
        _update()

    # ── Sheet trackers ────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_sheet_trackers(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._frm_tracker_header(frm, "Willpower",
                                      self.character.willpower_max,
                                      self._refresh_wp_cells,
                                      max_to=10)],
            [self._frm_wp_cells(frm)],
            [ttk.Label(frm, text="Humanity / Path", style="sheet.M.TLabel")],
            [self._frm_humanity_cells(frm)],
            [self._frm_tracker_header(frm, "Blood Pool",
                                      self.character.blood_max_value,
                                      self._refresh_sheet_blood_cells)],
            [self._frm_sheet_blood_cells(frm)],
        ])

    @frm(padding=5)
    def _frm_wounds_weakness(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="Health Levels", style="sheet.M.TLabel")],
            [self._frm_sheet_wounds(frm)],
        ])

    @frm(padding=0)
    def _frm_sheet_wounds(self, frm: ttk.Frame) -> None:
        """Health levels table: name | penalty | clickable dot."""
        char = self.character
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
            penalty_text = str(level.penalty) if level.penalty else ""
            rows.append([
                ttk.Label(frm, text=level.name, width=12,
                          anchor="e", style="sheet.S.TLabel"),
                ttk.Label(frm, text=penalty_text, width=2,
                          anchor="center", style="sheet.S.TLabel"),
                dot,
            ])
        place_widgets(rows)

    @frm(padding=0)
    def _frm_tracker_header(
        self,
        frm: ttk.Frame,
        title: str,
        max_var: IntVar,
        refresh_cmd,
        max_to: int = 40,
    ) -> None:
        """Label + 'Max:' label + spinbox in a single row."""
        place_widgets([[
            ttk.Label(frm, text=title, style="sheet.M.TLabel"),
            ttk.Label(frm, text="Max:", style="sheet.S.TLabel"),
            ttk.Spinbox(frm, from_=1, to=max_to, textvariable=max_var,
                        command=refresh_cmd, width=3, style="sheet.TSpinbox"),
        ]])

    # ── Virtue-colored tracker helpers ───────────────────────────────────────

    def _build_tracker_dot_row(
        self,
        parent: ttk.Frame,
        count: int,
        click_fn,
    ) -> list[ttk.Label]:
        """
        Build *count* dot labels in a single row inside *parent* and return them.

        click_fn(index) is called when the user clicks a dot.
        The caller is responsible for wiring trace callbacks and the initial paint.
        """
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
        """
        Build 10 willpower dot labels.

        Cells 0..courage-1 are tinted crimson when filled to indicate
        the virtue-provided baseline. Cells beyond willpower_max are disabled.
        """
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
        """Repaint willpower labels based on current value, max, and Courage."""
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
        """
        Build 10 humanity dot labels.

        Cells 0..conscience-1 are tinted crimson when filled to indicate
        the Conscience / Conviction virtue baseline.
        """
        char = self.character
        self._humanity_labels = self._build_tracker_dot_row(
            frm, 10, char.set_humanity)

        char.humanity_value.trace_add("write", lambda *_: self._refresh_humanity_cells())
        for v in char.virtues[0]["vars"]:
            v.trace_add("write", lambda *_: self._refresh_humanity_cells())

        self._refresh_humanity_cells()

    def _refresh_humanity_cells(self) -> None:
        """Repaint humanity labels based on current value and Conscience/Conviction."""
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
        """Build 4×10 blood cell labels mirroring the main tracker layout."""
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
        """Grey out and unbind cells beyond blood_max_value."""
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
        variables: list[BooleanVar],
        spec_var: StringVar,
    ) -> None:
        spec_entry = ttk.Entry(frm, textvariable=spec_var,
                               width=15, style="sheet.TEntry")

        def _update_spec_state(*_) -> None:
            filled = sum(v.get() for v in variables)
            if filled >= 4:
                spec_entry.configure(state="normal")
            else:
                spec_var.set("")
                spec_entry.configure(state="disabled")

        for var in variables:
            var.trace_add("write", _update_spec_state)
        _update_spec_state()

        place_widgets([[
            ttk.Label(frm, text=label, width=10, style="sheet.S.TLabel"),
            spec_entry,
            self._frm_dots(frm, variables),
        ]])

    @frm(padding=0)
    def _frm_dots(self, frm: ttk.Frame, variables: list[BooleanVar]) -> None:
        row: list[ttk.Label] = []
        for idx, var in enumerate(variables):
            lbl = ttk.Label(frm, text="●" if var.get() else "○",
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write",
                          lambda *_, l=lbl, v=var: l.configure(
                              text="●" if v.get() else "○"))
            lbl.bind("<Button-1>", lambda e, i=idx, v=variables: self._set_dots(v, i))
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