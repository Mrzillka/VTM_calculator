from __future__ import annotations

from tkinter import BooleanVar, StringVar
from tkinter import ttk
from typing import Callable

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
        attrs = self._frm_attributes()
        abilities = self._frm_abilities()
        advantages = self._frm_advantages()
        bottom = self._frm_bottom()

        place_widgets([
            [ttk.Label(self, text="Vampire the Masquerade", style="sheet.title.TLabel")],
            [self._frm_header()],
            [self._section_header("Attributes", attrs)],
            [attrs],
            [self._section_header("Abilities", abilities)],
            [abilities],
            [self._section_header("Advantages", advantages)],
            [advantages],
            [ttk.Label(self, text="─" * 50, style="sheet.L.TLabel")],
            [bottom],
        ])

    def _section_header(self, title: str, content: ttk.Frame) -> ttk.Label:
        """Return a clickable label that toggles the visibility of *content*."""
        state = BooleanVar(value=True)
        lbl = ttk.Label(self, style="sheet.L.TLabel", cursor="hand2")

        def _refresh() -> None:
            lbl.configure(text=f"{'▼' if state.get() else '►'}  {title}")

        def _toggle(e=None) -> None:
            state.set(not state.get())
            _refresh()
            if state.get():
                content.grid()
            else:
                content.grid_remove()

        _refresh()
        lbl.bind("<Button-1>", _toggle)
        return lbl

    @staticmethod
    def _make_sub_toggle(
        lbl: ttk.Label,
        content: ttk.Frame,
        title: str,
        state: BooleanVar,
    ) -> Callable:
        """Return a click handler that toggles a sub-section column."""
        def _toggle(e=None) -> None:
            state.set(not state.get())
            lbl.configure(text=f"{'▼' if state.get() else '►'} {title}")
            if state.get():
                content.grid()
            else:
                content.grid_remove()
        return _toggle

    # ── Header ───────────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_header(self, frm: ttk.Frame) -> None:
        left_fields = [
            ("Name", self.character.character_name),
            ("Player", self.character.player),
            ("Chronicle", self.character.chronicle),
        ]
        center_fields = [
            ("Nature", self.character.nature),
            ("Demeanor", self.character.demeanor),
            ("Clan", self.character.clan),
        ]
        right_fields = [
            ("Generation", self.character.generation),
            ("Heaven", self.character.heaven),
            ("Concept", self.character.concept),
        ]
        place_widgets([[
            self._frm_header_fields(frm, group)
            for group in [left_fields, center_fields, right_fields]
        ]])

    @frm(padding=5)
    def _frm_header_fields(self, frm: ttk.Frame, fields: list[tuple[str, StringVar]]) -> None:
        place_widgets([[self._frm_field(frm, label, var)] for label, var in fields])

    @frm(padding=3)
    def _frm_field(self, frm: ttk.Frame, label: str, var: StringVar) -> None:
        place_widgets([[
            ttk.Label(frm, text=label, width=10, anchor="e", style="sheet.S.TLabel"),
            ttk.Entry(frm, textvariable=var, width=20, style="sheet.TEntry"),
        ]])

    # ── Attributes ───────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_attributes(self, frm: ttk.Frame) -> None:
        for col_idx, (cat_name, cat_data) in enumerate(self.character.attributes.items()):
            state = BooleanVar(value=True)
            content = self._frm_stat_lines(frm, cat_data)
            header = ttk.Label(
                frm, text=f"▼ {cat_name}", style="sheet.M.TLabel", cursor="hand2",
            )
            header.bind("<Button-1>", self._make_sub_toggle(header, content, cat_name, state))
            header.grid(row=0, column=col_idx, sticky="w", padx=5, pady=(0, 2))
            content.grid(row=1, column=col_idx, sticky="n", padx=5)

    # ── Abilities ────────────────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_abilities(self, frm: ttk.Frame) -> None:
        for col_idx, (cat_name, cat_data) in enumerate(self.character.abilities.items()):
            state = BooleanVar(value=True)
            content = self._frm_stat_lines(frm, cat_data)
            header = ttk.Label(
                frm, text=f"▼ {cat_name}", style="sheet.M.TLabel", cursor="hand2",
            )
            header.bind("<Button-1>", self._make_sub_toggle(header, content, cat_name, state))
            header.grid(row=0, column=col_idx, sticky="w", padx=5, pady=(0, 2))
            content.grid(row=1, column=col_idx, sticky="n", padx=5)

    @frm(padding=0)
    def _frm_stat_lines(
        self,
        frm: ttk.Frame,
        data: dict[str, dict[str, StringVar | list[BooleanVar]]],
    ) -> None:
        place_widgets([
            [self._frm_line(frm, label, variables=values["vars"], spec_var=values["spec"])]
            for label, values in data.items()
        ])

    # ── Advantages / Bottom ──────────────────────────────────────────────────

    @frm(padding=5)
    def _frm_advantages(self, frm: ttk.Frame) -> None:
        pass

    @frm(padding=5)
    def _frm_bottom(self, frm: ttk.Frame) -> None:
        pass

    # ── Shared stat-line widget ──────────────────────────────────────────────

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
        place_widgets([[
            ttk.Label(frm, text=label, width=10, style="sheet.S.TLabel")
            if not fillable else
            ttk.Entry(frm, textvariable=label_custom, width=10, style="sheet.TEntry"),
            ttk.Entry(frm, textvariable=spec_var, width=15, style="sheet.TEntry"),
            self._frm_dots(frm, variables),
        ]])

    @frm(padding=5)
    def _frm_dots(self, frm: ttk.Frame, variables: list[BooleanVar]) -> None:
        row = []
        for idx, var in enumerate(variables):
            lbl = ttk.Label(
                frm,
                text="●" if var.get() else "○",
                style="sheet.Dot.TLabel",
                cursor="hand2",
            )
            row.append(lbl)
            var.trace_add(
                "write",
                lambda *_, l=lbl, v=var: l.configure(text="●" if v.get() else "○"),
            )
            lbl.bind("<Button-1>", lambda e, i=idx, v=variables: self._set_dots(v, i))
        place_widgets([row])

    @staticmethod
    def _set_dots(variables: list[BooleanVar], clicked: int) -> None:
        filled = sum(v.get() for v in variables)
        threshold = clicked if filled == clicked + 1 else clicked + 1
        for i, var in enumerate(variables):
            var.set(i < threshold)