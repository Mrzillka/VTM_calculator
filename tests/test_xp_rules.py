"""Tests for game.xp_rules.xp_for_increase — V20 experience costs.

Cost model: each increment to rating R costs (R-1) x multiplier, with flat
first-dot special cases for new abilities and out-of-clan disciplines.
"""
from __future__ import annotations

import pytest

from game.xp_rules import XP_COSTS, xp_for_increase


# ── No-op / guard cases ──────────────────────────────────────────────────────

def test_no_increase_costs_nothing():
    assert xp_for_increase("attribute", 3, 3) == 0
    assert xp_for_increase("attribute", 4, 2) == 0


def test_unknown_trait_type_costs_nothing():
    # Falsy trait_type hits the final ``else: return total`` with nothing added.
    assert xp_for_increase("", 0, 3) == 0


# ── Attributes: (target) x 4 per dot ─────────────────────────────────────────

def test_attribute_single_step():
    # 2 -> 3 costs (3-1)*4 = 8.
    assert xp_for_increase("attribute", 2, 3) == 8


def test_attribute_multi_step_sums_each_dot():
    # 1 -> 3: (2-1)*4 + (3-1)*4 = 4 + 8 = 12.
    assert xp_for_increase("attribute", 1, 3) == 12


# ── Abilities: flat 3 for the first dot, then (target-1) x 2 ──────────────────

def test_ability_first_dot_is_flat():
    assert xp_for_increase("ability", 0, 1) == XP_COSTS["new_ability"] == 3


def test_ability_zero_to_two():
    # flat 3 (0->1) + (2-1)*2 = 3 + 2 = 5.
    assert xp_for_increase("ability", 0, 2) == 5


def test_ability_existing_dot_no_flat_cost():
    # 1 -> 2: (2-1)*2 = 2.
    assert xp_for_increase("ability", 1, 2) == 2


def test_secondary_ability_first_dot_is_flat_two():
    assert (
        xp_for_increase("secondary_ability", 0, 1)
        == XP_COSTS["new_secondary_ability"]
        == 2
    )


# ── Disciplines: in-clan x5, out-of-clan x7 per dot ──────────────────────────

def test_discipline_inclan_step():
    # 1 -> 2 in clan: (2-1)*5 = 5.
    assert xp_for_increase("discipline", 1, 2, is_inclan=True) == 5


def test_discipline_outclan_step():
    # 1 -> 2 out of clan: (2-1)*7 = 7.
    assert xp_for_increase("discipline", 1, 2, is_inclan=False) == 7


def test_discipline_outclan_first_dot_flat():
    # flat 10 for the new out-of-clan discipline, no per-dot on top of 0->1.
    assert (
        xp_for_increase("discipline", 0, 1, is_inclan=False)
        == XP_COSTS["new_discipline_outclan"]
        == 10
    )


def test_discipline_first_dot_charges_flat_regardless_of_clan():
    # CHARACTERIZATION: the 0->1 flat branch fires for any discipline, so even an
    # *in-clan* first dot is billed the 10-XP out-of-clan flat cost. Flagging in
    # case this should instead be 10 (out) vs the standard new-discipline rule.
    assert xp_for_increase("discipline", 0, 1, is_inclan=True) == 10


# ── Linear traits: virtue x2, willpower x1, humanity x2 ──────────────────────

def test_virtue_cost():
    # 1 -> 3: (2-1)*2 + (3-1)*2 = 2 + 4 = 6.
    assert xp_for_increase("virtue", 1, 3) == 6


def test_willpower_cost():
    # 5 -> 7: (6-1)*1 + (7-1)*1 = 5 + 6 = 11.
    assert xp_for_increase("willpower", 5, 7) == 11


def test_humanity_cost():
    # 4 -> 5: (5-1)*2 = 8.
    assert xp_for_increase("humanity", 4, 5) == 8


def test_background_is_free_under_this_table():
    # background multiplier is 0, so increments cost nothing here.
    assert xp_for_increase("background", 0, 3) == 0
