from __future__ import annotations

from tkinter import Widget, StringVar, BooleanVar
from tkinter import ttk
from typing import Any

from game.character import Character
from ui.utils import frm, place_widgets


class Interface(ttk.Frame):
    """

    """

    def __init__(self, root) -> None:
        super().__init__(root)
        self.root = root
        self.character = Character()

        self._build()

    def _build(self) -> None:
        place_widgets([
            [ttk.Label(self, text="Vampire the Masquerade", style="sheet.title.TLabel")],
            [self._frm_header()],
            [ttk.Label(self, text=' Attributes '.center(50, '—'), style='sheet.L.TLabel')],
            [self._frm_attributes()],
            [ttk.Label(self, text=' Abilities '.center(50, '—'), style='sheet.L.TLabel')],
            [self._frm_abilities()],
            [ttk.Label(self, text=' Advantages '.center(50, '—'), style='sheet.L.TLabel')],
            [self._frm_advantages()],
            [ttk.Label(self, text=''.center(50, '—'), style='sheet.L.TLabel')],
            [self._frm_bottom()]
        ])

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

        place_widgets([
            [self._frm_header_fields(frm, field_of_3) for field_of_3 in [left_fields, center_fields, right_fields]]
        ])

    @frm(padding=5)
    def _frm_header_fields(self, frm: ttk.Frame, field: list[tuple[str, StringVar]]) -> None:
        rows = [
            [self._frm_field(frm, label, var)] for label, var in field
        ]
        place_widgets(rows)

    @frm(padding=3)
    def _frm_field(self, frm: ttk.Frame, label: str, var: StringVar) -> None:
        place_widgets([
            [
                ttk.Label(frm, text=label, width=10, anchor='e', style="sheet.S.TLabel"),
                ttk.Entry(frm, textvariable=var, width=20, style="sheet.TEntry"),
            ]
        ])

    @frm(padding=5)
    def _frm_attributes(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text=name, style="sheet.M.TLabel")
             for name, attribute in self.character.attributes.items()],
            [self._frm_attributes_content(frm, attribute)
             for name, attribute in self.character.attributes.items()]
        ])

    @frm(padding=0)
    def _frm_attributes_content(self, frm: ttk.Frame,
                                attribute: dict[str, dict[str, StringVar | list[BooleanVar]]]) -> None:
        place_widgets([
            [self._frm_line(frm, label, variables=values['vars'], spec_var=values['spec'])]
            for label, values in attribute.items()
        ])

    @frm(padding=5)
    def _frm_abilities(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text=name, style="sheet.M.TLabel")
             for name, ability in self.character.abilities.items()],
            [self._frm_abilities_content(frm, attribute)
             for name, attribute in self.character.abilities.items()]
        ])

    @frm(padding=0)
    def _frm_abilities_content(self, frm: ttk.Frame,
                               ability: dict[str, dict[str, StringVar | list[BooleanVar]]]) -> None:
        place_widgets([
            [self._frm_line(frm, label, variables=values['vars'], spec_var=values['spec'])]
            for label, values in ability.items()
        ])

    @frm(padding=5)
    def _frm_advantages(self, frm: ttk.Frame) -> None:
        pass

    @frm(padding=5)
    def _frm_bottom(self, frm: ttk.Frame) -> None:
        pass

    @frm(padding=0)
    def _frm_line(self, frm: ttk.Frame,
                  label: str, variables: list[BooleanVar], spec_var: StringVar,
                  fillable: bool = False, label_custom: StringVar | None = None) -> None:
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
                cursor="hand2"
            )
            row.append(lbl)
            var.trace_add(
                'write',
                lambda *_, l=lbl, v=var: l.configure(text="●" if v.get() else "○")
            )
            lbl.bind(
                '<Button-1>',
                lambda e, i=idx, v=variables: self._set_dots(v, i),
            )
        place_widgets([row])

    @staticmethod
    def _set_dots(variables: list[BooleanVar], clicked: int) -> None:
        filled = sum(v.get() for v in variables)
        threshold = clicked if filled == clicked + 1 else clicked + 1
        for i, var in enumerate(variables):
            var.set(True if i < threshold else False)
