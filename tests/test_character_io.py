"""Tests for game.character_io.CharacterIO — serialization & persistence.

CharacterIO is a mixin on Character, so it is exercised through a real
``Character`` instance (the ``character`` fixture).
"""
from __future__ import annotations

import json


def _populate(character):
    """Put a character into a distinctive, fully-populated state."""
    character.character_name.set("Test Subject")
    character.player.set("Alice")
    character.chronicle.set("By Night")
    character.clan.set("Tremere")
    character.generation.set("7th")          # trace sets blood_max -> 20

    character.blood_value.set(8)
    character.wounds_value.set(2)
    character.humanity_value.set(6)
    character.will_value.set(5)
    character.willpower_max.set(9)
    character.xp_total.set(30)

    for v in character.attributes["Physical"]["Strength"]["vars"][:4]:
        v.set(True)
    character.attributes["Physical"]["Strength"]["spec"].set("Crushing")
    for v in character.abilities["Talents"]["Brawl"]["vars"][:2]:
        v.set(True)

    character.backgrounds[0]["name"].set("Resources")
    for v in character.backgrounds[0]["vars"][:3]:
        v.set(True)

    for v in character.virtues[0]["vars"][:4]:
        v.set(True)

    character.custom_abilities["Talents"][0]["name"].set("Carousing")
    for v in character.custom_abilities["Talents"][0]["vars"][:2]:
        v.set(True)


# ── Round trip ───────────────────────────────────────────────────────────────

def test_to_dict_load_roundtrip(character, tk_root):
    from game.character import Character

    _populate(character)
    # Capture a snapshot so the dict carries one; otherwise load() would
    # synthesise a legacy baseline and the second dump would differ.
    character.capture_chargen_snapshot()
    first = character.to_dict()

    restored = Character()
    restored.load(first)
    second = restored.to_dict()

    assert first == second


def test_roundtrip_preserves_specific_fields(character, tk_root):
    from game.character import Character

    _populate(character)
    character.capture_chargen_snapshot()
    data = character.to_dict()

    restored = Character()
    restored.load(data)

    assert restored.character_name.get() == "Test Subject"
    assert restored.player.get() == "Alice"
    assert restored.generation.get() == "7th"
    assert restored.xp_total.get() == 30
    assert sum(v.get() for v in restored.attributes["Physical"]["Strength"]["vars"]) == 4
    assert restored.attributes["Physical"]["Strength"]["spec"].get() == "Crushing"
    assert restored.backgrounds[0]["name"].get() == "Resources"


# ── Defaults & robustness ────────────────────────────────────────────────────

def test_load_empty_dict_applies_defaults(character):
    character.load({})
    assert character.generation.get() == "13th"
    assert character.blood_value.get() == 10
    assert character.wounds_value.get() == -1
    assert character.character_name.get()  # random NPC name, but non-empty


def test_load_without_snapshot_synthesises_legacy_baseline(character):
    # A legacy save with no chargen_snapshot should produce a baseline rather
    # than leaving it None (0 XP spent against current state).
    character.load({})
    assert character.chargen_snapshot is not None


def test_load_restores_explicit_snapshot(character):
    sentinel = {"attributes": {}, "marker": "explicit"}
    character.load({"chargen_snapshot": sentinel})
    assert character.chargen_snapshot == sentinel


def test_load_ignores_unknown_attribute_entries(character):
    # Out-of-taxonomy keys must be skipped, not raise.
    character.load({"attributes": {"Bogus": {"Nope": {"spec": "x", "dots": [1]}}}})
    # A valid one alongside still applies.
    character.load(
        {"attributes": {"Physical": {"Strength": {"spec": "", "dots": [1, 1, 1]}}}}
    )
    assert sum(v.get() for v in character.attributes["Physical"]["Strength"]["vars"]) == 3


# ── Persistence to disk ──────────────────────────────────────────────────────

def test_save_writes_named_json(character, tmp_path):
    _populate(character)
    out = tmp_path / "subject.json"
    character.save(path=out)

    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["header"]["character_name"] == "Test Subject"
    assert data["trackers"]["xp_total"] == 30


# ── apply_trackers wiring ────────────────────────────────────────────────────

def test_apply_trackers_syncs_dot_arrays_and_values(character):
    character.blood_value.set(7)
    character.wounds_value.set(1)
    character.humanity_value.set(6)
    character.will_value.set(5)
    for v in character.attributes["Physical"]["Dexterity"]["vars"][:4]:
        v.set(True)
    for v in character.attributes["Mental"]["Wits"]["vars"][:3]:
        v.set(True)

    character.apply_trackers()

    assert sum(v.get() for r in character.blood for v in r) == 7
    assert sum(v.get() for v in character.wounds) == 2   # level 1 -> dots 0 and 1
    assert sum(v.get() for v in character.humanity) == 6
    assert sum(v.get() for v in character.will) == 5
    assert character.dex_value.get() == 4
    assert character.wits_value.get() == 3
