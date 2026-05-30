from __future__ import annotations

import json
import logging
import queue
import shutil
from pathlib import Path
from tkinter import BooleanVar, IntVar, StringVar, Tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Callable

import dotenv

from bot.tg_bot import TgBot
from config import CHARACTER_FILE_PATH, CHARACTERS_DIR, ENV_FILE_PATH, get_bot_token
from game.calculator import Calculator
from game.character import ABILITIES, ATTRIBUTES, Character
from game.models import RollRecord
from game.roller import Roller
from lang import locale
from network.protocol import dict_to_roll_record, roll_record_to_dict
from network.session import NtfySession
from ui.constants import AUTOSAVE_DEBOUNCE_MS, BOT_STATUS_POLL_MS, NET_POLL_MS, TRACKER_DEBOUNCE_MS
from ui.player.interface import PlayerInterface
from ui.styles import configure_main_styles
from ui.theme import theme
from ui.utils import apply_icon, place_widgets

logger = logging.getLogger(__name__)


class PlayerRoot(Tk):
    """
    Main application window for VTM Calculator (Player).

    Owns application-level state (Telegram, roll parameters, UI flags, roll
    history, network session) and an instance of Character for all
    character-specific state.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("VTM calculator")
        self.resizable(False, False)

        apply_icon(self, "icon.ico")

        _env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        self._restore_lang_pref(_env)
        self._restore_theme_pref(_env)

        # ── Character ──────────────────────────────────────────────────────────
        self.character = Character()

        # ── Telegram ───────────────────────────────────────────────────────────
        try:
            token = get_bot_token()
        except EnvironmentError as exc:
            messagebox.showwarning("Telegram", str(exc))
            token = ""
        self.bot = TgBot(token)
        self.chat_id = StringVar(value=str(self.bot.chat_id or ""))

        # ── Roll parameters ────────────────────────────────────────────────────
        self.dice_number    = IntVar(value=5)
        self.difficulty     = IntVar(value=6)
        self.success_needed = IntVar(value=1)
        self.auto_success   = IntVar(value=0)
        self.specialisation = BooleanVar(value=False)

        # ── Quick rolls ────────────────────────────────────────────────────────
        _attr_names = [a for attrs in ATTRIBUTES.values() for a in attrs]
        _abil_names = [a for abils in ABILITIES.values() for a in abils]
        self.quick_rolls: list[tuple[StringVar, StringVar, IntVar, BooleanVar, IntVar]] = [
            (StringVar(value=_attr_names[0]),
             StringVar(value=_abil_names[0]),
             IntVar(value=6),
             BooleanVar(value=False),
             IntVar(value=0))
            for _ in range(4)
        ]
        self.quick_penalty = IntVar(value=0)
        self.quick_roll_dice: list[StringVar] = [StringVar(value="") for _ in range(4)]
        self.default_skill_penalty = BooleanVar(value=True)
        self.chargen_min_will = BooleanVar(value=False)

        # ── UI flags ───────────────────────────────────────────────────────────
        self.additional_options   = BooleanVar(value=False)
        self.is_send_to_telegram  = BooleanVar(value=False)
        self.trackers             = BooleanVar(value=False)

        # ── Session state ──────────────────────────────────────────────────────
        self.session_code = StringVar(value="")
        self.is_connected = BooleanVar(value=False)

        # ── Roll history ───────────────────────────────────────────────────────
        self.roll_history: list[RollRecord] = []
        self._on_roll_callbacks: list[Callable[[RollRecord], None]] = []

        # ── Telegram bot state ─────────────────────────────────────────────────
        self.pooling_state = StringVar(value=locale.t("controls.connect_tg"))

        locale.on_change(self._on_locale_change)

        self._configure_grid()
        self._configure_styles()
        self._build_interface()
        self.load_from_file()

        # Network: created after load so session_code is restored from file.
        self._net_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._session: NtfySession | None = None
        self._tracker_send_job: str | None = None
        self._autosave_job: str | None = None
        self._setup_tracker_traces()
        self._setup_autosave_traces()
        self._setup_quick_roll_dice_traces()
        self._refresh_quick_roll_dice()
        self.after(NET_POLL_MS, self._poll_net_queue)

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _restore_lang_pref(self, env: dict) -> None:
        saved = env.get("LANG_PREF", "en")
        if saved != locale.lang:
            locale.set_lang(saved)

    def _restore_theme_pref(self, env: dict) -> None:
        theme.set_mode(env.get("THEME_PREF", "light"))

    def _configure_grid(self) -> None:
        self.grid_columnconfigure(0, weight=1, pad=10)
        self.grid_rowconfigure(0, weight=1, pad=10)

    def _configure_styles(self) -> None:
        s = ttk.Style()
        s.theme_use("clam")
        configure_main_styles(s, theme.palette)
        self.option_add("*TCombobox*Listbox.background",       theme.palette["entry_bg"])
        self.option_add("*TCombobox*Listbox.foreground",       theme.palette["entry_fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", theme.palette["select_bg"])
        self.option_add("*TCombobox*Listbox.selectForeground", theme.palette["select_fg"])
        self.configure(bg=theme.palette["bg"])

    def toggle_theme(self) -> None:
        theme.toggle()
        s = ttk.Style()
        configure_main_styles(s, theme.palette)
        self.configure(bg=theme.palette["bg"])
        self.option_add("*TCombobox*Listbox.background",       theme.palette["entry_bg"])
        self.option_add("*TCombobox*Listbox.foreground",       theme.palette["entry_fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", theme.palette["select_bg"])
        self.option_add("*TCombobox*Listbox.selectForeground", theme.palette["select_fg"])
        self.save_to_file()

    def _build_interface(self) -> None:
        self._interface = PlayerInterface(self)
        place_widgets([[self._interface]])

    # ── Locale ─────────────────────────────────────────────────────────────────

    def _on_locale_change(self) -> None:
        self.pooling_state.set(
            locale.t("controls.connecting") if self.bot.is_polling
            else locale.t("controls.connect_tg")
        )

    # ── Roll callbacks ─────────────────────────────────────────────────────────

    def on_roll(self, callback: Callable[[RollRecord], None]) -> None:
        self._on_roll_callbacks.append(callback)

    def _emit_roll(self, record: RollRecord) -> None:
        for cb in self._on_roll_callbacks:
            cb(record)

    # ── Game logic ─────────────────────────────────────────────────────────────

    def _calculate(self, no_botch: bool = False) -> float:
        calc = Calculator(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            success_needed=self.success_needed.get(),
            auto_successes=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            no_botch=no_botch,
        )
        return calc.get_probability()

    def roll_and_calculate(self) -> None:
        probability = self._calculate()

        roller = Roller(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            penalty=self.character.roll_penalty.get(),
        )
        result = roller.roll()

        record = RollRecord(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            dice=list(result.dice),
            specialisation_dice=list(result.specialisation_dice),
            successes=result.successes,
            probability=probability,
            roller_name=self.character.character_name.get(),
            roll_type="NORMAL",
        )
        self._record_and_emit(record)

    def roll_damage_soak(self) -> None:
        """Roll without botch subtraction (damage or soak roll)."""
        probability = self._calculate(no_botch=True)

        roller = Roller(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            specialisation=self.specialisation.get(),
            penalty=self.character.roll_penalty.get(),
            no_botch=True,
        )
        result = roller.roll()

        record = RollRecord(
            dice_number=self.dice_number.get(),
            difficulty=self.difficulty.get(),
            auto_success=self.auto_success.get(),
            dice=list(result.dice),
            specialisation_dice=list(result.specialisation_dice),
            successes=result.successes,
            probability=probability,
            roller_name=self.character.character_name.get(),
            roll_type="DAMAGE",
        )
        self._record_and_emit(record)

    def quick_roll(self, index: int) -> None:
        attr_var, abil_var, diff_var, spec_var, auto_var = self.quick_rolls[index]
        attr_name = locale.reverse_lookup_en("sheet.attr_names", attr_var.get())
        abil_name = locale.reverse_lookup_en("sheet.ability_names", abil_var.get())
        attr_val  = self.character.get_stat_value(attr_name)
        abil_val  = self.character.get_stat_value(abil_name)
        dice_pool = attr_val + abil_val
        if abil_name and abil_val == 0 and self.default_skill_penalty.get():
            dice_pool -= 1
        penalty   = self.character.roll_penalty.get() + self.quick_penalty.get()

        effective_dice = max(1, max(1, dice_pool) + penalty)
        probability = Calculator(
            dice_number=effective_dice,
            difficulty=diff_var.get(),
            success_needed=1,
            auto_successes=auto_var.get(),
            specialisation=spec_var.get(),
        ).get_probability()

        roller = Roller(
            dice_number=max(1, dice_pool),
            difficulty=diff_var.get(),
            auto_success=auto_var.get(),
            penalty=penalty,
            specialisation=spec_var.get(),
        )
        result = roller.roll()
        record = RollRecord(
            dice_number=dice_pool,
            difficulty=diff_var.get(),
            auto_success=auto_var.get(),
            dice=list(result.dice),
            specialisation_dice=list(result.specialisation_dice),
            successes=result.successes,
            probability=probability,
            roller_name=self.character.character_name.get(),
            roll_type="QUICK",
        )
        self._record_and_emit(record)

    def roll_initiative(self) -> None:
        from random import randint
        char    = self.character
        d10     = randint(1, 10)
        penalty = char.roll_penalty.get()
        dex     = char.dex_value.get() + char.dex_boost.get()
        wits    = char.wits_value.get()
        total   = d10 + penalty + dex + wits

        record = RollRecord(
            dice_number=1,
            difficulty=0,
            auto_success=dex + wits,
            dice=[d10],
            specialisation_dice=[],
            successes=total,
            probability=0.0,
            roller_name=self.character.character_name.get(),
            roll_type="INITIATIVE",
        )
        self._record_and_emit(record)

        if self.is_send_to_telegram.get():
            self._send_initiative_to_telegram(total, d10)

    def _record_and_emit(self, record: RollRecord) -> None:
        """Append *record* to history, notify callbacks, publish to session and Telegram."""
        self.roll_history.append(record)
        self._emit_roll(record)

        if self._session is not None:
            self._session.publish("roll", roll_record_to_dict(record))

        if self.is_send_to_telegram.get() and record.roll_type in ("NORMAL", "DAMAGE"):
            self._send_roll_to_telegram(record)

    # ── Session management ─────────────────────────────────────────────────────

    def join_session(self) -> None:
        code = self.session_code.get().strip()
        if not code:
            messagebox.showwarning("Session", "Enter the session code from the Storyteller.")
            return
        if self._session is not None:
            self._session.stop()
        self._session = NtfySession(topic=code, event_queue=self._net_queue)
        self._session.start()
        self.is_connected.set(True)

    def leave_session(self) -> None:
        if self._session is not None:
            self._session.stop()
            self._session = None
        self.is_connected.set(False)

    def send_sheet_to_server(self) -> None:
        if self._session is None:
            return
        self._session.publish("sheet", self.character.to_dict())

    # ── Tracker auto-send (debounced) ──────────────────────────────────────────

    def _setup_autosave_traces(self) -> None:
        for var in (
            self.character.blood_value, self.character.blood_max_value,
            self.character.wounds_value, self.character.humanity_value,
            self.character.will_value, self.character.willpower_max,
            self.dice_number, self.difficulty, self.success_needed,
            self.auto_success, self.specialisation,
            self.session_code, self.character.character_name,
        ):
            var.trace_add("write", lambda *_: self._schedule_save())
        for av, bv, dv, sv, autov in self.quick_rolls:
            for var in (av, bv, dv, sv, autov):
                var.trace_add("write", lambda *_: self._schedule_save())
        self.quick_penalty.trace_add("write", lambda *_: self._schedule_save())
        self.default_skill_penalty.trace_add("write", lambda *_: self._schedule_save())
        self.chargen_min_will.trace_add("write", lambda *_: self._schedule_save())

    def _setup_quick_roll_dice_traces(self) -> None:
        char = self.character
        for av, bv, _dv, _sv, autov in self.quick_rolls:
            av.trace_add("write", self._refresh_quick_roll_dice)
            bv.trace_add("write", self._refresh_quick_roll_dice)
            autov.trace_add("write", self._refresh_quick_roll_dice)
        self.quick_penalty.trace_add("write", self._refresh_quick_roll_dice)
        char.roll_penalty.trace_add("write", self._refresh_quick_roll_dice)
        self.default_skill_penalty.trace_add("write", self._refresh_quick_roll_dice)
        for v in (char.str_boost, char.dex_boost, char.sta_boost):
            v.trace_add("write", self._refresh_quick_roll_dice)
        locale.on_change(self._refresh_quick_roll_dice)
        for cat_data in char.attributes.values():
            for stat_data in cat_data.values():
                for var in stat_data["vars"]:
                    var.trace_add("write", self._refresh_quick_roll_dice)
        for cat_data in char.abilities.values():
            for stat_data in cat_data.values():
                for var in stat_data["vars"]:
                    var.trace_add("write", self._refresh_quick_roll_dice)

    def _refresh_quick_roll_dice(self, *_) -> None:
        char = self.character
        pen = char.roll_penalty.get() + self.quick_penalty.get()
        for i, roll_tuple in enumerate(self.quick_rolls):
            attr_var, abil_var = roll_tuple[0], roll_tuple[1]
            attr_name = locale.reverse_lookup_en("sheet.attr_names", attr_var.get())
            abil_name = locale.reverse_lookup_en("sheet.ability_names", abil_var.get())
            attr_val = char.get_stat_value(attr_name)
            abil_val = char.get_stat_value(abil_name)
            pool = attr_val + abil_val
            if abil_name and abil_val == 0 and self.default_skill_penalty.get():
                pool -= 1
            eff = max(1, max(1, pool) + pen)
            auto_val = roll_tuple[4].get()
            text = f"{attr_val} + {abil_val} = {eff}"
            if auto_val > 0:
                text += f"  +{auto_val} auto"
            self.quick_roll_dice[i].set(text)

    def _schedule_save(self) -> None:
        if self._autosave_job:
            self.after_cancel(self._autosave_job)
        self._autosave_job = self.after(AUTOSAVE_DEBOUNCE_MS, self.save_to_file)

    def _setup_tracker_traces(self) -> None:
        for var in (
            self.character.blood_value,
            self.character.blood_max_value,
            self.character.wounds_value,
            self.character.humanity_value,
            self.character.will_value,
            self.character.willpower_max,
        ):
            var.trace_add("write", lambda *_: self._schedule_tracker_send())

    def _schedule_tracker_send(self) -> None:
        if self._session is None:
            return
        if self._tracker_send_job:
            self.after_cancel(self._tracker_send_job)
        self._tracker_send_job = self.after(TRACKER_DEBOUNCE_MS, self._send_trackers_now)

    def _send_trackers_now(self) -> None:
        self._tracker_send_job = None
        if self._session is None:
            return
        char = self.character
        self._session.publish("sheet_trackers", {
            "character_name": char.character_name.get(),
            "trackers": {
                "blood_value":     char.blood_value.get(),
                "blood_max_value": char.blood_max_value.get(),
                "wounds_value":    char.wounds_value.get(),
                "humanity_value":  char.humanity_value.get(),
                "will_value":      char.will_value.get(),
                "willpower_max":   char.willpower_max.get(),
            },
        })

    # ── Network queue polling ──────────────────────────────────────────────────

    def _poll_net_queue(self) -> None:
        try:
            while True:
                event_type, data = self._net_queue.get_nowait()

                if event_type == "roll":
                    record = dict_to_roll_record(data)  # type: ignore[arg-type]
                    self.roll_history.append(record)
                    self._emit_roll(record)

        except queue.Empty:
            pass
        finally:
            self.after(NET_POLL_MS, self._poll_net_queue)

    # ── Telegram ───────────────────────────────────────────────────────────────

    def start_bot_polling(self) -> None:
        self.bot.start_polling_in_background()
        self.pooling_state.set(locale.t("controls.connecting"))
        self._poll_status_update()

    def _poll_status_update(self) -> None:
        if self.bot.is_polling:
            self.pooling_state.set(locale.t("controls.connecting"))
            self.after(BOT_STATUS_POLL_MS, self._poll_status_update)
        else:
            self.pooling_state.set(locale.t("controls.connect_tg"))

    def _send_roll_to_telegram(self, record: RollRecord) -> None:
        all_dice = record.dice + record.specialisation_dice
        roll_label = (
            locale.t("controls.damage_soak")
            if record.roll_type == "DAMAGE"
            else "roll"
        )
        msg = (
            f"<b><i>{self.character.character_name.get()}</i> {roll_label}:</b>\n"
            f"<i>{', '.join(map(str, all_dice))}</i>\n"
            f"on <b>{record.dice_number} dices</b> "
            f"with <b>difficulty {record.difficulty}</b>.\n"
            f"<b>It's a {record.outcome}!</b>\n\n"
            f"<b><u>Total successes: {record.successes}</u></b>\n"
            f"        Auto successes: {record.auto_success}\n"
            f"        Wounds penalty: {self.character.roll_penalty.get()} die(s)\n"
            f"        Needed at least {self.success_needed.get()} successes\n"
            f"Succeed {record.probability:.2f}%"
        )
        self.bot.send_async(msg)

    def _send_initiative_to_telegram(self, total: int, raw: int) -> None:
        char = self.character
        dex  = char.dex_value.get() + char.dex_boost.get()
        wits = char.wits_value.get()
        msg = (
            f"<b><i>{char.character_name.get()}</i> rolled #INITIATIVE</b>\n"
            f"Result: <b>{total}</b>\n"
            f"<i>Rolled {raw} + {dex} Dex + {wits} Wits</i>"
        )
        self.bot.send_async(msg)

    # ── Save / load ────────────────────────────────────────────────────────────

    def save_to_file(self) -> None:
        """Persist settings and current character (saved under its name)."""
        dotenv.set_key(str(ENV_FILE_PATH), "CHAT_ID",         str(self.bot.chat_id))
        dotenv.set_key(str(ENV_FILE_PATH), "THREAD_ID",       str(self.bot.thread_id))
        dotenv.set_key(str(ENV_FILE_PATH), "LANG_PREF",       locale.lang)
        dotenv.set_key(str(ENV_FILE_PATH), "THEME_PREF",      theme.mode)
        dotenv.set_key(str(ENV_FILE_PATH), "SESSION_CODE",      self.session_code.get())
        dotenv.set_key(str(ENV_FILE_PATH), "UNSKILLED_PENALTY", "1" if self.default_skill_penalty.get() else "0")
        dotenv.set_key(str(ENV_FILE_PATH), "CHARGEN_MIN_WILL",  "1" if self.chargen_min_will.get() else "0")
        filename = f"{self.character.character_name.get()}.json"
        dotenv.set_key(str(ENV_FILE_PATH), "LAST_CHARACTER",  filename)
        char_data = self.character.to_dict()
        char_data["quick_rolls"] = [
            {
                "attr": locale.reverse_lookup_en("sheet.attr_names", av.get()),
                "abil": locale.reverse_lookup_en("sheet.ability_names", bv.get()),
                "diff": dv.get(),
                "spec": sv.get(),
                "auto": autov.get(),
            }
            for av, bv, dv, sv, autov in self.quick_rolls
        ]
        char_data["quick_penalty"] = self.quick_penalty.get()
        save_path = CHARACTERS_DIR / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(char_data, f, indent=2, ensure_ascii=False)

    def load_from_file(self) -> None:
        """Restore settings and the last-used character from disk."""
        env = dotenv.dotenv_values(str(ENV_FILE_PATH))
        self.bot.chat_id   = env.get("CHAT_ID")   if env.get("CHAT_ID")   not in (None, "None", "") else None
        self.bot.thread_id = env.get("THREAD_ID") if env.get("THREAD_ID") not in (None, "None", "") else None
        self.session_code.set(env.get("SESSION_CODE", ""))
        self.default_skill_penalty.set(env.get("UNSKILLED_PENALTY", "1") == "1")
        self.chargen_min_will.set(env.get("CHARGEN_MIN_WILL", "0") == "1")

        if not self._try_load_character(env):
            self.save_to_file()
            return

        self._interface.refresh_blood_cells()
        self.character.apply_trackers()

    def _try_load_character(self, env: dict) -> bool:
        """Attempt to load a character, with legacy migration as fallback.

        Priority:
        1. File named in LAST_CHARACTER env key inside CHARACTERS_DIR.
        2. Legacy character.json in APP_DATA_DIR (migrated on first load).

        Returns True if a character was loaded.
        """
        last = env.get("LAST_CHARACTER", "")
        if last:
            path = CHARACTERS_DIR / last
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                self.character.load(data)
                self._load_quick_rolls(data)
                return True

        # One-time migration from the old single-file storage.
        if CHARACTER_FILE_PATH.exists():
            with open(CHARACTER_FILE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            self.character.load(data)
            self.character.save()   # writes to CHARACTERS_DIR / {name}.json
            logger.info("Migrated legacy character.json → CHARACTERS_DIR")
            return True

        return False

    def load_character_dialog(self) -> None:
        """Open a file picker, copy the selected JSON to CHARACTERS_DIR, and load it."""
        src = filedialog.askopenfilename(
            title=locale.t("controls.load_character"),
            filetypes=[("JSON files", "*.json")],
            initialdir=CHARACTERS_DIR,
        )
        if not src:
            return

        src_path = Path(src)
        try:
            with open(src_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            messagebox.showerror("Load Character", str(exc))
            return

        name = data.get("header", {}).get("character_name") or src_path.stem
        dst = CHARACTERS_DIR / f"{name}.json"

        if dst.exists() and dst.resolve() != src_path.resolve():
            if not messagebox.askyesno(
                "Load Character",
                f"'{name}' already exists in your characters folder. Overwrite?",
            ):
                return

        if src_path.resolve() != dst.resolve():
            shutil.copy2(src_path, dst)

        self.character.load(data)
        self._load_quick_rolls(data)
        self._interface.refresh_blood_cells()
        self.character.apply_trackers()
        self.save_to_file()

    def _load_quick_rolls(self, data: dict) -> None:
        for (attr_var, abil_var, diff_var, spec_var, auto_var), entry in zip(
            self.quick_rolls, data.get("quick_rolls", [])
        ):
            attr_name = entry.get("attr", "")
            abil_name = entry.get("abil", "")
            attr_var.set(locale.translate_known("sheet.attr_names", attr_name))
            abil_var.set(locale.translate_known("sheet.ability_names", abil_name))
            diff_var.set(entry.get("diff", 6))
            spec_var.set(bool(entry.get("spec", False)))
            auto_var.set(int(entry.get("auto", 0)))
        self.quick_penalty.set(data.get("quick_penalty", 0))

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def scaler(value: str, var: IntVar) -> None:
        var.set(int(float(value)))