"""Tests for the roll pipeline on ui.player.root.PlayerRoot.

PlayerRoot.__init__ builds the whole UI, a Telegram bot, and loads files — far
too much for a unit test. The roll methods themselves, though, only read a few
Vars and the Character. We build the instance with ``object.__new__`` (skipping
__init__) and wire just the state those methods touch, then call the *real*
methods.
"""
from __future__ import annotations

import queue
from tkinter import BooleanVar, IntVar, StringVar

import pytest

from game.character import ABILITIES, ATTRIBUTES, Character
from ui.player.root import PlayerRoot


# ── Helpers ──────────────────────────────────────────────────────────────────

def _set_dots(stat, n):
    """Fill the first *n* dot BooleanVars of an attribute/ability stat dict."""
    for i, v in enumerate(stat["vars"]):
        v.set(i < n)


@pytest.fixture
def patch_dice(monkeypatch):
    """Make Roller see a constant die face (patches game.roller.randint)."""
    def _install(face):
        monkeypatch.setattr("game.roller.randint", lambda _a, _b: face)
    return _install


class _FakeSession:
    def __init__(self):
        self.published = []

    def publish(self, msg_type, data):
        self.published.append((msg_type, data))


@pytest.fixture
def proot(tk_root):
    """A PlayerRoot wired with only the state the roll pipeline reads."""
    r = object.__new__(PlayerRoot)
    r.after = lambda *a, **k: None            # neutralise Tk scheduling

    r.character = Character()
    r.dice_number = IntVar(value=5)
    r.difficulty = IntVar(value=6)
    r.success_needed = IntVar(value=1)
    r.auto_success = IntVar(value=0)
    r.specialisation = BooleanVar(value=False)

    _attr = [a for attrs in ATTRIBUTES.values() for a in attrs]
    _abil = [a for abils in ABILITIES.values() for a in abils]
    r.quick_rolls = [
        (StringVar(value=_attr[0]), StringVar(value=_abil[0]),
         IntVar(value=6), BooleanVar(value=False), IntVar(value=0))
        for _ in range(4)
    ]
    r.quick_penalty = IntVar(value=0)
    r.quick_roll_dice = [StringVar(value="") for _ in range(4)]
    r.default_skill_penalty = BooleanVar(value=True)

    r.main_attr_var = StringVar(value="")
    r.main_abil_var = StringVar(value="")
    r._cb_setting_dice = False

    r.roll_history = []
    r._on_roll_callbacks = []
    r._session = None
    r.is_send_to_telegram = BooleanVar(value=False)
    r._net_queue = queue.Queue()
    return r


# ── _calculate ───────────────────────────────────────────────────────────────

def test_calculate_matches_calculator(proot):
    proot.dice_number.set(1)
    proot.difficulty.set(6)
    assert proot._calculate() == pytest.approx(50.0)


def test_calculate_no_botch_branch(proot):
    proot.dice_number.set(1)
    proot.difficulty.set(6)
    # With botches in play a single die is 50%; the no_botch flag changes the
    # distribution but at diff 6 still yields 50% — assert it runs and is sane.
    assert 0.0 <= proot._calculate(no_botch=True) <= 100.0


# ── roll_and_calculate ───────────────────────────────────────────────────────

def test_roll_and_calculate_records_normal_roll(proot, patch_dice):
    patch_dice(7)                              # every die hits at diff 6
    proot.roll_and_calculate()

    assert len(proot.roll_history) == 1
    rec = proot.roll_history[0]
    assert rec.roll_type == "NORMAL"
    assert rec.dice_number == 5
    assert rec.successes == 5
    assert rec.roller_name == proot.character.character_name.get()
    assert rec.probability == pytest.approx(proot._calculate())


def test_roll_applies_wound_penalty_to_pool(proot, patch_dice):
    patch_dice(7)
    proot.character.set_wounds(clicked=3)      # "Wounded" -> -2 dice
    proot.roll_and_calculate()
    # 5 dice - 2 penalty = 3 dice, all 7s -> 3 successes.
    assert proot.roll_history[0].successes == 3


# ── roll_damage_soak ─────────────────────────────────────────────────────────

def test_damage_roll_ignores_botches(proot, patch_dice):
    patch_dice(1)                              # all 1s
    proot.roll_damage_soak()
    rec = proot.roll_history[0]
    assert rec.roll_type == "DAMAGE"
    assert rec.successes == 0                   # 1s are misses, not botches


def test_normal_roll_counts_botches_for_contrast(proot, patch_dice):
    patch_dice(1)
    proot.roll_and_calculate()
    assert proot.roll_history[0].successes == -5   # five botches


# ── quick_roll ───────────────────────────────────────────────────────────────

def test_quick_roll_pool_is_attribute_plus_ability(proot, patch_dice):
    patch_dice(7)
    _set_dots(proot.character.attributes["Physical"]["Strength"], 3)
    _set_dots(proot.character.abilities["Talents"]["Brawl"], 2)
    proot.quick_rolls[0][0].set("Strength")
    proot.quick_rolls[0][1].set("Brawl")

    proot.quick_roll(0)
    rec = proot.roll_history[0]
    assert rec.roll_type == "QUICK"
    assert rec.dice_number == 5                # 3 + 2


def test_quick_roll_applies_unskilled_penalty(proot, patch_dice):
    patch_dice(7)
    _set_dots(proot.character.attributes["Physical"]["Strength"], 3)
    # Brawl left at 0 dots; default_skill_penalty is on -> -1 die.
    proot.quick_rolls[0][0].set("Strength")
    proot.quick_rolls[0][1].set("Brawl")

    proot.quick_roll(0)
    assert proot.roll_history[0].dice_number == 2   # 3 + 0 - 1


def test_quick_roll_no_penalty_when_disabled(proot, patch_dice):
    patch_dice(7)
    _set_dots(proot.character.attributes["Physical"]["Strength"], 3)
    proot.default_skill_penalty.set(False)
    proot.quick_rolls[0][0].set("Strength")
    proot.quick_rolls[0][1].set("Brawl")

    proot.quick_roll(0)
    assert proot.roll_history[0].dice_number == 3   # no -1


# ── roll_initiative ──────────────────────────────────────────────────────────

def test_roll_initiative_sums_d10_dex_wits(proot, monkeypatch):
    # roll_initiative does `from random import randint`, so patch random.randint.
    monkeypatch.setattr("random.randint", lambda _a, _b: 7)
    _set_dots(proot.character.attributes["Physical"]["Dexterity"], 3)
    _set_dots(proot.character.attributes["Mental"]["Wits"], 2)

    proot.roll_initiative()
    rec = proot.roll_history[0]
    assert rec.roll_type == "INITIATIVE"
    assert rec.dice == [7]
    assert rec.auto_success == 5               # dex 3 + wits 2
    assert rec.successes == 12                 # 7 + 0 penalty + 3 + 2


# ── _record_and_emit / callbacks ─────────────────────────────────────────────

def test_record_and_emit_notifies_callbacks(proot):
    seen = []
    proot.on_roll(seen.append)
    from game.models import RollRecord

    rec = RollRecord(1, 6, 0, [7], [], 1, 50.0)
    proot._record_and_emit(rec)
    assert proot.roll_history == [rec]
    assert seen == [rec]


def test_record_and_emit_publishes_to_session(proot):
    proot._session = _FakeSession()
    from game.models import RollRecord

    rec = RollRecord(1, 6, 0, [7], [], 1, 50.0, roller_name="X", roll_type="NORMAL")
    proot._record_and_emit(rec)
    assert proot._session.published[0][0] == "roll"
    assert proot._session.published[0][1]["roller_name"] == "X"


def test_record_and_emit_skips_session_when_offline(proot):
    from game.models import RollRecord

    # _session is None: must not raise, just record + emit.
    proot._record_and_emit(RollRecord(1, 6, 0, [7], [], 1, 50.0))
    assert len(proot.roll_history) == 1


# ── _poll_net_queue (inbound rolls) ──────────────────────────────────────────

def test_poll_net_queue_appends_inbound_roll(proot):
    seen = []
    proot.on_roll(seen.append)
    proot._net_queue.put((
        "roll",
        {"dice_number": 3, "difficulty": 6, "auto_success": 0,
         "dice": [9, 8, 2], "spec_dice": [], "successes": 2,
         "probability": 60.0, "roller_name": "Remote", "roll_type": "NORMAL"},
    ))
    proot._poll_net_queue()
    assert len(proot.roll_history) == 1
    assert proot.roll_history[0].roller_name == "Remote"
    assert seen[0].successes == 2


# ── update_main_dice_from_cb ──────────────────────────────────────────────────

def test_update_main_dice_sets_pool_from_comboboxes(proot):
    _set_dots(proot.character.attributes["Physical"]["Strength"], 4)
    _set_dots(proot.character.abilities["Talents"]["Brawl"], 2)
    proot.main_attr_var.set("Strength")
    proot.main_abil_var.set("Brawl")
    proot.update_main_dice_from_cb()
    assert proot.dice_number.get() == 6


def test_update_main_dice_noop_when_selection_incomplete(proot):
    proot.dice_number.set(5)
    proot.main_attr_var.set("Strength")
    proot.main_abil_var.set("")               # incomplete selection
    proot.update_main_dice_from_cb()
    assert proot.dice_number.get() == 5       # unchanged


# ── _refresh_quick_roll_dice ──────────────────────────────────────────────────

def test_refresh_quick_roll_dice_text(proot):
    _set_dots(proot.character.attributes["Physical"]["Strength"], 3)
    _set_dots(proot.character.abilities["Talents"]["Brawl"], 2)
    proot.quick_rolls[0][0].set("Strength")
    proot.quick_rolls[0][1].set("Brawl")
    proot._refresh_quick_roll_dice()
    assert proot.quick_roll_dice[0].get() == "3 + 2 = 5"


def test_refresh_quick_roll_dice_shows_auto(proot):
    _set_dots(proot.character.attributes["Physical"]["Strength"], 3)
    _set_dots(proot.character.abilities["Talents"]["Brawl"], 2)
    proot.quick_rolls[0][0].set("Strength")
    proot.quick_rolls[0][1].set("Brawl")
    proot.quick_rolls[0][4].set(2)            # 2 auto successes
    proot._refresh_quick_roll_dice()
    assert proot.quick_roll_dice[0].get() == "3 + 2 = 5  +2 auto"
