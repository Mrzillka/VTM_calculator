from __future__ import annotations

from tkinter import Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from config import WOUND_LEVELS
from ui.utils import frm, place_widgets

if TYPE_CHECKING:
    from ui.root import Root


class Interface(ttk.Frame):
    """
    Root widget of the application interface.

    Composes all child frames and delegates logic to the Root object.
    Toggle-able sections (trackers, additional options) are built once
    and shown/hidden via grid_remove() / grid() to avoid full redraws.
    """

    def __init__(self, root: "Root") -> None:
        super().__init__(root)
        self.root = root

        self._trackers_frame: ttk.Frame | None = None
        self._additional_row: list[Widget] = []
        self._sheet_window = None

        self._build()

    def _build(self) -> None:
        place_widgets([
            [self._frm_center()],
            [self._frm_bottom()],
        ])

    def refresh_blood_cells(self) -> None:
        """Re-evaluate which blood cells are active based on current blood_max_value."""
        self._disable_blood_cells()

    # ── Toggle handlers ───────────────────────────────────────────────────────

    def _toggle_trackers(self) -> None:
        if self._trackers_frame is None:
            return
        if self.root.trackers.get():
            self._trackers_frame.grid()
        else:
            self._trackers_frame.grid_remove()

    def _toggle_additional_options(self) -> None:
        if self.root.additional_options.get():
            for col_idx, widget in enumerate(self._additional_row):
                widget.grid(column=col_idx, row=4)
                widget.update()
        else:
            for widget in self._additional_row:
                widget.grid_remove()

    def _open_character_sheet(self) -> None:
        """Open or focus the character sheet window."""
        if self._sheet_window is not None and self._sheet_window.winfo_exists():
            self._sheet_window.lift()
            self._sheet_window.focus_force()
            return
        from ui.character_sheet import CharacterSheet
        self._sheet_window = CharacterSheet(self.root.character)

    # ── Center block ──────────────────────────────────────────────────────────

    @frm(padding=4, style="solid.TFrame")
    def _frm_center(self, frm: ttk.Frame) -> None:
        self._trackers_frame = self._frm_trackers(frm)
        widgets = [
            self._frm_main(frm),
            self._frm_results(frm),
            self._frm_sidebar(frm),
            self._trackers_frame,
        ]
        place_widgets([widgets])
        if not self.root.trackers.get():
            self._trackers_frame.grid_remove()

    @frm(padding=5)
    def _frm_main(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="VTM calculator", anchor="n", style="L.TLabel")],
            [self._frm_controls(frm)],
            [self._frm_main_buttons(frm)],
        ])

    @frm(padding=5)
    def _frm_controls(self, frm: ttk.Frame) -> None:
        root = self.root

        rows: list[list[Any]] = []

        rows.append([
            ttk.Label(frm, text="Number of dice:", width=12, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=1, to=15, length=125,
                      variable=root.dice_number, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.dice_number)),
            ttk.Spinbox(frm, from_=1, to=15, textvariable=root.dice_number,
                        width=3, style="my.TSpinbox"),
            ttk.Label(frm, textvariable=root.character.roll_penalty, width=3, style="S.TLabel"),
        ])

        rows.append([
            ttk.Label(frm, text="Difficulty:", width=12, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=2, to=10, length=125,
                      variable=root.difficulty, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.difficulty)),
            ttk.Spinbox(frm, from_=2, to=10, textvariable=root.difficulty,
                        width=3, style="my.TSpinbox"),
        ])

        rows.append([
            ttk.Label(frm, text="Auto success:", width=12, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=0, to=5, length=125,
                      variable=root.auto_success, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.auto_success)),
            ttk.Spinbox(frm, from_=0, to=5, textvariable=root.auto_success,
                        width=3, style="my.TSpinbox"),
        ])

        rows.append([
            ttk.Checkbutton(frm, text="Specialisation",
                            variable=root.specialisation, style="my.TCheckbutton"),
            ttk.Checkbutton(frm, text="Send to Telegram",
                            variable=root.is_send_to_telegram, style="my.TCheckbutton"),
            ttk.Checkbutton(frm, text="∨",
                            variable=root.additional_options,
                            command=self._toggle_additional_options,
                            style="my.TCheckbutton"),
        ])

        place_widgets(rows)

        self._additional_row = [
            ttk.Label(frm, text="Success needed:", width=12, style="M.TLabel", anchor="e"),
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
    def _frm_main_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([[
            ttk.Button(frm, text="Calculate & Roll!", style="L.TButton",
                       command=self.root.roll_and_calculate),
            ttk.Button(frm, text="Roll initiative", style="M.TButton",
                       command=self.root.roll_initiative),
        ]])

    @frm(padding=5)
    def _frm_results(self, frm: ttk.Frame) -> None:
        root = self.root
        place_widgets([
            [ttk.Label(frm, textvariable=root.result, width=14, anchor="center", style="L.TLabel")],
            [ttk.Label(frm, textvariable=root.roll_result_1, width=20, anchor="n", style="S.TLabel")],
            [ttk.Label(frm, textvariable=root.roll_result_2, width=20, anchor="n", style="S.TLabel")],
            [ttk.Label(frm, textvariable=root.roll_result_spec, width=20, anchor="n", style="S.TLabel")],
            [ttk.Label(frm, textvariable=root.successes, width=5, anchor="n", style="L.TLabel")],
            [ttk.Label(frm, textvariable=root.initiative, width=10, anchor="n", style="M.TLabel")],
        ])

    @frm(padding=5)
    def _frm_sidebar(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Checkbutton(frm, text="Trackers ►", variable=self.root.trackers,
                             command=self._toggle_trackers, style="my.TCheckbutton")],
            [ttk.Button(frm, text="Sheet", style="S.TButton",
                        command=self._open_character_sheet)],
        ])

    # ── Trackers ──────────────────────────────────────────────────────────────

    @frm(padding=5, style="solid.TFrame")
    def _frm_trackers(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._frm_blood_humanity_will(frm),
            self._frm_wounds(frm),
        ]])

    @frm(padding=5)
    def _frm_blood_humanity_will(self, frm: ttk.Frame) -> None:
        place_widgets([
            [self._frm_blood(frm)],
            [self._frm_humanity(frm)],
            [self._frm_will(frm)],
        ])

    @frm(padding=5)
    def _frm_blood(self, frm: ttk.Frame) -> None:
        cells_frm = self._frm_blood_cells(frm)
        self._disable_blood_cells()
        place_widgets([
            [ttk.Label(frm, text="Blood", width=12, anchor="n", style="M.TLabel")],
            [cells_frm],
            [self._frm_max_blood(frm)],
        ])

    @frm(padding=5)
    def _frm_blood_cells(self, frm: ttk.Frame) -> None:
        self._blood_cells: list[list[ttk.Checkbutton]] = []
        char = self.root.character

        for i in range(4):
            row_widgets = []
            for j in range(10):
                cell = ttk.Checkbutton(
                    frm,
                    variable=char.blood[i][j],
                    command=lambda r=i, c=j: char.set_blood(r, c),
                    style="my.TCheckbutton",
                )
                cell.grid(row=i, column=j)
                row_widgets.append(cell)
            self._blood_cells.append(row_widgets)

    def _disable_blood_cells(self) -> None:
        char = self.root.character
        max_blood = char.blood_max_value.get()
        for i, row in enumerate(self._blood_cells):
            for j, cell in enumerate(row):
                active = i * 10 + j < max_blood
                cell.configure(state="normal" if active else "disabled")
                if not active:
                    char.blood[i][j].set(False)
        if char.blood_value.get() > max_blood:
            char.blood_value.set(max_blood)
            char.set_blood(load=True)

    @frm(padding=5)
    def _frm_max_blood(self, frm: ttk.Frame) -> None:
        place_widgets([[
            ttk.Label(frm, text="Max Blood", width=12, anchor="n", style="S.TLabel"),
            ttk.Spinbox(
                frm, from_=1, to=40,
                textvariable=self.root.character.blood_max_value,
                command=self._disable_blood_cells,
                width=3, style="my.TSpinbox",
            ),
        ]])

    @frm(padding=5)
    def _frm_wounds(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [ttk.Label(frm, text="Wounds", width=12, anchor="n", style="M.TLabel")],
            [self._frm_wounds_cells(frm)],
            [ttk.Button(frm, text="HEAL", command=char.heal, style="M.TButton")],
        ])

    @frm(padding=5)
    def _frm_wounds_cells(self, frm: ttk.Frame) -> None:
        char = self.root.character
        rows = []
        for i, level in enumerate(WOUND_LEVELS):
            rows.append([
                ttk.Label(frm, text=level.name, width=10, anchor="e", style="S.TLabel"),
                ttk.Label(frm, text=str(level.penalty or ""), anchor="w", style="S.TLabel"),
                ttk.Checkbutton(frm, variable=char.wounds[i],
                                command=lambda y=i: char.set_wounds(y),
                                style="my.TCheckbutton"),
            ])
        place_widgets(rows)

    @frm(padding=5)
    def _frm_humanity(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [ttk.Label(frm, text="Humanity/Path", style="M.TLabel")],
            [self._frm_dot_tracker(frm, char.humanity, lambda x: char.set_humanity(x))],
        ])
        char.set_humanity(load=True)

    @frm(padding=5)
    def _frm_will(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [ttk.Label(frm, text="Will", style="M.TLabel")],
            [self._frm_dot_tracker(frm, char.will, lambda x: char.set_will(x))],
        ])
        char.set_will(load=True)

    @frm(padding=5)
    def _frm_dot_tracker(self, frm: ttk.Frame, variables: list, command) -> None:
        """Generic dot-tracker widget (Humanity, Will)."""
        labels = [ttk.Label(frm, text=str(i + 1), width=2, anchor="w", style="S.TLabel")
                  for i in range(10)]
        cells = [ttk.Checkbutton(frm, variable=variables[i],
                                 command=lambda x=i: command(x),
                                 style="my.TCheckbutton")
                 for i in range(10)]
        place_widgets([labels, cells])

    # ── Bottom block ──────────────────────────────────────────────────────────

    @frm(padding=5, style="solid.TFrame")
    def _frm_bottom(self, frm) -> None:
        char = self.root.character
        place_widgets([[
            self._frm_options(frm),
            self._frm_stat_label(frm, "Blood", char.blood_value),
            self._frm_stat_label(frm, "Wounds", char.wounds_value),
            self._frm_stat_label(frm, "Humanity", char.humanity_value),
            self._frm_stat_label(frm, "Will", char.will_value),
        ]])

    @frm(padding=5)
    def _frm_options(self, frm: ttk.Frame) -> None:
        place_widgets([[
            self._frm_name(frm),
            self._frm_initiative_spinboxes(frm),
            self._frm_action_buttons(frm),
        ]])

    @frm(padding=5)
    def _frm_name(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="Character name:", width=12, anchor="e", style="M.TLabel")],
            [ttk.Entry(frm, textvariable=self.root.character.character_name, width=15,
                       style="my.TEntry")],
        ])

    @frm(padding=5)
    def _frm_initiative_spinboxes(self, frm: ttk.Frame) -> None:
        char = self.root.character
        place_widgets([
            [ttk.Label(frm, text="Dex", width=5, anchor="e", style="S.TLabel"),
             ttk.Spinbox(frm, from_=0, to=10, textvariable=char.initiative_bonus_dex,
                         width=3, style="my.TSpinbox")],
            [ttk.Label(frm, text="Wits", width=5, anchor="e", style="S.TLabel"),
             ttk.Spinbox(frm, from_=0, to=10, textvariable=char.initiative_bonus_wits,
                         width=3, style="my.TSpinbox")],
        ])

    @frm(padding=5)
    def _frm_action_buttons(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Button(frm, textvariable=self.root.pooling_state,
                        command=self.root.start_bot_polling, style="S.TButton")],
            [ttk.Button(frm, text="Save",
                        command=self.root.save_to_file, style="S.TButton")],
        ])

    @frm(padding=5)
    def _frm_stat_label(self, frm: ttk.Frame, title: str, var) -> None:
        """Small widget for displaying a single numeric tracker value."""
        place_widgets([
            [ttk.Label(frm, text=title, style="M.TLabel")],
            [ttk.Label(frm, textvariable=var, style="S.TLabel")],
        ])