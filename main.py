import asyncio
import logging
import os
import threading
from itertools import combinations_with_replacement
from random import randint, choice
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from typing import Tuple, List, Any

import dotenv
from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler

# import UI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

NAMES = ('Alex', 'Greg', 'John', 'Bill', 'Emma', 'Richard', 'Anna', 'Thomas', 'Andrew', 'Maria', 'Caren', 'Carl')
WOUNDS = (
    ("", ""),
    ("Bruised", ""),
    ("Hurt", "-1"),
    ("Injured", "-1"),
    ("Wounded", "-2"),
    ("Mauled", "-2"),
    ("Crippled", "-5"),
    ("Incapacitated", ""),
    ("Torpor", ""),
)

BOT_TOKEN = "8184695854:AAGBsg4e2dg-IwVu-Ggf7K_a8an_1LJnObA"
ENV_PATH = '%s\\VTM Roller\\' % os.environ['APPDATA']
ENV_FILE_PATH = os.path.join(ENV_PATH, ".env")


def set_appdata_settings():
    if not os.path.exists(ENV_PATH):
        print(f'{ENV_PATH} does not exist! Creating...')
        os.makedirs(ENV_PATH)
    if not os.path.exists(ENV_FILE_PATH):
        print(f'{ENV_FILE_PATH} does not exist! Creating...')
        file = open(ENV_FILE_PATH, 'w')
        file.close()
    dotenv.load_dotenv(ENV_FILE_PATH)


def place_widgets(lst: list[list[Widget]]) -> None:
    for y in range(len(lst)):
        for x in range(len(lst[y])):
            lst[y][x].grid(column=x, row=y)
            lst[y][x].update()


class Root(Tk):
    # TODO: add statistics

    start_font_size = 10

    def __init__(self):
        super().__init__()
        self.font_size = self.start_font_size
        self.title('VTM calculator')
        self.resizable(True, True)

        self.scale = 1

        self.bot = TgBot(BOT_TOKEN)
        self.chat_id = StringVar(value=self.bot.CHAT_ID)

        self.grid_columnconfigure(0, pad=10)
        self.grid_columnconfigure(1, pad=10)
        self.grid_columnconfigure(2, pad=10)
        self.grid_columnconfigure(3, pad=10)
        self.grid_rowconfigure(0, pad=10)

        self.dice_number = IntVar(value=1)
        self.difficulty = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success = IntVar(value=0)
        self.additional_options = BooleanVar(value=False)
        self.is_send_to_telegram = BooleanVar(value=False)
        self.specialisation = BooleanVar(value=False)

        self.result = StringVar(value='Chance: -.--%')
        self.roll_result = []
        self.specialisation_roll = []
        self.roll_result_1 = StringVar(value="")
        self.roll_result_2 = StringVar(value="")
        self.roll_result_spec = StringVar(value="")
        self.successes = StringVar(value="0")
        self.initiative = StringVar(value="")

        self.expand_options = BooleanVar(value=False)
        self.name = StringVar(value=choice(NAMES))
        self.pooling_state = StringVar(value='Connect to Telegram')
        self.initiative_bonus_dex = IntVar(value=0)
        self.initiative_bonus_wits = IntVar(value=0)

        self.expand_blood = BooleanVar(value=False)
        self.blood_max_value = IntVar(value=10)
        self.blood = [[BooleanVar(value=False) for _ in range(10)] for _ in range(4)]
        self.blood_value = IntVar(value=10)
        self.set_blood(load=True)

        self.expand_wounds = BooleanVar(value=False)
        self.wounds = [BooleanVar(value=False) for _ in range(9)]
        self.wounds_value = IntVar(value=0)
        self.roll_penalty = IntVar(value=0)

        self.humanity = [BooleanVar(value=False) for _ in range(10)]
        self.humanity_value = IntVar(value=0)

        self.will = [BooleanVar(value=False) for _ in range(10)]
        self.will_value = IntVar(value=0)

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

        self.load_from_file()

    def styles_configure(self):
        # TODO: test styles functionality
        self.styles["my.TFrame"].configure("my.TFrame", relief='solid')
        self.styles["first.TFrame"].configure("first.TFrame", background='#A0A0A0')
        self.styles["second.TFrame"].configure("second.TFrame", background='#010101')
        self.styles["third.TFrame"].configure("third.TFrame", background='#FFFFFF')
        self.styles["L.TButton"].configure("L.TButton", font=("Javanese text", int(self.font_size * 1.5)))
        self.styles["S.TButton"].configure("S.TButton", font=("Javanese text", self.font_size))
        self.styles["my.TEntry"].configure("my.TEntry", font=("Javanese text", self.font_size))
        self.styles["my.Horizontal.TScale"].configure("my.Horizontal.TScale", font=("Javanese text", self.font_size))
        self.styles["my.TSpinbox"].configure("my.TSpinbox", font=("Javanese text", self.font_size))
        self.styles["my.TCheckbutton"].configure("my.TCheckbutton", font=("Javanese text", self.font_size))
        self.styles["L.TLabel"].configure("L.TLabel", font=("Javanese text", self.font_size * 2))
        self.styles["M.TLabel"].configure("M.TLabel", font=("Javanese text", int(self.font_size * 1.5)))
        self.styles["S.TLabel"].configure("S.TLabel", font=("Javanese text", self.font_size))

    def redraw_interface(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, pad=10)
        self.grid_columnconfigure(1, pad=10)
        self.grid_columnconfigure(2, pad=10)
        self.grid_columnconfigure(3, pad=10)
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
        calculator = Calculator(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            success_needed=self.success_needed.get(),
            auto_successes=self.auto_success.get(),
        )
        self.result.set(f'Chance: {calculator.get_result():.2f}%')

    def roll(self) -> None:
        roller = Roller(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            penalty=self.roll_penalty.get()
        )
        roll, successes, specialisation_roll = roller.get_result()
        self.roll_result = roll
        self.specialisation_roll = specialisation_roll
        self.set_roll_result_placement()
        self.successes.set(f"{successes}")

    def roll_and_calculate(self) -> None:
        self.calculate()
        self.roll()
        if self.is_send_to_telegram.get():
            self.send_roll_to_telegram()

    def roll_initiative(self):
        roll = randint(1, 10) + self.roll_penalty.get()
        self.initiative.set(f"Initiative: {roll + self.initiative_bonus_dex.get() + self.initiative_bonus_wits.get()}")
        if self.is_send_to_telegram.get():
            self.send_initiative_to_telegram()

    def run_bot_polling(self):
        self.bot.is_pooling = True
        self.pooling_state.set('Pooling...')
        self.update_pooling_state(0)
        threading.Thread(
            target=self.bot.run_bot_polling,
            daemon=True
        ).start()

    def update_pooling_state(self, x):
        if self.bot.is_pooling:
            self.pooling_state.set('Connecting...')
        else:
            self.pooling_state.set('Connect to Telegram')
        self.after(1000, self.update_pooling_state, x)

    def set_roll_result_placement(self) -> None:
        self.roll_result_1.set(f'{", ".join(map(str, self.roll_result[:8]))}')
        self.roll_result_2.set(f'{", ".join(map(str, self.roll_result[8:]))}')
        self.roll_result_spec.set(f'{", ".join(map(str, self.specialisation_roll))}')

    @staticmethod
    def scaler(s, var) -> None:
        var.set(int(float(s)))

    def send_roll_to_telegram(self):
        roll = self.roll_result_1.get().split(', ') + self.roll_result_2.get().split(
            ', ') + self.roll_result_spec.get().split(', ')
        roll = [i for i in roll if i]
        print(roll)

        message = f"<b><i>{self.name.get()}</i> rolled:</b>\n"
        message += f"<i>{', '.join(roll)}</i>\n"
        message += f"on <b>{self.dice_number.get()} dices</b> with <b>difficulty {self.difficulty.get()}</b>.\n"

        message += f"<b>It's a {'SUCCESS' if int(self.successes.get()) >= 1 else 'BOCH' if int(self.successes.get()) < 0 else 'FAILURE'}!</b>\n\n"
        message += f"<b><u>Total successes: {self.successes.get()}</u></b>\n"
        message += f"        Auto successes: {self.auto_success.get()}\n"
        message += f"        Wounds penalty: {self.roll_penalty.get()} die(s)\n"
        message += f"        Needed at least {self.success_needed.get()} successes\n"
        # total_successes = f"{int(self.successes.get()) - int(self.auto_success.get())} + {self.auto_success.get()} - {-self.roll_penalty.get()} = {self.successes.get()}"

        message += f"Succeed {self.result.get()}"

        print(message + f"\n{'-' * 20}\n")

        self.bot.threaded_send(message)

    def send_initiative_to_telegram(self):
        roll = int(self.initiative.get().split()[1])
        bonus_dex = self.initiative_bonus_dex.get()
        bonus_wits = self.initiative_bonus_wits.get()
        roll -= bonus_dex + bonus_wits

        message = f"<b><i>{self.name.get()}</i> rolled #INITIATIVE</b>\n"
        message += f"Result: <b>{roll + bonus_dex + bonus_wits}</b>\n"
        message += f"<i>Rolled {roll} + {bonus_dex} Dex + {bonus_wits} Wits</i>"

        print(message + f"\n{'-' * 20}\n")

        self.bot.threaded_send(message)

    def save_to_file(self):
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='CHAT_ID', value_to_set=str(self.bot.CHAT_ID))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='THREAD_ID', value_to_set=str(self.bot.THREAD_ID))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='NAME', value_to_set=self.name.get())
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='DEX', value_to_set=str(self.initiative_bonus_dex.get()))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='WITS', value_to_set=str(self.initiative_bonus_wits.get()))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='BLOOD', value_to_set=str(self.blood_value.get()))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='MAX_BLOOD', value_to_set=str(self.blood_max_value.get()))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='WOUNDS', value_to_set=str(self.wounds_value.get()))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='HUMANITY', value_to_set=str(self.humanity_value.get()))
        dotenv.set_key(dotenv_path=ENV_FILE_PATH, key_to_set='WILL', value_to_set=str(self.will_value.get()))

    def load_from_file(self):
        try:
            env = dotenv.dotenv_values(dotenv_path=ENV_FILE_PATH)
            self.bot.CHAT_ID = env['CHAT_ID']
            self.bot.THREAD_ID = env['THREAD_ID'] if env['THREAD_ID'] != 'None' else None
            self.name.set(env['NAME'])
            self.initiative_bonus_dex.set(int(env['DEX']))
            self.initiative_bonus_wits.set(int(env['WITS']))
            self.blood_value.set(int(env['BLOOD']))
            self.blood_max_value.set(int(env['MAX_BLOOD']))
            self.set_blood(load=True)
            self.wounds_value.set(int(env['WOUNDS']))
            self.set_wounds(load=True)
            self.humanity_value.set(int(env['HUMANITY']))
            self.set_humanity(load=True)
            self.will_value.set(int(env['WILL']))
            self.set_will(load=True)
        except KeyError:
            self.save_to_file()

    def set_blood(self, r=0, c=0, load=False) -> None:
        if load:
            r = self.blood_value.get() // 10
            c = self.blood_value.get() % 10
        for i in range(4):
            for j in range(10):
                if i < r:
                    self.blood[i][j].set(True)
                elif i <= r and j <= c:
                    self.blood[i][j].set(True)
                else:
                    self.blood[i][j].set(False)
        if load:
            self.blood[r][c].set(False)
            self.blood_value.set(10 * r + c)
        else:
            self.blood_value.set(10 * r + (c + 1))

    def set_wounds(self, y=0, load=False):
        if load:
            y = self.wounds_value.get()
        for i in range(9):
            if i <= y:
                self.wounds[i].set(True)
            else:
                self.wounds[i].set(False)
        self.wounds_value.set(y)
        roll_penalty = WOUNDS[self.wounds_value.get()][1]
        self.roll_penalty.set(int(roll_penalty) if roll_penalty else 0)

    def set_humanity(self, x=0, load=False):
        if load:
            x = self.humanity_value.get()
        for i in range(10):
            if i <= x:
                self.humanity[i].set(True)
            else:
                self.humanity[i].set(False)
        self.humanity_value.set(x)

    def set_will(self, x=0, load=False):
        if load:
            x = self.will_value.get()
        for i in range(10):
            if i <= x:
                self.will[i].set(True)
            else:
                self.will[i].set(False)
        self.will_value.set(x)

    def interface(self) -> None:
        interface = Interface(self)
        interface.place_objects()
        place_widgets([[interface]])


class Interface(ttk.Frame):
    def __init__(self, root: Root):
        super().__init__()

        self.root = root

        self.placement: dict[str, list[list[Any]]] = {}
        self.placement['root'] = [
            [self.frm_center(self)],
            [self.frm_bottom(self)]
        ]

        self.place_objects()

    def frm_center(self, root_frm):
        frm = ttk.Frame(root_frm, padding=4, style='my.TFrame')

        self.placement['frm_center'] = [
            [
                self.frm_main(frm),
                self.frm_results(frm),
                self.frm_scale(frm),
                self.frm_expand_options(frm),
                self.frm_expand_blood(frm),
                self.frm_expand_wounds(frm),
            ]
        ]

        return frm

    def frm_main(self, root_frm):
        frm = ttk.Frame(root_frm, padding=10, style='my.TFrame')
        lbl_title = ttk.Label(frm, text='VTM calculator', anchor='n', style='L.TLabel')

        self.placement['frm_main'] = [
            [lbl_title],
            [self.frm_controls(root_frm=frm)],
            [self.frm_main_buttons(root_frm=frm)]
        ]

        return frm

    def frm_controls(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style="my.TFrame")
        frm.grid_columnconfigure(1, pad=5)
        self.placement['frm_controls'] = []

        lbl_number_of_dice = ttk.Label(frm, text="Number of dice:", width=12, style="M.TLabel", anchor='e')
        scale_number_of_dice = ttk.Scale(frm,
                                         from_=1,
                                         to=15,
                                         length=125 * self.root.scale,
                                         variable=self.root.dice_number,
                                         style="my.Horizontal.TScale",
                                         command=lambda s: self.root.scaler(s, self.root.dice_number))
        spinbox_number_of_dice = ttk.Spinbox(frm,
                                             from_=1,
                                             to=15,
                                             textvariable=self.root.dice_number,
                                             width=3,
                                             style="my.TSpinbox")
        lbl_penalty = ttk.Label(frm, textvariable=self.root.roll_penalty, width=3, style="S.TLabel")
        self.placement['frm_controls'].append(
            [lbl_number_of_dice, scale_number_of_dice, spinbox_number_of_dice, lbl_penalty])

        lbl_difficulty = ttk.Label(frm, text="Difficulty:", width=12, style="M.TLabel", anchor='e')
        scale_difficulty = ttk.Scale(frm,
                                     from_=2,
                                     to=10,
                                     length=125 * self.root.scale,
                                     variable=self.root.difficulty,
                                     style="my.Horizontal.TScale",
                                     command=lambda s: self.root.scaler(s, self.root.difficulty))
        spinbox_difficulty = ttk.Spinbox(frm,
                                         from_=2,
                                         to=10,
                                         textvariable=self.root.difficulty,
                                         width=3,
                                         style="my.TSpinbox")
        self.placement['frm_controls'].append([lbl_difficulty, scale_difficulty, spinbox_difficulty])

        lbl_auto_success = ttk.Label(frm, text="Auto success:", width=12, style="M.TLabel", anchor='e')
        scale_auto_success = ttk.Scale(frm,
                                       from_=0,
                                       to=5,
                                       length=125 * self.root.scale,
                                       variable=self.root.auto_success,
                                       style="my.Horizontal.TScale",
                                       command=lambda s: self.root.scaler(s, self.root.auto_success))
        spinbox_auto_success = ttk.Spinbox(frm,
                                           from_=0,
                                           to=5,
                                           textvariable=self.root.auto_success,
                                           width=3,
                                           style="my.TSpinbox")
        self.placement['frm_controls'].append([lbl_auto_success, scale_auto_success, spinbox_auto_success])

        chk_specialisations = ttk.Checkbutton(frm,
                                              text="Specialisation",
                                              variable=self.root.specialisation,
                                              style="my.TCheckbutton")
        chk_is_send_to_telegram = ttk.Checkbutton(frm,
                                                  text="Send to Telegram",
                                                  variable=self.root.is_send_to_telegram,
                                                  style="my.TCheckbutton")
        chk_additional_options = ttk.Checkbutton(frm,
                                                 text="∨",
                                                 variable=self.root.additional_options,
                                                 command=self.root.redraw_interface,
                                                 style="my.TCheckbutton")
        self.placement['frm_controls'].append([chk_specialisations, chk_is_send_to_telegram, chk_additional_options])
        # self.placement['frm_controls'].append([])

        if self.root.additional_options.get():
            lbl_success_needed = ttk.Label(frm, text="Success needed:", width=12, style="M.TLabel", anchor='e')
            scale_success_needed = ttk.Scale(frm,
                                             from_=1,
                                             to=10,
                                             length=125 * self.root.scale,
                                             variable=self.root.success_needed,
                                             style="my.Horizontal.TScale",
                                             command=lambda s: self.root.scaler(s, self.root.success_needed))
            spinbox_success_needed = ttk.Spinbox(frm,
                                                 from_=1,
                                                 to=10,
                                                 textvariable=self.root.success_needed,
                                                 width=3,
                                                 style="my.TSpinbox")
            self.placement['frm_controls'].append([lbl_success_needed, scale_success_needed, spinbox_success_needed])

        return frm

    def frm_main_buttons(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_main_buttons'] = []
        btn_calkulate = ttk.Button(frm, text='Calculate & Roll!', style='L.TButton',
                                   command=self.root.roll_and_calculate)
        btn_initiative = ttk.Button(frm, text='Roll initiative', style='M.TButton',
                                    command=self.root.roll_initiative)

        self.placement['frm_main_buttons'].append([btn_calkulate, btn_initiative])

        return frm

    def frm_results(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_results'] = []
        lbl_result_calc = ttk.Label(frm, textvariable=self.root.result, width=14, anchor="center", style="L.TLabel")
        self.placement['frm_results'].append([lbl_result_calc])
        lbl_result_roll_1 = ttk.Label(frm,
                                      textvariable=self.root.roll_result_1,
                                      style="S.TLabel",
                                      width=20,
                                      anchor='n')
        self.placement['frm_results'].append([lbl_result_roll_1])
        lbl_result_roll_2 = ttk.Label(frm,
                                      textvariable=self.root.roll_result_2,
                                      style="S.TLabel",
                                      width=20,
                                      anchor='n')
        self.placement['frm_results'].append([lbl_result_roll_2])
        lbl_result_roll_spec = ttk.Label(frm,
                                         textvariable=self.root.roll_result_spec,
                                         style="S.TLabel",
                                         width=20,
                                         anchor='n')
        self.placement['frm_results'].append([lbl_result_roll_spec])
        lbl_successes = ttk.Label(frm,
                                  textvariable=self.root.successes,
                                  style="L.TLabel",
                                  width=5,
                                  anchor='n')
        self.placement['frm_results'].append([lbl_successes])
        lbl_initiative = ttk.Label(frm,
                                   textvariable=self.root.initiative,
                                   style="M.TLabel",
                                   width=10,
                                   anchor='n')

        self.placement['frm_results'].append([lbl_initiative])

        return frm

    def frm_scale(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_scale'] = []

        chk_expand_options = ttk.Checkbutton(frm,
                                             text='Options >',
                                             variable=self.root.expand_options,
                                             command=self.root.redraw_interface,
                                             style='my.TCheckbutton')
        self.placement['frm_scale'].append([chk_expand_options])
        chk_expand_blood = ttk.Checkbutton(frm,
                                           text='Blood >',
                                           variable=self.root.expand_blood,
                                           command=self.root.redraw_interface,
                                           style='my.TCheckbutton')
        self.placement['frm_scale'].append([chk_expand_blood])
        chk_expand_wounds = ttk.Checkbutton(frm,
                                            text='Wounds >',
                                            variable=self.root.expand_wounds,
                                            command=self.root.redraw_interface,
                                            style='my.TCheckbutton')
        self.placement['frm_scale'].append([chk_expand_wounds])
        btn_plus = ttk.Button(frm, width=2, text='+', style='L.TButton',
                              command=lambda: self.root.scale_up(True))
        self.placement['frm_scale'].append([btn_plus])
        btn_minus = ttk.Button(frm, width=2, text='-', style='L.TButton',
                               command=lambda: self.root.scale_up(False))
        self.placement['frm_scale'].append([btn_minus])

        return frm

    def frm_expand_options(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_expand_options'] = []
        self.placement['frm_expand_options_initiative'] = []
        if self.root.expand_options.get():
            lbl_name = ttk.Label(frm, text="Character name:", width=12, anchor='e', style="M.TLabel")
            self.placement['frm_expand_options'].append([lbl_name])
            entr_name = ttk.Entry(frm, textvariable=self.root.name, width=15,
                                  font=("Javanese text", self.root.font_size))
            self.placement['frm_expand_options'].append([entr_name])

            frm_expand_initiative = ttk.Frame(frm, padding=5, style='my.TFrame')
            lbl_expand_initiative_dex = ttk.Label(frm_expand_initiative, text='Dex', width=5, anchor='e',
                                                  style='S.TLabel')
            spinbox_expand_initiative_dex = ttk.Spinbox(frm_expand_initiative,
                                                        from_=0,
                                                        to=10,
                                                        textvariable=self.root.initiative_bonus_dex,
                                                        width=3,
                                                        style='my.TSpinbox')
            self.placement['frm_expand_options_initiative'].append(
                [lbl_expand_initiative_dex, spinbox_expand_initiative_dex])
            lbl_expand_initiative_wits = ttk.Label(frm_expand_initiative, text='Wits', width=5, anchor='e',
                                                   style='S.TLabel')
            spinbox_expand_initiative_wits = ttk.Spinbox(frm_expand_initiative,
                                                         from_=0,
                                                         to=10,
                                                         textvariable=self.root.initiative_bonus_wits,
                                                         width=3,
                                                         style='my.TSpinbox')
            self.placement['frm_expand_options_initiative'].append(
                [lbl_expand_initiative_wits, spinbox_expand_initiative_wits])

            self.placement['frm_expand_options'].append([frm_expand_initiative])

            btn_connect = ttk.Button(frm, textvariable=self.root.pooling_state, style='S.TButton',
                                     command=self.root.run_bot_polling)
            self.placement['frm_expand_options'].append([btn_connect])

            btn_save = ttk.Button(frm, text='Save', style='S.TButton',
                                  command=self.root.save_to_file)
            self.placement['frm_expand_options'].append([btn_save])

        return frm

    def disable_blood_cells(self):
        r = self.root.blood_max_value.get() // 10
        c = self.root.blood_max_value.get() % 10
        for i in range(4):
            for j in range(10):
                if i < r:
                    self.placement['frm_expand_blood_cells'][i][j].config(state='normal')
                elif i <= r and j < c:
                    self.placement['frm_expand_blood_cells'][i][j].config(state='normal')
                else:
                    self.placement['frm_expand_blood_cells'][i][j].config(state='disabled')
                    self.root.blood[i][j].set(False)

    def frm_expand_blood(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_expand_blood'] = []
        if self.root.expand_blood.get():
            lbl_blood_title = ttk.Label(frm, text='Blood', width=12, anchor='n', style="M.TLabel")
            self.placement['frm_expand_blood'].append([lbl_blood_title])

            frm_cells = self.frm_expand_blood_cells(frm)
            self.placement['frm_expand_blood'].append([frm_cells])

            frm_max_blood = self.frm_max_blood(frm)
            self.disable_blood_cells()
            self.placement['frm_expand_blood'].append([frm_max_blood])

        return frm

    def frm_expand_blood_cells(self, root_frm):
        frm = ttk.Frame(root_frm, style="my.TFrame")
        self.placement['frm_expand_blood_cells'] = []

        for i in range(4):
            self.placement['frm_expand_blood_cells'].append([])
            for j in range(10):
                blood_cell = ttk.Checkbutton(frm,
                                             variable=self.root.blood[i][j],
                                             command=lambda r=i, c=j: self.root.set_blood(r, c),
                                             style="my.TCheckbutton")
                self.placement['frm_expand_blood_cells'][i].append(blood_cell)

        return frm

    def frm_max_blood(self, root_frm):
        frm = ttk.Frame(root_frm, style="my.TFrame")
        self.placement['frm_expand_max_blood'] = []

        lbl = ttk.Label(frm, text="Max Blood", width=12, anchor='n', style='S.TLabel')

        spinbox = ttk.Spinbox(frm,
                              from_=1,
                              to=40,
                              textvariable=self.root.blood_max_value,
                              command=self.disable_blood_cells,
                              width=3,
                              style="my.TSpinbox")
        self.placement['frm_expand_max_blood'].append([lbl, spinbox])

        return frm

    def frm_expand_wounds(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_expand_wounds'] = []
        if self.root.expand_wounds.get():
            lbl_wounds_title = ttk.Label(frm, text='Wounds', width=12, anchor='n', style="M.TLabel")
            self.placement['frm_expand_wounds'].append([lbl_wounds_title])
            frm_cells = self.frm_expand_wounds_cells(frm)
            self.placement['frm_expand_wounds'].append([frm_cells])

        return frm

    def frm_expand_wounds_cells(self, root_frm):
        frm = ttk.Frame(root_frm, padding=0, style='my.TFrame')
        self.placement['frm_expand_wounds_cells'] = []

        for i in range(9):
            wound_name = ttk.Label(frm, text=WOUNDS[i][0], width=10, anchor='e',
                                   style="S.TLabel")
            wound_penalty = ttk.Label(frm, text=WOUNDS[i][1], anchor='w', style="S.TLabel")
            wound_cell = ttk.Checkbutton(frm,
                                         variable=self.root.wounds[i],
                                         command=lambda y=i: self.root.set_wounds(y),
                                         style="my.TCheckbutton")
            self.placement['frm_expand_wounds_cells'].append([wound_name, wound_penalty, wound_cell])

        return frm

    def frm_bottom(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_bottom'] = []

        frm_blood = self.frm_bottom_blood(frm)
        frm_wounds = self.frm_bottom_wounds(frm)
        frm_humanity = self.frm_bottom_humanity(frm)
        frm_will = self.frm_bottom_will(frm)

        self.placement['frm_bottom'].append([frm_blood, frm_wounds, frm_humanity, frm_will])

        return frm

    def frm_bottom_blood(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_bottom_blood'] = []

        lbl = ttk.Label(frm, text='Blood', style='M.TLabel')
        self.placement['frm_bottom_blood'].append([lbl])

        lbl_var = ttk.Label(frm, textvariable=self.root.blood_value, style = 'S.TLabel')
        self.placement['frm_bottom_blood'].append([lbl_var])

        return frm

    def frm_bottom_wounds(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_bottom_wounds'] = []

        lbl = ttk.Label(frm, text='Wounds', style='M.TLabel')
        self.placement['frm_bottom_wounds'].append([lbl])

        lbl_var = ttk.Label(frm, textvariable=self.root.wounds_value, style = 'S.TLabel')
        self.placement['frm_bottom_wounds'].append([lbl_var])

        return frm

    def frm_bottom_humanity(self, root_frm):
        frm = ttk.Frame(root_frm, padding=0, style='my.TFrame')
        self.placement['frm_humanity'] = []

        lbl = ttk.Label(frm, text='Humanity/Path', style='M.TLabel')
        self.placement['frm_humanity'].append([lbl])

        frm_humanity_cells = self.frm_humanity_cells(frm)
        self.placement['frm_humanity'].append([frm_humanity_cells])
        self.root.set_humanity(load=True)

        return frm

    def frm_humanity_cells(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_humanity_cells'] = [[],
                                                []]

        for i in range(10):
            point = ttk.Label(frm, text=f'{i + 1}', width=2, anchor='w', style='my.TLabel')
            self.placement['frm_humanity_cells'][0].append(point)
            cell = ttk.Checkbutton(frm,
                                   variable=self.root.humanity[i],
                                   command=lambda x=i: self.root.set_humanity(x),
                                   style='my.TCheckbutton')
            self.placement['frm_humanity_cells'][1].append(cell)

        return frm

    def frm_bottom_will(self, root_frm):
        frm = ttk.Frame(root_frm, padding=0, style='my.TFrame')
        self.placement['frm_will'] = []

        lbl = ttk.Label(frm, text='Will', style='M.TLabel')
        self.placement['frm_will'].append([lbl])

        frm_will_cells = self.frm_will_cells(frm)
        self.placement['frm_will'].append([frm_will_cells])
        self.root.set_will(load=True)

        return frm

    def frm_will_cells(self, root_frm):
        frm = ttk.Frame(root_frm, padding=5, style='my.TFrame')
        self.placement['frm_will_cells'] = [[],
                                            []]

        for i in range(10):
            point = ttk.Label(frm, text=f'{i + 1}', width=2, anchor='w', style='my.TLabel')
            self.placement['frm_will_cells'][0].append(point)
            cell = ttk.Checkbutton(frm,
                                   variable=self.root.will[i],
                                   command=lambda x=i: self.root.set_will(x),
                                   style='my.TCheckbutton')
            self.placement['frm_will_cells'][1].append(cell)

        return frm

    def place_objects(self):
        for obj in self.placement.values():
            place_widgets(obj)


class TgBot:
    def __init__(self, token):
        self.application = None
        self.token = token
        self.CHAT_ID = None
        self.THREAD_ID = None
        self.is_pooling = False

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

    async def start_command(self, update: Update, context):
        self.CHAT_ID = update.effective_chat.id
        self.THREAD_ID = update.message.message_thread_id
        try:
            await context.bot.send_message(chat_id=self.CHAT_ID, message_thread_id=self.THREAD_ID,
                                           text=self.greeting_message)
            self.application.stop_running()
            self.is_pooling = False
        except TelegramError as e:
            raise RuntimeError(f"Telegram error: {e}")

    async def debug_command(self, update: Update, context):
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
            [
                i >= self.difficulty for i in lst
            ].count(True) - lst.count(1) + self.auto_successes >= self.success_needed
            for lst in prod
        ]

    def get_result(self) -> float:
        result = self.run(self.get_product())
        return result.count(True) / len(result) * 100


class Roller:
    def __init__(self, dice_number: int = 1, difficulty: int = 6, auto_success: int = 0, specialisation: bool = False,
                 penalty: int = 0):
        self.dice_number = dice_number
        self.difficulty = difficulty
        self.auto_success = auto_success
        self.specialisation = specialisation
        self.penalty = penalty

    def get_result(self) -> Tuple[List[int], int, List[int]]:
        roll = [randint(1, 10) for _ in range(self.dice_number + self.penalty)]

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
    set_appdata_settings()
    app = Root()
    app.mainloop()
