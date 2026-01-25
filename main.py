from itertools import combinations_with_replacement
from random import randint
from tkinter import *
from tkinter import ttk
from typing import Tuple, List


class Root(Tk):
    # TODO: add statistics
    # TODO: add specialisations
    def __init__(self):
        super().__init__()
        self.width, self.height, self.font_size = 100, 100, 10
        self.geometry(f"{self.width}x{self.height}")
        self.title('VTM calculator')

        self.scale = 1

        self.dice_number = IntVar(value=1)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success = IntVar(value=0)
        self.additional_options = BooleanVar(value=False)

        self.result = StringVar(value='0.00%')
        self.roll_result = []
        self.roll_result_1 = StringVar(value="[]")
        self.roll_result_2 = StringVar(value="")
        self.roll_result_3 = StringVar(value="")
        self.successes = StringVar(value="0")

        self.styles = {
            "first.TFrame": ttk.Style(),
            "second.TFrame": ttk.Style(),
            "third.TFrame": ttk.Style(),
            "my.TButton": ttk.Style(),
            "my.Horizontal.TScale": ttk.Style(),
            "my.TSpinbox": ttk.Style(),
            "my.TCheckbutton": ttk.Style(),
            "L.TLabel": ttk.Style(),
            "M.TLabel": ttk.Style(),
            "S.TLabel": ttk.Style(),
        }
        self.styles_configure()

        self.interface()

        self.width = sum(frm.winfo_width() for frm in self.winfo_children()) + 10 * 3
        self.height = max(frm.winfo_height() for frm in self.winfo_children()) + 10

        self.redraw_interface()

    def styles_configure(self):
        # TODO: test styles functionality
        self.styles["first.TFrame"].configure("first.TFrame", background='#A0A0A0')
        self.styles["second.TFrame"].configure("second.TFrame", background='#000000')
        self.styles["third.TFrame"].configure("third.TFrame", background='#A0A0A0')
        self.styles["my.TButton"].configure("my.TButton", font=("Javanese text", int(self.font_size * 1.5)),
                                            padding=3 * self.scale, )
        self.styles["my.Horizontal.TScale"].configure("my.Horizontal.TScale", font=("Javanese text", self.font_size),
                                                      padding=3 * self.scale, )
        self.styles["my.TSpinbox"].configure("my.TSpinbox", font=("Javanese text", self.font_size),
                                             padding=3 * self.scale, )
        self.styles["my.TCheckbutton"].configure("my.TCheckbutton", font=("Javanese text", self.font_size),
                                                 padding=3 * self.scale)
        self.styles["L.TLabel"].configure("L.TLabel", font=("Javanese text", self.font_size * 2),
                                          padding=3 * self.scale)
        self.styles["M.TLabel"].configure("M.TLabel", font=("Javanese text", int(self.font_size * 1.5)),
                                          padding=3 * self.scale)
        self.styles["S.TLabel"].configure("S.TLabel", font=("Javanese text", self.font_size), padding=3 * self.scale)

    def redraw_interface(self):
        for widget in self.winfo_children():
            widget.destroy()
        additional_width = 0
        additional_height = 0
        if self.additional_options.get():
            additional_height = 100

        self.geometry(f"{self.width * self.scale}x{self.height * self.scale + additional_height * self.scale}")
        self.grid_columnconfigure(0, pad=10)
        self.grid_columnconfigure(1, pad=10)
        self.grid_columnconfigure(2, pad=10)
        self.grid_rowconfigure(0, pad=10)

        self.interface()

    def scale_up(self, up=True) -> None:
        if up:
            if self.scale < 4:
                self.scale += 1
                self.font_size *= 2
        else:
            if self.scale > 1:
                self.scale -= 1
                self.font_size //= 2

        self.styles_configure()
        self.redraw_interface()

    def calculate(self) -> None:
        calculator = Calculator(self.dice_number.get(), self.difficulty.get(), self.success_needed.get())
        self.result.set(f'Chance: {calculator.get_result():.2f}%')

    def roll(self) -> None:
        roller = Roller(self.dice_number.get(), self.difficulty.get(), self.auto_success.get())
        roll, successes = roller.get_result()
        self.roll_result = roll
        self.set_roll_result_placement()
        self.successes.set(f"{successes}")

    def roll_and_calculate(self) -> None:
        self.calculate()
        self.roll()

    def set_roll_result_placement(self) -> None:
        self.roll_result_1.set(f'{self.roll_result[:8]}')
        self.roll_result_2.set(f'{self.roll_result[8:]}')

    @staticmethod
    def scaler(s, var) -> None:
        var.set(int(float(s)))

    @staticmethod
    def place_widgets(lst: list[list[Widget]]) -> None:
        for y in range(len(lst)):
            for x in range(len(lst[y])):
                lst[y][x].update()
                lst[y][x].grid(column=x, row=y)

    def interface(self) -> None:
        # 3 main frames
        frm_main = ttk.Frame(self, padding=10, style='first.TFrame')
        frm_results = ttk.Frame(self, padding=10, style='first.TFrame')
        frm_scale = ttk.Frame(self, padding=10, style='first.TFrame')

        # frm_main
        lbl_title = ttk.Label(frm_main, text='VTM calculator', anchor='n', style='L.TLabel')
        frm_controls = ttk.Frame(frm_main, padding=10, style="first.TFrame")
        btn_calkulate = ttk.Button(frm_main, text='Calculate & Roll!', style="my.TButton",
                                   command=self.roll_and_calculate)
        frm_main_placement = [[lbl_title],
                              [frm_controls],
                              [btn_calkulate]]

        # frm_main -> frm_controls
        lbl1 = ttk.Label(frm_controls, text="Number of dice:", width=12, style="M.TLabel", anchor='e')
        scale_1 = ttk.Scale(frm_controls,
                            from_=1,
                            to=15,
                            length=125 * self.scale,
                            variable=self.dice_number,
                            style="my.Horizontal.TScale",
                            command=lambda s: self.scaler(s, self.dice_number))
        spinbox_1 = ttk.Spinbox(frm_controls,
                                from_=1,
                                to=15,
                                textvariable=self.dice_number,
                                width=3,
                                style="my.TSpinbox")
        lbl2 = ttk.Label(frm_controls, text="Difficulty:", width=12, style="M.TLabel", anchor='e')
        scale_2 = ttk.Scale(frm_controls,
                            from_=2,
                            to=10,
                            length=125 * self.scale,
                            variable=self.difficulty,
                            style="my.Horizontal.TScale",
                            command=lambda s: self.scaler(s, self.difficulty))
        spinbox_2 = ttk.Spinbox(frm_controls,
                                from_=2,
                                to=10,
                                textvariable=self.difficulty,
                                width=3,
                                style="my.TSpinbox")
        chk_box = ttk.Checkbutton(frm_controls,
                                  text="Additional options",
                                  variable=self.additional_options,
                                  command=self.redraw_interface,
                                  style="my.TCheckbutton")
        frm_controls_placement = [[lbl1, scale_1, spinbox_1],
                                  [lbl2, scale_2, spinbox_2],
                                  [chk_box]]

        if self.additional_options.get():
            lbl3 = ttk.Label(frm_controls, text="Success needed:", width=12, style="M.TLabel", anchor='e')
            scale_3 = ttk.Scale(frm_controls,
                                from_=1,
                                to=10,
                                length=125 * self.scale,
                                variable=self.success_needed,
                                style="my.Horizontal.TScale",
                                command=lambda s: self.scaler(s, self.success_needed))
            spinbox_3 = ttk.Spinbox(frm_controls,
                                    from_=1,
                                    to=10,
                                    textvariable=self.success_needed,
                                    width=3,
                                    style="my.TSpinbox")
            frm_controls_placement.append([lbl3, scale_3, spinbox_3])
            lbl4 = ttk.Label(frm_controls, text="Auto success:", width=12, style="M.TLabel", anchor='e')
            scale_4 = ttk.Scale(frm_controls,
                                from_=0,
                                to=5,
                                length=125 * self.scale,
                                variable=self.auto_success,
                                style="my.Horizontal.TScale",
                                command=lambda s: self.scaler(s, self.auto_success))
            spinbox_4 = ttk.Spinbox(frm_controls,
                                    from_=0,
                                    to=5,
                                    textvariable=self.auto_success,
                                    width=3,
                                    style="my.TSpinbox")
            frm_controls_placement.append([lbl4, scale_4, spinbox_4])

        # frm_result
        lbl_result_calc = ttk.Label(frm_results, textvariable=self.result, style="L.TLabel", width=15, anchor="center")
        lbl_result_roll_1 = ttk.Label(frm_results,
                                      textvariable=self.roll_result_1,
                                      style="S.TLabel",
                                      width=20,
                                      anchor="n")
        lbl_result_roll_2 = ttk.Label(frm_results,
                                      textvariable=self.roll_result_2,
                                      style="S.TLabel",
                                      width=20,
                                      anchor="n")
        lbl_successes = ttk.Label(frm_results,
                                  textvariable=self.successes,
                                  style="L.TLabel",
                                  width=5,
                                  anchor='n')
        frm_results_placement = [[lbl_result_calc],
                                 [lbl_result_roll_1],
                                 [lbl_result_roll_2],
                                 [lbl_successes]]

        # frm_scale
        btn_plus = ttk.Button(frm_scale, width=2 * self.scale, text='+', style='my.TButton',
                              command=lambda: self.scale_up(True))
        btn_minus = ttk.Button(frm_scale, width=2 * self.scale, text='-', style='my.TButton',
                               command=lambda: self.scale_up(False))
        frm_scale_placement = [[btn_plus],
                               [btn_minus]]

        root_placement = [[frm_main, frm_results, frm_scale]]

        for obj in (root_placement, frm_main_placement, frm_results_placement, frm_controls_placement,
                    frm_scale_placement):
            self.place_widgets(obj)


class Calculator:
    def __init__(self, dice_number: int = 1, difficulty: int = 6, success_needed: int = 1, auto_successes: int = 0):
        self.dice_number = dice_number
        self.difficulty = difficulty
        self.success_needed = success_needed
        self.auto_successes = auto_successes

    def get_product(self) -> list[tuple[int, ...]]:
        return list(combinations_with_replacement(range(1, 10 + 1), self.dice_number))

    def run(self, prod: list[tuple[int, ...]]) -> list[bool]:
        return [
            [i >= self.difficulty for i in lst].count(True) - lst.count(1) + self.auto_successes >= self.success_needed
            for lst in
            prod]

    def get_result(self) -> float:
        result = self.run(self.get_product())
        return result.count(True) / len(result) * 100


class Roller:
    def __init__(self, dice_number: int = 1, difficulty: int = 6, auto_success: int = 0):
        self.dice_number, self.difficulty, self.auto_success = dice_number, difficulty, auto_success

    def get_result(self) -> Tuple[List[int], int]:
        roll = [randint(1, 10) for _ in range(self.dice_number)]
        successes = len([1 for d in roll if d >= self.difficulty]) + self.auto_success
        failures = roll.count(1)
        successes -= failures
        return roll, successes


if __name__ == '__main__':
    root = Root()
    root.mainloop()
