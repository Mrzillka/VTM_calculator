"""Tests for the roll pipeline on ui.storyteller.root.StorytellerRoot.

Same approach as the player root: build via ``object.__new__`` and wire only
the state the roll methods read, so we exercise the real methods without
spinning up the Storyteller UI.
"""
from __future__ import annotations

import queue
from tkinter import BooleanVar, IntVar, StringVar

import pytest

from game.models import RollRecord
from ui.storyteller.constants import NO_ROLLER
from ui.storyteller.root import StorytellerRoot


@pytest.fixture
def patch_dice(monkeypatch):
    def _install(face):
        monkeypatch.setattr("game.roller.randint", lambda _a, _b: face)
    return _install


class _FakeSession:
    def __init__(self):
        self.published = []

    def publish(self, msg_type, data):
        self.published.append((msg_type, data))


@pytest.fixture
def sroot(tk_root):
    r = object.__new__(StorytellerRoot)
    r.after = lambda *a, **k: None

    r.dice_number = IntVar(value=5)
    r.difficulty = IntVar(value=6)
    r.success_needed = IntVar(value=1)
    r.auto_success = IntVar(value=0)
    r.specialisation = BooleanVar(value=False)
    r.active_roller = StringVar(value=NO_ROLLER)

    r.roll_history = []
    r._on_roll_callbacks = []
    r._session = None
    r._net_queue = queue.Queue()
    return r


# ── _active_roller_name ──────────────────────────────────────────────────────

def test_active_roller_name_maps_sentinel_to_empty(sroot):
    sroot.active_roller.set(NO_ROLLER)
    assert sroot._active_roller_name() == ""


def test_active_roller_name_passes_through_real_name(sroot):
    sroot.active_roller.set("Prince LaCroix")
    assert sroot._active_roller_name() == "Prince LaCroix"


# ── roll_and_calculate ───────────────────────────────────────────────────────

def test_roll_uses_active_roller_name(sroot, patch_dice):
    patch_dice(7)
    sroot.active_roller.set("Smiling Jack")
    sroot.roll_and_calculate()
    rec = sroot.roll_history[0]
    assert rec.roll_type == "NORMAL"
    assert rec.roller_name == "Smiling Jack"
    assert rec.successes == 5


def test_storyteller_roll_has_no_wound_penalty(sroot, patch_dice):
    # Unlike the player, the Storyteller's generic roll applies no penalty.
    patch_dice(7)
    sroot.roll_and_calculate()
    assert sroot.roll_history[0].dice_number == 5
    assert sroot.roll_history[0].roller_name == ""   # NO_ROLLER -> empty


# ── roll_damage_soak ─────────────────────────────────────────────────────────

def test_damage_roll_ignores_botches(sroot, patch_dice):
    patch_dice(1)
    sroot.roll_damage_soak()
    rec = sroot.roll_history[0]
    assert rec.roll_type == "DAMAGE"
    assert rec.successes == 0


# ── roll_initiative (dice_number repurposed as flat bonus) ───────────────────

def test_initiative_adds_dice_number_as_flat_bonus(sroot, monkeypatch):
    monkeypatch.setattr("random.randint", lambda _a, _b: 7)
    sroot.dice_number.set(3)                   # used as the +bonus, not a pool
    sroot.roll_initiative()
    rec = sroot.roll_history[0]
    assert rec.roll_type == "INITIATIVE"
    assert rec.dice == [7]
    assert rec.auto_success == 3
    assert rec.successes == 10                 # 7 + 3


# ── npc_quick_roll ───────────────────────────────────────────────────────────

def test_npc_quick_roll_uses_toolbar_difficulty_and_pool(sroot, patch_dice):
    patch_dice(7)
    sroot.difficulty.set(6)
    sroot.npc_quick_roll("Sabbat Pack", dice_pool=4, no_botch=False)
    rec = sroot.roll_history[0]
    assert rec.roll_type == "QUICK"
    assert rec.roller_name == "Sabbat Pack"
    assert rec.dice_number == 4                # raw pool recorded
    assert rec.difficulty == 6
    assert rec.successes == 4


def test_npc_quick_roll_no_botch(sroot, patch_dice):
    patch_dice(1)
    sroot.npc_quick_roll("Ghoul", dice_pool=3, no_botch=True)
    assert sroot.roll_history[0].successes == 0   # 1s ignored


def test_npc_quick_roll_floors_pool_at_one(sroot, patch_dice):
    patch_dice(7)
    # dice_pool 0 -> effective pool of 1 die rolled, but raw 0 is recorded.
    sroot.npc_quick_roll("Mortal", dice_pool=0, no_botch=False)
    rec = sroot.roll_history[0]
    assert rec.dice_number == 0
    assert len(rec.dice) == 1


# ── _record_and_emit / polling ───────────────────────────────────────────────

def test_record_and_emit_notifies_and_publishes(sroot):
    seen = []
    sroot.on_roll(seen.append)
    sroot._session = _FakeSession()

    rec = RollRecord(1, 6, 0, [7], [], 1, 50.0, roller_name="X")
    sroot._record_and_emit(rec)
    assert seen == [rec]
    assert sroot._session.published[0][0] == "roll"


def test_poll_net_queue_appends_inbound_roll(sroot):
    seen = []
    sroot.on_roll(seen.append)
    sroot._net_queue.put((
        "roll",
        {"dice_number": 2, "difficulty": 7, "auto_success": 0,
         "dice": [9, 1], "spec_dice": [], "successes": 0,
         "probability": 40.0, "roller_name": "Player1", "roll_type": "NORMAL"},
    ))
    sroot._poll_net_queue()
    assert len(sroot.roll_history) == 1
    assert sroot.roll_history[0].roller_name == "Player1"
    assert seen[0].outcome == "FAILURE"
