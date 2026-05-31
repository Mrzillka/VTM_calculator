"""Tests for network.protocol — RollRecord <-> dict codecs and message types."""
from __future__ import annotations

import pytest

from game.models import RollRecord
from network.protocol import (
    MSG_ROLL,
    MSG_SHEET,
    MSG_SHEET_TRACKERS,
    dict_to_roll_record,
    roll_record_to_dict,
)


def _record(**overrides):
    base = dict(
        dice_number=5,
        difficulty=6,
        auto_success=1,
        dice=[9, 7, 4, 2, 1],
        specialisation_dice=[8],
        successes=3,
        probability=72.5,
        roller_name="Caine",
        roll_type="DAMAGE",
    )
    base.update(overrides)
    return RollRecord(**base)


# ── Message-type identifiers ─────────────────────────────────────────────────

def test_message_type_values():
    assert MSG_ROLL == "roll"
    assert MSG_SHEET == "sheet"
    assert MSG_SHEET_TRACKERS == "sheet_trackers"


# ── Encode ───────────────────────────────────────────────────────────────────

def test_roll_record_to_dict_maps_every_field():
    d = roll_record_to_dict(_record())
    assert d == {
        "dice_number": 5,
        "difficulty": 6,
        "auto_success": 1,
        "dice": [9, 7, 4, 2, 1],
        "spec_dice": [8],          # note the rename from specialisation_dice
        "successes": 3,
        "probability": 72.5,
        "roller_name": "Caine",
        "roll_type": "DAMAGE",
    }


# ── Decode ───────────────────────────────────────────────────────────────────

def test_dict_to_roll_record_reconstructs_fields():
    record = dict_to_roll_record(roll_record_to_dict(_record()))
    assert record.specialisation_dice == [8]
    assert record.roller_name == "Caine"
    assert record.roll_type == "DAMAGE"


def test_dict_to_roll_record_defaults_optional_fields():
    d = roll_record_to_dict(_record())
    del d["roller_name"]
    del d["roll_type"]
    record = dict_to_roll_record(d)
    assert record.roller_name == ""        # default: Storyteller rolled
    assert record.roll_type == "NORMAL"


def test_dict_to_roll_record_requires_core_fields():
    d = roll_record_to_dict(_record())
    del d["dice_number"]
    with pytest.raises(KeyError):
        dict_to_roll_record(d)


# ── Round trip ───────────────────────────────────────────────────────────────

def test_codec_round_trip_is_identity():
    original = _record()
    assert dict_to_roll_record(roll_record_to_dict(original)) == original


def test_round_trip_preserves_outcome():
    botch = _record(successes=-2)
    restored = dict_to_roll_record(roll_record_to_dict(botch))
    assert restored.outcome == "BOTCH"
