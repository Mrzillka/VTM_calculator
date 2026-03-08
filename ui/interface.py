from __future__ import annotations

from functools import wraps
from tkinter import Widget
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Callable

from config import WOUND_LEVELS

if TYPE_CHECKING:
    from ui.root import Root


# ── Utilities ─────────────────────────────────────────────────────────────────

def place_widgets(grid: list[list[Widget | None]]) -> None:
    """Place widgets in a grid layout (row=y, column=x)."""
    for row_idx, row in enumerate(grid):
        for col_idx, widget in enumerate(row):
            widget.grid(column=col_idx, row=row_idx)
            widget.update()


def frm(padding: int = 5, style: str = "my.TFrame", *args, **kwargs) -> Callable:
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self: "Interface", parent: ttk.Frame | None = None, *args, **kwargs) -> ttk.Frame:
            frame = ttk.Frame(parent if parent is not None else self,
                              padding=padding, style=style)
            method(self, frame, *args, **kwargs)
            return frame
        return wrapper
    return decorator


# ── Interface ─────────────────────────────────────────────────────────────────

class Interface(ttk.Frame):
    """
    Root widget of the application interface.

    Composes all child frames and delegates logic to the Root object.
    Toggle-able sections (trackers, additional options) are built once
    and shown/hidden via grid_remove() / grid() to avoid full redraws.
    """

    def __init__(self, root: Root) -> None:
        super().__init__(root)
        self.root = root

        # References to toggle-able widgets
        self._trackers_frame: ttk.Frame | None = None
        self._additional_row: list[Widget] = []

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
        """Show or hide the trackers panel without rebuilding it."""
        if self._trackers_frame is None:
            return
        if self.root.trackers.get():
            self._trackers_frame.grid()
        else:
            self._trackers_frame.grid_remove()

    def _toggle_additional_options(self) -> None:
        """Show or hide the 'Success needed' row without rebuilding it."""
        if self.root.additional_options.get():
            for col_idx, widget in enumerate(self._additional_row):
                widget.grid(column=col_idx, row=4)
                widget.update()
        else:
            for widget in self._additional_row:
                widget.grid_remove()

    # ── Center block ──────────────────────────────────────────────────────────

    @frm(padding=4, style='solid.TFrame')
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
            ttk.Label(frm, textvariable=root.roll_penalty, width=3, style="S.TLabel"),
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

        # Always build the additional row; show or hide based on current state.
        self._additional_row = [
            ttk.Label(frm, text="Success needed:", width=12, style="M.TLabel", anchor="e"),
            ttk.Scale(frm, from_=1, to=10, length=125,
                      variable=root.success_needed, style="my.Horizontal.TScale",
                      command=lambda s: root.scaler(s, root.success_needed)),
            ttk.Spinbox(frm, from_=1, to=10, textvariable=root.success_needed,
                        width=3, style="my.TSpinbox"),
        ]
        # Place at row 4 first so tkinter knows the grid position, then hide if needed.
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
        ])

    @frm(padding=5, style='solid.TFrame')
    def _frm_trackers(self, frm: ttk.Frame) -> None:
        """Tracker panel — always built, visibility controlled externally."""
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

        for i in range(4):
            row_widgets = []
            for j in range(10):
                cell = ttk.Checkbutton(
                    frm,
                    variable=self.root.blood[i][j],
                    command=lambda r=i, c=j: self.root.set_blood(r, c),
                    style="my.TCheckbutton",
                )
                cell.grid(row=i, column=j)
                row_widgets.append(cell)
            self._blood_cells.append(row_widgets)

    def _disable_blood_cells(self) -> None:
        max_blood = self.root.blood_max_value.get()
        for i, row in enumerate(self._blood_cells):
            for j, cell in enumerate(row):
                active = i * 10 + j < max_blood
                cell.configure(state="normal" if active else "disabled")
                if not active:
                    self.root.blood[i][j].set(False)
        if self.root.blood_value.get() > max_blood:
            self.root.blood_value.set(max_blood)
            self.root.set_blood(load=True)

    @frm(padding=5)
    def _frm_max_blood(self, frm: ttk.Frame) -> None:
        place_widgets([[
            ttk.Label(frm, text="Max Blood", width=12, anchor="n", style="S.TLabel"),
            ttk.Spinbox(
                frm, from_=1, to=40,
                textvariable=self.root.blood_max_value,
                command=self._disable_blood_cells,
                width=3, style="my.TSpinbox",
            ),
        ]])

    @frm(padding=5)
    def _frm_wounds(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="Wounds", width=12, anchor="n", style="M.TLabel")],
            [self._frm_wounds_cells(frm)],
            [ttk.Button(frm, text="HEAL", command=self.root.heal, style="M.TButton")],
        ])

    @frm(padding=5)
    def _frm_wounds_cells(self, frm: ttk.Frame) -> None:
        rows = []
        for i, level in enumerate(WOUND_LEVELS):
            rows.append([
                ttk.Label(frm, text=level.name, width=10, anchor="e", style="S.TLabel"),
                ttk.Label(frm, text=str(level.penalty or ""), anchor="w", style="S.TLabel"),
                ttk.Checkbutton(frm, variable=self.root.wounds[i],
                                command=lambda y=i: self.root.set_wounds(y),
                                style="my.TCheckbutton"),
            ])
        place_widgets(rows)

    @frm(padding=5)
    def _frm_humanity(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="Humanity/Path", style="M.TLabel")],
            [self._frm_dot_tracker(frm, self.root.humanity,
                                   lambda x: self.root.set_humanity(x))],
        ])
        self.root.set_humanity(load=True)

    @frm(padding=5)
    def _frm_will(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="Will", style="M.TLabel")],
            [self._frm_dot_tracker(frm, self.root.will,
                                   lambda x: self.root.set_will(x))],
        ])
        self.root.set_will(load=True)

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

    @frm(padding=5, style='solid.TFrame')
    def _frm_bottom(self, frm) -> None:
        place_widgets([[
            self._frm_options(frm),
            self._frm_stat_label(frm, "Blood", self.root.blood_value),
            self._frm_stat_label(frm, "Wounds", self.root.wounds_value),
            self._frm_stat_label(frm, "Humanity", self.root.humanity_value),
            self._frm_stat_label(frm, "Will", self.root.will_value),
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
            [ttk.Entry(frm, textvariable=self.root.name, width=15,
                       style="my.TEntry")],
        ])

    @frm(padding=5)
    def _frm_initiative_spinboxes(self, frm: ttk.Frame) -> None:
        place_widgets([
            [ttk.Label(frm, text="Dex", width=5, anchor="e", style="S.TLabel"),
             ttk.Spinbox(frm, from_=0, to=10, textvariable=self.root.initiative_bonus_dex,
                         width=3, style="my.TSpinbox")],
            [ttk.Label(frm, text="Wits", width=5, anchor="e", style="S.TLabel"),
             ttk.Spinbox(frm, from_=0, to=10, textvariable=self.root.initiative_bonus_wits,
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
