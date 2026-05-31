"""Tests for game.chargen — CharGen helpers and the creation data tables."""
from __future__ import annotations

from game.chargen import (
    AFFILIATIONS,
    CLAN_DISCIPLINES,
    CLANS,
    GENERATION_CHOICES,
    CharGen,
)


# ── rules_for ────────────────────────────────────────────────────────────────

def test_rules_for_known_affiliation():
    assert CharGen.rules_for("Sabbat") is AFFILIATIONS["Sabbat"]


def test_rules_for_unknown_affiliation_falls_back_to_camarilla():
    assert CharGen.rules_for("Nonexistent") is AFFILIATIONS["Camarilla"]


# ── clan_disciplines ─────────────────────────────────────────────────────────

def test_clan_disciplines_known_clan():
    assert CharGen.clan_disciplines("Tremere") == ("Auspex", "Dominate", "Thaumaturgy")


def test_clan_disciplines_unknown_clan_is_empty():
    assert CharGen.clan_disciplines("Not A Clan") == ()


def test_caitiff_has_no_clan_disciplines():
    assert CharGen.clan_disciplines("Caitiff") == ()


# ── dots_in_category (needs a real Character) ────────────────────────────────

def test_dots_in_category_sums_attribute_dots(character):
    phys = character.attributes["Physical"]
    # Strength = 3 dots, Dexterity = 2 dots.
    for v in phys["Strength"]["vars"][:3]:
        v.set(True)
    for v in phys["Dexterity"]["vars"][:2]:
        v.set(True)
    assert CharGen.dots_in_category(character, "Physical", "attributes") == 5


def test_dots_in_category_sums_ability_dots(character):
    talents = character.abilities["Talents"]
    for v in talents["Brawl"]["vars"][:4]:
        v.set(True)
    assert CharGen.dots_in_category(character, "Talents", "abilities") == 4


def test_dots_in_category_unknown_source_is_zero(character):
    assert CharGen.dots_in_category(character, "Physical", "bogus") == 0


# ── Data-table integrity ─────────────────────────────────────────────────────

def test_every_clan_has_a_discipline_entry():
    for clan in CLANS:
        assert clan in CLAN_DISCIPLINES, clan


def test_non_caitiff_clans_have_three_disciplines():
    for clan, discs in CLAN_DISCIPLINES.items():
        if clan == "Caitiff":
            assert discs == ()
        else:
            assert len(discs) == 3, clan


def test_affiliation_pools_are_three_tiered():
    for name, rules in AFFILIATIONS.items():
        assert len(rules.attr_pools) == 3, name
        assert len(rules.ability_pools) == 3, name


def test_generation_choices_are_formatted_ordinals():
    assert GENERATION_CHOICES[0] == "4th"
    assert GENERATION_CHOICES[-1] == "15th"
    assert len(GENERATION_CHOICES) == 12
