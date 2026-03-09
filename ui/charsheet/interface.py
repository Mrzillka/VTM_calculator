from __future__ import annotations

from tkinter import BooleanVar, StringVar
from tkinter import ttk

from game.character import Character
from ui.utils import frm, place_widgets


class Interface(ttk.Frame):
    """Main content frame for the character sheet."""

    def __init__(self, parent: ttk.Frame, root) -> None:
        super().__init__(parent)
        self.root = root
        self.character: Character = root.character
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
        rows.append([self._frm_bottom()])
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
        headers = [
            ttk.Label(parent, text=name, style="sheet.M.TLabel")
            for name in categories
        ]
        contents = [
            self._frm_stat_lines(parent, data)
            for data in categories.values()
        ]
        place_widgets([headers, contents])

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

    # ── Advantages / Bottom ──────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_advantages(self, frm: ttk.Frame) -> None:
        pass

    @frm(padding=5)
    def _frm_bottom(self, frm: ttk.Frame) -> None:
        pass

    # ── Stat line ────────────────────────────────────────────────────────────

    @frm(padding=0)
    def _frm_line(
        self,
        frm: ttk.Frame,
        label: str,
        variables: list[BooleanVar],
        spec_var: StringVar,
        fillable: bool = False,
        label_custom: StringVar | None = None,
    ) -> None:
        name_widget = (
            ttk.Entry(frm, textvariable=label_custom, width=10, style="sheet.TEntry")
            if fillable else
            ttk.Label(frm, text=label, width=10, style="sheet.S.TLabel")
        )
        place_widgets([[
            name_widget,
            ttk.Entry(frm, textvariable=spec_var, width=15, style="sheet.TEntry"),
            self._frm_dots(frm, variables),
        ]])

    @frm(padding=5)
    def _frm_dots(self, frm: ttk.Frame, variables: list[BooleanVar]) -> None:
        row = []
        for idx, var in enumerate(variables):
            lbl = ttk.Label(frm, text="●" if var.get() else "○",
                            style="sheet.Dot.TLabel", cursor="hand2")
            var.trace_add("write",
                          lambda *_, l=lbl, v=var: l.configure(text="●" if v.get() else "○"))
            lbl.bind("<Button-1>", lambda e, i=idx, v=variables: self._set_dots(v, i))
            row.append(lbl)
        place_widgets([row])

    @staticmethod
    def _set_dots(variables: list[BooleanVar], clicked: int) -> None:
        filled = sum(v.get() for v in variables)
        threshold = clicked if filled == clicked + 1 else clicked + 1
        for i, var in enumerate(variables):
            var.set(i < threshold)