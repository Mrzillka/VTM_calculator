import asyncio
import logging
import threading
from itertools import combinations_with_replacement
from random import randint, choice
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from typing import Tuple, List, Any

from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, Application, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

NAMES = ('Alex', 'Greg', 'John', 'Bill', 'Emma', 'Richard', 'Anna', 'Thomas', 'Andrew', 'Maria', 'Caren', 'Carl')

BOT_TOKEN = "8184695854:AAGBsg4e2dg-IwVu-Ggf7K_a8an_1LJnObA"


class Root(Tk):
    # TODO: add statistics
    # TODO: improve interface
    # TODO: make initiative roll
    def __init__(self):
        super().__init__()
        self.start_font_size = 10
        self.font_size = self.start_font_size
        self.title('VTM calculator')
        self.resizable(False, False)

        self.scale = 1

        self.bot = TgBot(BOT_TOKEN)
        self.chat_id = StringVar(value=self.bot.CHAT_ID)

        self.grid_columnconfigure(0, pad=10)
        self.grid_columnconfigure(1, pad=10)
        self.grid_columnconfigure(2, pad=10)
        self.grid_rowconfigure(0, pad=10)

        self.dice_number = IntVar(value=1)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success = IntVar(value=0)
        self.additional_options = BooleanVar(value=False)
        self.is_send_to_telegram = BooleanVar(value=False)
        self.name = StringVar(value=choice(NAMES))
        self.specialisation = BooleanVar(value=False)

        self.result = StringVar(value='Chance: -.--%')
        self.roll_result = []
        self.specialisation_roll = []
        self.roll_result_1 = StringVar(value="")
        self.roll_result_2 = StringVar(value="")
        self.roll_result_spec = StringVar(value="")
        self.successes = StringVar(value="0")

        self.styles = {
            "my.TFrame": ttk.Style(),
            "first.TFrame": ttk.Style(),
            "second.TFrame": ttk.Style(),
            "third.TFrame": ttk.Style(),
            "L.TButton": ttk.Style(),
            "S.TButton": ttk.Style(),
            "my.TEntry": ttk.Style(),
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

        self.set_window_size()

    def styles_configure(self):
        # TODO: test styles functionality
        self.styles["my.TFrame"].configure("first.TFrame")
        self.styles["first.TFrame"].configure("first.TFrame", background='#A0A0A0')
        self.styles["second.TFrame"].configure("second.TFrame", background='#010101')
        self.styles["third.TFrame"].configure("third.TFrame", background='#FFFFFF')
        self.styles["L.TButton"].configure("L.TButton", font=("Javanese text", int(self.font_size * 1.5)),
                                           padding=3 * self.scale)
        self.styles["S.TButton"].configure("S.TButton", font=("Javanese text", self.font_size),
                                           padding=3 * self.scale)
        self.styles["my.TEntry"].configure("my.TEntry", font=("Javanese text", self.font_size))
        self.styles["my.Horizontal.TScale"].configure("my.Horizontal.TScale", font=("Javanese text", self.font_size),
                                                      padding=3 * self.scale)
        self.styles["my.TSpinbox"].configure("my.TSpinbox", font=("Javanese text", self.font_size),
                                             padding=3 * self.scale)
        self.styles["my.TCheckbutton"].configure("my.TCheckbutton", font=("Javanese text", self.font_size),
                                                 padding=3 * self.scale)
        self.styles["L.TLabel"].configure("L.TLabel", font=("Javanese text", self.font_size * 2),
                                          padding=3 * self.scale)
        self.styles["M.TLabel"].configure("M.TLabel", font=("Javanese text", int(self.font_size * 1.5)),
                                          padding=3 * self.scale)
        self.styles["S.TLabel"].configure("S.TLabel", font=("Javanese text", self.font_size),
                                          padding=3 * self.scale)

    def redraw_interface(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, pad=10)
        self.grid_columnconfigure(1, pad=10)
        self.grid_columnconfigure(2, pad=10)
        self.grid_rowconfigure(0, pad=10)

        self.interface()
        self.set_window_size()

    def set_window_size(self):
        width = sum(frm.winfo_width() for frm in self.winfo_children()) + 10 * 3
        height = max(frm.winfo_height() for frm in self.winfo_children()) + 10
        self.geometry(f"{width}x{height}")

    def scale_up(self, up=True) -> None:
        if up:
            if self.scale < 3:
                self.scale += 1
                self.font_size *= self.scale
        else:
            if self.scale > 1:
                self.scale -= 1
                self.font_size = self.start_font_size * self.scale
            else:
                return

        self.styles_configure()
        self.redraw_interface()

    def calculate(self) -> None:
        calculator = Calculator(self.dice_number.get(), self.difficulty.get(), self.success_needed.get())
        self.result.set(f'Chance: {calculator.get_result():.2f}%')

    def roll(self) -> None:
        roller = Roller(self.dice_number.get(),
                        self.difficulty.get(),
                        self.auto_success.get(),
                        self.specialisation.get())
        roll, successes, specialisation_roll = roller.get_result()
        self.roll_result = roll
        self.specialisation_roll = specialisation_roll
        self.set_roll_result_placement()
        self.successes.set(f"{successes}")

    def roll_and_calculate(self) -> None:
        self.calculate()
        self.roll()
        if self.is_send_to_telegram.get():
            self.send_to_telegram()

    def run_bot_polling(self):
        threading.Thread(
            target=self.bot.run_bot_polling,
            daemon=True
        ).start()

    def set_roll_result_placement(self) -> None:
        self.roll_result_1.set(f'{", ".join(map(str, self.roll_result[:8]))}')
        self.roll_result_2.set(f'{", ".join(map(str, self.roll_result[8:]))}')
        self.roll_result_spec.set(f'{", ".join(map(str, self.specialisation_roll))}')

    @staticmethod
    def scaler(s, var) -> None:
        var.set(int(float(s)))

    @staticmethod
    def place_widgets(lst: list[list[Widget]]) -> None:
        for y in range(len(lst)):
            for x in range(len(lst[y])):
                lst[y][x].update()
                lst[y][x].grid(column=x, row=y)

    def send_to_telegram(self):
        roll = self.roll_result_1.get().split(', ') + self.roll_result_2.get().split(
            ', ') + self.roll_result_spec.get().split(', ')
        roll = [i for i in roll if i]
        print(roll)

        message = f"""<b><i>{self.name.get()}</i> rolled:</b>
<i>{', '.join(roll)}</i>
on <b>{self.dice_number.get()} dices</b> with <b> difficulty {self.difficulty.get()}</b>.

<b>It's a {'SUCCESS' if int(self.successes.get()) >= 1 else 'BOCH' if int(self.successes.get()) < 0 else 'FAILURE'}!</b>
<b><u>Total successes: {self.successes.get()}</u></b>

Succeed {self.result.get()}
"""

        print(message + f"\n{'-' * 20}\n")

        self.bot.threaded_send(message)

    def interface(self) -> None:
        # 3 main frames
        frm_main = ttk.Frame(self, padding=10, style='my.TFrame')
        frm_results = ttk.Frame(self, padding=10, style='my.TFrame')
        frm_scale = ttk.Frame(self, padding=10, style='my.TFrame')

        # frm_main
        lbl_title = ttk.Label(frm_main, text='VTM calculator', anchor='n', style='L.TLabel')
        frm_controls = ttk.Frame(frm_main, padding=10, style="my.TFrame")
        frm_controls.grid_columnconfigure(1, pad=5)
        btn_calkulate = ttk.Button(frm_main, text='Calculate & Roll!', style="L.TButton",
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
        chk_additional_options = ttk.Checkbutton(frm_controls,
                                                 text="Additional options",
                                                 variable=self.additional_options,
                                                 command=self.redraw_interface,
                                                 style="my.TCheckbutton")
        chk_is_send_to_telegram = ttk.Checkbutton(frm_controls,
                                                  text="Send to Telegram",
                                                  variable=self.is_send_to_telegram,
                                                  style="my.TCheckbutton")
        frm_controls_placement: List[Any] = [[lbl1, scale_1, spinbox_1],
                                             [lbl2, scale_2, spinbox_2],
                                             [chk_additional_options, chk_is_send_to_telegram]]

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

            lbl5 = ttk.Label(frm_controls, text="Character name:", width=12, anchor='e', style="M.TLabel")
            entr_name = ttk.Entry(frm_controls, textvariable=self.name, width=15,
                                  font=("Javanese text", self.font_size))
            frm_controls_placement.append([lbl5, entr_name])

            chk_specialisations = ttk.Checkbutton(frm_controls,
                                                  text="Specialisation",
                                                  variable=self.specialisation,
                                                  style="my.TCheckbutton")
            frm_controls_placement.append([chk_specialisations])

            btn_connect = ttk.Button(frm_controls, text="Connect to Telegram", style='S.TButton',
                                     command=self.run_bot_polling)
            frm_controls_placement.append([btn_connect])

        # frm_result
        lbl_result_calc = ttk.Label(frm_results, textvariable=self.result, width=14, anchor="center", style="L.TLabel")
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
        lbl_result_roll_spec = ttk.Label(frm_results,
                                         textvariable=self.roll_result_spec,
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
                                 [lbl_result_roll_spec],
                                 [lbl_successes]]

        # frm_scale
        btn_plus = ttk.Button(frm_scale, width=2, text='+', style='L.TButton',
                              command=lambda: self.scale_up(True))
        btn_minus = ttk.Button(frm_scale, width=2, text='-', style='L.TButton',
                               command=lambda: self.scale_up(False))
        frm_scale_placement = [[btn_plus],
                               [btn_minus]]

        root_placement = [[frm_main, frm_results, frm_scale]]

        for obj in (root_placement, frm_main_placement, frm_results_placement, frm_controls_placement,
                    frm_scale_placement):
            self.place_widgets(obj)


class TgBot:
    def __init__(self, token):
        self.token = token
        self.CHAT_ID = None
        self.THREAD_ID = None

        self.greeting_message = """Hello! I'm a bot, connected to VTM Calculator.

Press check box in the desktop interface to send roll results in this thread

Results will be send to the last thread where you use /start command."""

        self.message = ""

    def run_bot_polling(self):
        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .build()
        )

        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))

        self.application.run_polling()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.CHAT_ID = update.effective_chat.id
        self.THREAD_ID = update.message.message_thread_id
        try:
            await context.bot.send_message(chat_id=self.CHAT_ID, message_thread_id=self.THREAD_ID,
                                           text=self.greeting_message)
            self.application.stop_running()
        except TelegramError as e:
            raise RuntimeError(f"Telegram error: {e}")

    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.CHAT_ID = update.effective_chat.id
        self.THREAD_ID = update.message.message_thread_id
        try:
            await context.bot.send_message(chat_id=self.CHAT_ID, message_thread_id=self.THREAD_ID, parse_mode="HTML",
                                           text=f"CHAT ID: <code>{str(update.effective_chat.id)}</code>")
            await context.bot.send_message(chat_id=self.CHAT_ID, message_thread_id=self.THREAD_ID, parse_mode="HTML",
                                           text=f"THREAD ID: <code>{str(update.message.message_thread_id)}</code>")
        except TelegramError as e:
            raise RuntimeError(f"Telegram error: {e}")

    async def send_telegram_message(self, text: str):
        bot = Bot(token=BOT_TOKEN)
        try:
            await bot.send_message(
                chat_id=self.CHAT_ID,
                message_thread_id=int(self.THREAD_ID) if self.THREAD_ID else None,
                text=text,
                parse_mode="HTML"
            )
        except TelegramError as e:
            raise RuntimeError(f"Telegram error: {e}")

    def send_message_from_gui(self, text: str):
        async def runner():
            await self.send_telegram_message(text)

        try:
            asyncio.run(runner())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def threaded_send(self, text: str):
        thread = threading.Thread(
            target=self.send_message_from_gui,
            args=(text,),
            daemon=True
        )
        thread.start()


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
    def __init__(self, dice_number: int = 1, difficulty: int = 6, auto_success: int = 0, specialisation: bool = False):
        self.dice_number = dice_number
        self.difficulty = difficulty
        self.auto_success = auto_success
        self.specialisation = specialisation

    def get_result(self) -> Tuple[List[int], int, List[int]]:
        roll = [randint(1, 10) for _ in range(self.dice_number)]

        additional_roll = []
        if self.specialisation:
            for r in [i for i in roll if i == 10]:
                new_ = r
                while new_ == 10:
                    new_ = randint(1, 10)
                    additional_roll.append(new_)

        successes = len([1 for d in roll + additional_roll if d >= self.difficulty]) + self.auto_success
        failures = roll.count(1)
        successes -= failures
        return roll, successes, additional_roll


if __name__ == '__main__':
    root = Root()
    root.mainloop()
