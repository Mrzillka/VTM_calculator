"""Tests for game.models — RollResult / RollRecord and the outcome rule."""
from __future__ import annotations

import dataclasses

import pytest

from game.models import RollRecord, RollResult


# ── Outcome classification (shared by both models) ───────────────────────────

@pytest.mark.parametrize(
    "successes, expected",
    [
        (3, "SUCCESS"),
        (1, "SUCCESS"),
        (0, "FAILURE"),
        (-1, "BOTCH"),
        (-5, "BOTCH"),
    ],
)
def test_roll_result_outcome(successes, expected):
    result = RollResult(dice=(), specialisation_dice=(), successes=successes)
    assert result.outcome == expected


@pytest.mark.parametrize(
    "successes, expected",
    [(2, "SUCCESS"), (0, "FAILURE"), (-1, "BOTCH")],
)
def test_roll_record_outcome(successes, expected):
    record = RollRecord(
        dice_number=3,
        difficulty=6,
        auto_success=0,
        dice=[],
        specialisation_dice=[],
        successes=successes,
        probability=50.0,
    )
    assert record.outcome == expected


# ── RollResult helpers ───────────────────────────────────────────────────────

def test_all_dice_concatenates_pool_and_spec():
    result = RollResult(dice=(10, 7), specialisation_dice=(8,), successes=3)
    assert result.all_dice == (10, 7, 8)


def test_roll_result_is_frozen():
    result = RollResult(dice=(1,), specialisation_dice=(), successes=0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.successes = 5  # type: ignore[misc]


# ── RollRecord defaults ──────────────────────────────────────────────────────

def test_roll_record_defaults():
    record = RollRecord(
        dice_number=1,
        difficulty=6,
        auto_success=0,
        dice=[7],
        specialisation_dice=[],
        successes=1,
        probability=50.0,
    )
    # Empty roller_name means "the Storyteller rolled"; default type is NORMAL.
    assert record.roller_name == ""
    assert record.roll_type == "NORMAL"
