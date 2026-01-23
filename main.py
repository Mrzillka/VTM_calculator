from itertools import combinations_with_replacement
from random import randint
from tkinter import *
from tkinter import ttk
from tkinter.font import Font


class Root(Tk):
    def __init__(self):
        super().__init__()
        self.width, self.height, self.font_size = 775, 350, 10
        self.geometry(f"{self.width}x{self.height}")
        self.title('VTM calculator')

        self.scale = 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.dice_number = IntVar(value=1)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)

        self.result = StringVar(value='0.00%')
        self.roll_result = []
        self.roll_result_1 = StringVar(value="[]")
        self.roll_result_2 = StringVar(value="")
        self.roll_result_3 = StringVar(value="")
        self.successes = StringVar(value="0")

        self.styles = {
            "my.TButton": ttk.Style(),
            "my.Horizontal.TScale": ttk.Style(),
            "my.TSpinbox": ttk.Style(),
            "L.TLabel": ttk.Style(),
            "M.TLabel": ttk.Style(),
            "S.TLabel": ttk.Style(),
        }
        self.styles_configure()

        self.interface()

    def styles_configure(self):
        self.styles["my.TButton"].configure("my.TButton", font=("Javanese text", int(self.font_size * 1.5)),
                                            padding=3 * self.scale, )
        self.styles["my.Horizontal.TScale"].configure("my.Horizontal.TScale", font=("Javanese text", self.font_size),
                                                      padding=3 * self.scale, )
        self.styles["my.TSpinbox"].configure("my.TSpinbox", font=("Javanese text", self.font_size),
                                             padding=3 * self.scale, )
        self.styles["L.TLabel"].configure("L.TLabel", font=("Javanese text", self.font_size * 2),
                                          padding=3 * self.scale)
        self.styles["M.TLabel"].configure("M.TLabel", font=("Javanese text", int(self.font_size * 1.5)),
                                          padding=3 * self.scale)
        self.styles["S.TLabel"].configure("S.TLabel", font=("Javanese text", self.font_size), padding=3 * self.scale)

    def scale_up(self, up=True):
        if up:
            if self.scale < 4:
                self.scale += 1
                self.width *= 2
                self.height *= 2
                self.font_size *= 2
        else:
            if self.scale > 1:
                self.scale -= 1
                self.width //= 2
                self.height //= 2
                self.font_size //= 2
        self.geometry(f"{self.width}x{self.height}")
        self.styles_configure()

        for widget in self.winfo_children():
            widget.destroy()
        self.interface()

    def calculate(self):
        calculator = Calculator(self.dice_number.get(), self.difficulty.get(), self.success_needed.get())
        self.result.set(f'Chance: {calculator.get_result():.2f}%')

    def roll(self):
        roller = Roller(self.dice_number.get(), self.difficulty.get())
        roll, successes = roller.get_result()
        self.roll_result = roll
        self.set_roll_result_placement()
        self.successes.set(f"{successes}")

    def set_roll_result_placement(self):
        self.roll_result_1.set(f'{self.roll_result[:8]}')
        self.roll_result_2.set(f'{self.roll_result[8:]}')

    def roll_and_calculate(self):
        self.calculate()
        self.roll()

    def scaler(self, s, var):
        var.set(int(float(s)))

    @staticmethod
    def place_widgets(lst: list[list[Widget]]) -> None:
        for y in range(len(lst)):
            for x in range(len(lst[y])):
                lst[y][x].grid(column=x, row=y)

    def interface(self):
        frm_main = ttk.Frame(self, padding=20)
        lbl_title = ttk.Label(frm_main, text='VTM calculator', style='L.TLabel')
        frm1 = ttk.Frame(frm_main, padding=10)
        btn_calkulate = ttk.Button(frm_main, text='Calculate & Roll!', width=20 * self.scale, style="my.TButton",
                                   command=self.roll_and_calculate)

        frm_main_placement = [[lbl_title],
                              [frm1],
                              [btn_calkulate]]

        frm_results = ttk.Frame(self, padding=10)
        lbl_result_calc = ttk.Label(frm_results,
                                    textvariable=self.result,
                                    style="L.TLabel",
                                    width=15, anchor="center")
        lbl_result_roll_1 = ttk.Label(frm_results,
                                      textvariable=self.roll_result_1,
                                      style="S.TLabel",
                                      width=30,
                                      anchor="n")
        lbl_result_roll_2 = ttk.Label(frm_results,
                                      textvariable=self.roll_result_2,
                                      style="S.TLabel",
                                      width=30,
                                      anchor="n")
        lbl_successes = ttk.Label(frm_results,
                                  textvariable=self.successes,
                                  style="L.TLabel",
                                  width=15,
                                  anchor='n')
        frm_results_placement = [[lbl_result_calc],
                                 [lbl_result_roll_1],
                                 [lbl_result_roll_2],
                                 [lbl_successes]]

        frm_scale = ttk.Frame(self, padding=10)
        btn_plus = ttk.Button(frm_scale, width=1 * self.scale, text='+', style='my.TButton',
                              command=lambda: self.scale_up(True))
        btn_minus = ttk.Button(frm_scale, width=1 * self.scale, text='-', style='my.TButton',
                               command=lambda: self.scale_up(False))
        frm_scale_placement = [[btn_plus],
                               [btn_minus]]

        root_placement = [[frm_main, frm_results, frm_scale]]

        lbl1 = ttk.Label(frm1, text="Number of dice:", width=15, style="M.TLabel", anchor='e')
        lbl2 = ttk.Label(frm1, text="Difficulty:", width=15, style="M.TLabel", anchor='e')
        lbl3 = ttk.Label(frm1, text="Success needed:", width=15, style="M.TLabel", anchor='e')

        scale_1 = ttk.Scale(frm1,
                            from_=1,
                            to=15,
                            length=125 * self.scale,
                            variable=self.dice_number,
                            command=lambda s: self.scaler(s, self.dice_number))
        spinbox_1 = ttk.Spinbox(frm1,
                                from_=1,
                                to=15,
                                textvariable=self.dice_number,
                                width=3,
                                font=Font(size=self.font_size))
        scale_2 = ttk.Scale(frm1,
                            from_=2,
                            to=10,
                            length=125 * self.scale,
                            variable=self.difficulty,
                            command=lambda s: self.scaler(s, self.difficulty))
        spinbox_2 = ttk.Spinbox(frm1,
                                from_=2,
                                to=10,
                                textvariable=self.difficulty,
                                width=3,
                                font=Font(size=self.font_size))
        scale_3 = ttk.Scale(frm1,
                            from_=1,
                            to=10,
                            length=175 * self.scale,
                            variable=self.success_needed,
                            command=lambda s: self.scaler(s, self.success_needed))
        spinbox_3 = ttk.Spinbox(frm1,
                                from_=1,
                                to=10,
                                textvariable=self.success_needed,
                                width=3,
                                font=Font(size=self.font_size))
        frm1_placement = [[lbl1, scale_1, spinbox_1],
                          [lbl2, scale_2, spinbox_2],
                          [lbl3, scale_3, spinbox_3]]

        for obj in (root_placement, frm_main_placement, frm_results_placement, frm1_placement, frm_scale_placement):
            self.place_widgets(obj)


class Calculator:
    def __init__(self, dice_number: int = 1, difficulty: int = 6, success_needed: int = 1):
        self.dice_number, self.difficulty, self.success_needed = dice_number, difficulty, success_needed

    def get_product(self) -> list[tuple[int, ...]]:
        return list(combinations_with_replacement(range(1, 10 + 1), self.dice_number))

    def run(self, prod: list[tuple[int, ...]]) -> list[bool]:
        return [[i >= self.difficulty for i in lst].count(True) - lst.count(1) >= self.success_needed for lst in prod]

    def get_result(self) -> float:
        result = self.run(self.get_product())
        return result.count(True) / len(result) * 100


class Roller:
    def __init__(self, dice_number: int = 1, difficulty: int = 6):
        self.dice_number, self.difficulty = dice_number, difficulty

    def get_result(self):
        roll = [randint(1, 10) for _ in range(self.dice_number)]
        successes = len([1 for d in roll if d >= self.difficulty])
        failures = roll.count(1)
        successes -= failures
        return roll, successes


root = Root()
root.mainloop()
