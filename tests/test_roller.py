"""Tests for game.roller.Roller — the VTM d10 pool roll."""
from __future__ import annotations

import pytest

from game.roller import Roller


@pytest.fixture
def patch_dice(monkeypatch):
    """Return a helper that makes ``randint`` yield a fixed sequence of faces.

    ``Roller`` imports ``randint`` into its own module namespace
    (``from random import randint``), so we patch ``game.roller.randint`` — the
    name the module actually calls — rather than ``random.randint``.
    """
    def _install(faces):
        it = iter(faces)

        def fake_randint(_low, _high):
            return next(it)

        monkeypatch.setattr("game.roller.randint", fake_randint)

    return _install


# ── Pool sizing ──────────────────────────────────────────────────────────────

def test_penalty_shrinks_the_pool(patch_dice):
    patch_dice([7, 7, 7])  # only 3 dice should be drawn
    result = Roller(dice_number=5, difficulty=6, penalty=-2).roll()
    assert len(result.dice) == 3


def test_positive_penalty_grows_the_pool(patch_dice):
    patch_dice([7, 7, 7, 7, 7, 7, 7])
    result = Roller(dice_number=5, penalty=2).roll()
    assert len(result.dice) == 7


def test_pool_never_drops_below_one(patch_dice):
    patch_dice([3])  # a single die even though penalty would imply -4
    result = Roller(dice_number=1, penalty=-5).roll()
    assert len(result.dice) == 1


# ── Success counting ─────────────────────────────────────────────────────────

def test_hits_are_faces_at_or_above_difficulty(patch_dice):
    patch_dice([6, 5, 9, 6])  # 6,9,6 hit at diff 6; 5 misses
    result = Roller(dice_number=4, difficulty=6).roll()
    assert result.successes == 3


def test_ones_are_botches_and_subtract(patch_dice):
    patch_dice([7, 1, 1, 8])  # 2 hits, 2 botches -> net 0
    result = Roller(dice_number=4, difficulty=6).roll()
    assert result.successes == 0


def test_no_botch_ignores_ones(patch_dice):
    patch_dice([7, 1, 1, 8])  # damage/soak: 1s don't subtract -> 2 hits
    result = Roller(dice_number=4, difficulty=6, no_botch=True).roll()
    assert result.successes == 2


def test_auto_success_is_added(patch_dice):
    patch_dice([5, 5, 5])  # zero hits from the dice
    result = Roller(dice_number=3, difficulty=6, auto_success=2).roll()
    assert result.successes == 2


def test_auto_success_combines_with_botches(patch_dice):
    patch_dice([1, 1])  # two botches, plus one auto -> net -1
    result = Roller(dice_number=2, difficulty=6, auto_success=1).roll()
    assert result.successes == -1


# ── Specialisation re-rolls ──────────────────────────────────────────────────

def test_specialisation_rerolls_each_ten_once(patch_dice):
    # Pool: 10, 7. The single 10 triggers one extra die (an 8 -> another hit).
    patch_dice([10, 7, 8])
    result = Roller(dice_number=2, difficulty=6, specialisation=True).roll()
    assert result.specialisation_dice == (8,)
    # 10 hits, 7 hits, spec 8 hits -> 3
    assert result.successes == 3


def test_specialisation_chains_on_repeated_tens(patch_dice):
    # 10 -> reroll 10 -> reroll 4. Two extra dice, recursive chain stops at 4.
    patch_dice([10, 10, 4])
    result = Roller(dice_number=1, difficulty=6, specialisation=True).roll()
    assert result.specialisation_dice == (10, 4)


def test_specialisation_dice_do_not_botch(patch_dice):
    # A spec die showing 1 must not subtract (only base-pool 1s botch).
    patch_dice([10, 1])  # base 10 hits; spec reroll is a 1
    result = Roller(dice_number=1, difficulty=6, specialisation=True).roll()
    assert result.successes == 1  # the 10, with the spec 1 ignored


def test_no_specialisation_means_no_extra_dice(patch_dice):
    patch_dice([10, 10])
    result = Roller(dice_number=2, difficulty=6, specialisation=False).roll()
    assert result.specialisation_dice == ()


# ── Result shape ─────────────────────────────────────────────────────────────

def test_dice_are_sorted_descending(patch_dice):
    patch_dice([3, 9, 1, 6])
    result = Roller(dice_number=4).roll()
    assert result.dice == (9, 6, 3, 1)


def test_all_dice_concatenates_pool_and_spec(patch_dice):
    patch_dice([10, 2, 5])  # pool 10,2 sorted -> (10,2); spec from the 10 -> 5
    result = Roller(dice_number=2, difficulty=6, specialisation=True).roll()
    assert result.all_dice == (10, 2, 5)


def test_default_difficulty_is_six(patch_dice):
    patch_dice([6])
    assert Roller(dice_number=1).roll().successes == 1
