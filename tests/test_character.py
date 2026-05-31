"""Tests for game.character.Character mutation helpers.

These exercise the domain logic that lives on the model (blood/wound/willpower
trackers, blood-boosting, generation parsing, stat lookup). They need a live Tk
interpreter for the ``Var`` objects, supplied by the ``character`` fixture.
"""
from __future__ import annotations

import pytest

from config import BLOOD_COLS


# ── Blood pool ───────────────────────────────────────────────────────────────

def test_default_blood_matches_thirteenth_generation(character):
    # 13th gen blood_max is 10; the default character starts full.
    assert character.blood_value.get() == 10


def test_set_blood_click_fills_up_to_cell(character):
    # Click the 5th cell of the first row -> blood becomes 5.
    character.set_blood(row=0, col=4)
    assert character.blood_value.get() == 5
    filled = sum(v.get() for r in character.blood for v in r)
    assert filled == 5


def test_set_blood_clicking_last_filled_cell_toggles_it_off(character):
    character.set_blood(row=0, col=4)        # blood == 5, last filled is (0,4)
    character.set_blood(row=0, col=4)        # click it again
    assert character.blood_value.get() == 4


def test_set_blood_load_is_idempotent(character):
    character.blood_value.set(23)
    character.set_blood(load=True)
    assert character.blood_value.get() == 23
    filled = sum(v.get() for r in character.blood for v in r)
    assert filled == 23
    # 23 = 2 full rows + 3 cells.
    assert character.blood[2][2].get() is True
    assert character.blood[2][3].get() is False


# ── Wounds ───────────────────────────────────────────────────────────────────

def test_default_is_unharmed(character):
    assert character.wounds_value.get() == -1
    assert character.wounds_display.get() == "Unharmed"
    assert character.roll_penalty.get() == 0


def test_set_wounds_applies_level_penalty_and_label(character):
    character.set_wounds(clicked=2)          # index 2 == "Injured", penalty -1
    assert character.wounds_value.get() == 2
    assert character.roll_penalty.get() == -1
    assert character.wounds_display.get() == "Injured -1"


def test_set_wounds_clicking_last_dot_steps_down(character):
    character.set_wounds(clicked=2)          # fills 3 dots (level 2)
    character.set_wounds(clicked=2)          # click last filled -> step down
    assert character.wounds_value.get() == 1


def test_healing_costs_one_blood_and_one_wound(character):
    character.blood_value.set(5)
    character.set_blood(load=True)
    character.set_wounds(clicked=2)          # level 2
    character.heal()
    assert character.wounds_value.get() == 1
    assert character.blood_value.get() == 4


def test_healing_does_nothing_when_unharmed(character):
    character.blood_value.set(5)
    character.set_blood(load=True)
    character.heal()
    assert character.blood_value.get() == 5  # no blood spent


# ── Humanity / Willpower ─────────────────────────────────────────────────────

def test_set_humanity_fills_dots(character):
    character.set_humanity(clicked=6)        # fill up to 7
    assert character.humanity_value.get() == 7
    assert sum(v.get() for v in character.humanity) == 7


def test_set_will_toggle_off(character):
    character.set_will(clicked=4)            # fill 5
    character.set_will(clicked=4)            # click last -> step down to 4
    assert character.will_value.get() == 4


# ── Generation ───────────────────────────────────────────────────────────────

def test_parse_generation_reads_digits(character):
    character.generation.set("8th")
    assert character._parse_generation() == 8


def test_parse_generation_clamps_to_bounds(character):
    character.generation.set("99th")
    assert character._parse_generation() == 15  # MAX_GENERATION


def test_parse_generation_falls_back_on_garbage(character):
    character.generation.set("abc")
    assert character._parse_generation() == 13  # DEFAULT_GENERATION


def test_changing_generation_updates_blood_max_via_trace(character):
    character.generation.set("4th")          # 4th gen: blood_max 50, per-turn 6
    assert character.blood_max_value.get() == 50
    assert character.blood_per_turn.get() == "6"


# ── Blood boosting ───────────────────────────────────────────────────────────

def test_boost_attribute_spends_blood_and_raises_trait(character):
    for v in character.attributes["Physical"]["Strength"]["vars"][:3]:
        v.set(True)                          # Strength 3
    blood_before = character.blood_value.get()
    character.boost_attribute(
        character.str_boost, character.attributes["Physical"]["Strength"]["vars"]
    )
    assert character.str_boost.get() == 1
    assert character.blood_value.get() == blood_before - 1


def test_boost_attribute_respects_generation_trait_cap(character):
    # 13th gen cap is 5; Strength already at 5 -> boost refused, no blood spent.
    for v in character.attributes["Physical"]["Strength"]["vars"][:5]:
        v.set(True)
    blood_before = character.blood_value.get()
    character.boost_attribute(
        character.str_boost, character.attributes["Physical"]["Strength"]["vars"]
    )
    assert character.str_boost.get() == 0
    assert character.blood_value.get() == blood_before


def test_boost_attribute_needs_blood(character):
    character.blood_value.set(0)
    character.set_blood(load=True)
    for v in character.attributes["Physical"]["Strength"]["vars"][:2]:
        v.set(True)
    character.boost_attribute(
        character.str_boost, character.attributes["Physical"]["Strength"]["vars"]
    )
    assert character.str_boost.get() == 0


def test_end_scene_clears_boosts(character):
    character.str_boost.set(2)
    character.dex_boost.set(1)
    character.end_scene()
    assert character.str_boost.get() == 0
    assert character.dex_boost.get() == 0
    assert character.sta_boost.get() == 0


# ── Stat lookup ──────────────────────────────────────────────────────────────

def test_get_stat_value_for_attribute_includes_boost(character):
    for v in character.attributes["Physical"]["Strength"]["vars"][:3]:
        v.set(True)
    character.str_boost.set(1)
    assert character.get_stat_value("Strength") == 4


def test_get_stat_value_for_ability(character):
    for v in character.abilities["Talents"]["Brawl"]["vars"][:2]:
        v.set(True)
    assert character.get_stat_value("Brawl") == 2


def test_get_stat_value_for_named_discipline(character):
    character.disciplines[0]["name"].set("Auspex")
    for v in character.disciplines[0]["vars"][:3]:
        v.set(True)
    assert character.get_stat_value("Auspex") == 3


def test_get_stat_value_unknown_or_empty_is_zero(character):
    assert character.get_stat_value("") == 0
    assert character.get_stat_value("Nonexistent") == 0


# ── Pool name listing ────────────────────────────────────────────────────────

def test_all_pool_names_includes_abilities(character):
    names = character.all_pool_names()
    assert "Brawl" in names
    assert "Occult" in names


def test_all_pool_names_includes_set_disciplines_without_duplicates(character):
    character.disciplines[0]["name"].set("Dominate")
    character.disciplines[1]["name"].set("Dominate")  # duplicate must be de-duped
    names = character.all_pool_names()
    assert names.count("Dominate") == 1
