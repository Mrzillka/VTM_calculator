"""Tests for game.calculator.Calculator — exact success probability via DP.

Because the calculator is exact (it convolves a single-die distribution rather
than sampling), every expected value here is computed by hand from the VTM die
faces, not from a statistical tolerance.
"""
from __future__ import annotations

import math

import pytest

from game.calculator import Calculator


def approx(value):
    return pytest.approx(value, abs=1e-9)


# ── Single-die analytic cases ────────────────────────────────────────────────

def test_single_die_difficulty_six():
    # Faces 6-10 succeed (net >= 1): 5/10 = 50%.
    assert Calculator(dice_number=1, difficulty=6).get_probability() == approx(50.0)


def test_single_die_difficulty_eight():
    # Faces 8,9,10 hit -> 3/10 = 30%.
    assert Calculator(dice_number=1, difficulty=8).get_probability() == approx(30.0)


def test_single_die_no_botch_difficulty_six():
    # no_botch: faces 6-10 hit, 1-5 miss -> 50%.
    assert (
        Calculator(dice_number=1, difficulty=6, no_botch=True).get_probability()
        == approx(50.0)
    )


# ── Multi-die cases (botches subtract, so it is NOT 1-(1-p)^n) ────────────────

def test_two_dice_difficulty_six_one_success():
    # Per die net: -1 @ .1, 0 @ .4, +1 @ .5. P(sum >= 1) = 1 - P(sum <= 0).
    # P(sum<=0) = .01 + 2(.04) + .16 + 2(.05) = .35  ->  65%.
    assert (
        Calculator(dice_number=2, difficulty=6, success_needed=1).get_probability()
        == approx(65.0)
    )


def test_needing_more_successes_than_dice_is_impossible_without_botch_help():
    # 2 dice cannot net 3 successes (max +1 per die, no spec) -> 0%.
    assert (
        Calculator(dice_number=2, difficulty=6, success_needed=3).get_probability()
        == approx(0.0)
    )


# ── Auto successes lower the dice threshold ──────────────────────────────────

def test_auto_successes_offset_required_successes():
    # success_needed 2 with 1 auto == needing 1 net from a single die = 50%.
    assert (
        Calculator(
            dice_number=1, difficulty=6, success_needed=2, auto_successes=1
        ).get_probability()
        == approx(50.0)
    )


def test_auto_successes_do_not_shield_against_botches():
    # success_needed 2 with 2 autos drops the dice threshold to 0, but a single
    # die can still roll a 1 (botch, net -1) and pull the total below 2. So the
    # roll is NOT certain: P = 1 - P(botch) = 1 - 1/10 = 90%.
    assert (
        Calculator(
            dice_number=1, difficulty=6, success_needed=2, auto_successes=2
        ).get_probability()
        == approx(90.0)
    )


# ── Specialisation strictly helps ────────────────────────────────────────────

def test_specialisation_never_lowers_probability():
    plain = Calculator(dice_number=3, difficulty=6, success_needed=2).get_probability()
    spec = Calculator(
        dice_number=3, difficulty=6, success_needed=2, specialisation=True
    ).get_probability()
    assert spec >= plain


# ── Distribution integrity ───────────────────────────────────────────────────

def test_single_die_distribution_sums_to_one():
    for difficulty in range(2, 11):
        for no_botch in (False, True):
            for spec in (False, True):
                calc = Calculator(
                    difficulty=difficulty, no_botch=no_botch, specialisation=spec
                )
                total = sum(calc._single_die_distribution().values())
                assert total == pytest.approx(1.0, abs=1e-9), (
                    difficulty,
                    no_botch,
                    spec,
                )


def test_probability_is_a_percentage():
    p = Calculator(dice_number=6, difficulty=6, success_needed=3).get_probability()
    assert 0.0 <= p <= 100.0


def test_higher_difficulty_reduces_probability():
    easy = Calculator(dice_number=5, difficulty=4, success_needed=2).get_probability()
    hard = Calculator(dice_number=5, difficulty=9, success_needed=2).get_probability()
    assert easy > hard
