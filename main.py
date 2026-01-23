from itertools import combinations_with_replacement
from random import randint
from tkinter import *
from tkinter import ttk
from tkinter.font import Font


class Root(Tk):
    def __init__(self):
        super().__init__()
        self.width, self.height, self.font_size = 500, 200, 10
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
        self.roll_result_4 = StringVar(value="")
        self.successes = StringVar(value="0")

        self.interface()

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
        for widget in self.winfo_children():
            widget.destroy()
        self.interface()

    def calculate(self):
        calculator = Calculator(self.dice_number.get(), self.difficulty.get(), self.success_needed.get())
        self.result.set(f'{calculator.get_result():.2f}%')

    def roll(self):
        roller = Roller(self.dice_number.get(), self.difficulty.get())
        roll, successes = roller.get_result()
        self.roll_result = roll
        self.set_roll_result_placement()
        self.successes.set(f"{successes}")

    def set_roll_result_placement(self):
        self.roll_result_1.set(f'{self.roll_result[:5]}')
        self.roll_result_2.set(f'{self.roll_result[5:10]}')
        self.roll_result_3.set(f'{self.roll_result[10:15]}')
        self.roll_result_4.set(f'{self.roll_result[15:]}')

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
        lbl_title = ttk.Label(frm_main, text='VTM calculator', font=Font(size=int(self.font_size * 1)))
        frm1 = ttk.Frame(frm_main, padding=10)
        btn_calkulate = ttk.Button(frm_main, text='Calculate & Roll!', width=20 * self.scale,
                                   # font=Font(size=int(self.font_size * 1)),
                                   command=self.roll_and_calculate)
        # btn_calkulate = ttk.Button(frm_main, text='Calculate!', width=10 * self.scale, command=self.calculate)
        # btn_roll = ttk.Button(frm_main, text='Roll!', width=10 * self.scale, command=self.roll)

        frm_main_placement = [[lbl_title],
                              [frm1],
                              [btn_calkulate]]

        frm_results = ttk.Frame(self, padding=10)
        lbl_result_calc = ttk.Label(frm_results, textvariable=self.result, font=Font(size=int(self.font_size * 2)),
                                    width=8, anchor="w")
        lbl_result_roll_1 = ttk.Label(frm_results, textvariable=self.roll_result_1,
                                      font=Font(size=int(self.font_size * 1.5)),
                                      width=12, anchor="n")
        lbl_result_roll_2 = ttk.Label(frm_results, textvariable=self.roll_result_2,
                                      font=Font(size=int(self.font_size * 1.5)),
                                      width=12, anchor="n")
        lbl_result_roll_3 = ttk.Label(frm_results, textvariable=self.roll_result_3,
                                      font=Font(size=int(self.font_size * 1.5)),
                                      width=12, anchor="n")
        lbl_result_roll_4 = ttk.Label(frm_results, textvariable=self.roll_result_4,
                                      font=Font(size=int(self.font_size * 1.5)),
                                      width=12, anchor="n")
        lbl_successes = ttk.Label(frm_results, textvariable=self.successes,
                                  font=Font(size=int(self.font_size * 2)),
                                  width=8, anchor='n')
        frm_results_placement = [[lbl_result_calc],
                                 [lbl_result_roll_1],
                                 [lbl_result_roll_2],
                                 [lbl_result_roll_3],
                                 [lbl_result_roll_4],
                                 [lbl_successes]]

        frm_scale = ttk.Frame(self, padding=10)
        btn_plus = ttk.Button(frm_scale, width=1 * self.scale, text='+', command=lambda: self.scale_up(True))
        btn_minus = ttk.Button(frm_scale, width=1 * self.scale, text='-', command=lambda: self.scale_up(False))
        frm_scale_placement = [[btn_plus],
                               [btn_minus]]

        root_placement = [[frm_main, frm_results, frm_scale]]

        lbl1 = ttk.Label(frm1, text="Number of dice:", width=15, padding=3 * self.scale, anchor='e',
                         font=Font(size=self.font_size))
        lbl2 = ttk.Label(frm1, text="Difficulty:", width=15, padding=3 * self.scale, anchor='e',
                         font=Font(size=self.font_size))
        lbl3 = ttk.Label(frm1, text="Success needed:", width=15, padding=3 * self.scale, anchor='e',
                         font=Font(size=self.font_size))
        scale_1 = ttk.Scale(frm1,
                            from_=1,
                            to=20,
                            length=100 * self.scale,
                            variable=self.dice_number,
                            command=lambda s: self.scaler(s, self.dice_number))
        lbl_scale_1 = ttk.Label(frm1,
                                textvariable=self.dice_number,
                                width=3,
                                padding=3 * self.scale,
                                font=Font(size=self.font_size))
        scale_2 = ttk.Scale(frm1,
                            from_=2,
                            to=10,
                            length=100 * self.scale,
                            variable=self.difficulty,
                            command=lambda s: self.scaler(s, self.difficulty))
        lbl_scale_2 = ttk.Label(frm1,
                                textvariable=self.difficulty,
                                width=3,
                                padding=3 * self.scale,
                                font=Font(size=self.font_size))
        scale_3 = ttk.Scale(frm1,
                            from_=1,
                            to=10,
                            length=100 * self.scale,
                            variable=self.success_needed,
                            command=lambda s: self.scaler(s, self.success_needed))
        lbl_scale_3 = ttk.Label(frm1,
                                textvariable=self.success_needed,
                                width=3,
                                padding=3 * self.scale,
                                font=Font(size=self.font_size))
        frm1_placement = [[lbl1, scale_1, lbl_scale_1],
                          [lbl2, scale_2, lbl_scale_2],
                          [lbl3, scale_3, lbl_scale_3]]

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
