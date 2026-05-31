"""Data-integrity tests for game.discipline_rules.

These tables are hand-authored, so the tests act as a guard rail against typos:
out-of-range levels/difficulties, half-specified rolls, or combos that reference
a discipline that does not exist.
"""
from __future__ import annotations

import pytest

from game.discipline_rules import (
    COMBO_DISCIPLINES,
    DISCIPLINE_POWERS,
    ComboDiscipline,
    DisciplinePower,
)


def _all_powers():
    return [p for powers in DISCIPLINE_POWERS.values() for p in powers]


# ── DisciplinePower invariants ───────────────────────────────────────────────

def test_every_discipline_has_powers():
    for name, powers in DISCIPLINE_POWERS.items():
        assert powers, name


def test_power_levels_in_range():
    for p in _all_powers():
        assert 1 <= p.level <= 5, p.name


def test_power_difficulty_in_range():
    for p in _all_powers():
        assert 2 <= p.difficulty <= 10, p.name


def test_power_blood_cost_non_negative():
    for p in _all_powers():
        assert p.blood_cost >= 0, p.name


def test_rollable_powers_describe_how_to_roll():
    # A power that requires a roll (not automatic) must say what to roll: either
    # the standard attribute+ability pair, or a free-form roll spelled out in
    # notes (e.g. a flat Willpower roll like "Lighter").
    for p in _all_powers():
        if not p.is_automatic:
            has_pair = p.attribute is not None and p.ability is not None
            assert has_pair or p.notes, p.name


def test_attribute_and_ability_are_set_together_or_not_at_all():
    # No half-specified rolls (one of the pair present, the other missing).
    for p in _all_powers():
        assert (p.attribute is None) == (p.ability is None), p.name


# ── ComboDiscipline invariants ───────────────────────────────────────────────

def test_combos_require_at_least_one_discipline():
    for combo in COMBO_DISCIPLINES:
        assert combo.requires, combo.name


def test_combo_requirements_reference_real_disciplines():
    valid = set(DISCIPLINE_POWERS)
    for combo in COMBO_DISCIPLINES:
        for disc_name, min_dots in combo.requires:
            assert disc_name in valid, f"{combo.name} -> {disc_name}"
            assert 1 <= min_dots <= 5, f"{combo.name} -> {disc_name} {min_dots}"


def test_combo_xp_cost_is_positive():
    for combo in COMBO_DISCIPLINES:
        assert combo.xp_cost > 0, combo.name


def test_combo_names_are_unique():
    names = [c.name for c in COMBO_DISCIPLINES]
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, duplicates


def test_non_automatic_combos_describe_how_to_roll():
    # Same rule as powers: a rollable combo names an attribute+ability pair, or
    # borrows another discipline's roll as described in notes (e.g. "Far Mastery").
    for combo in COMBO_DISCIPLINES:
        if not combo.is_automatic:
            has_pair = combo.attribute is not None and combo.ability is not None
            assert has_pair or combo.notes, combo.name


# ── Dataclass immutability ───────────────────────────────────────────────────

def test_dataclasses_are_frozen():
    power = _all_powers()[0]
    combo = COMBO_DISCIPLINES[0]
    with pytest.raises(Exception):
        power.level = 9  # type: ignore[misc]
    with pytest.raises(Exception):
        combo.xp_cost = 0  # type: ignore[misc]
    assert isinstance(power, DisciplinePower)
    assert isinstance(combo, ComboDiscipline)
