from __future__ import annotations

import json
from pathlib import Path
from random import choice
from typing import TYPE_CHECKING

from config import CHARACTER_FILE_PATH, CHARACTERS_DIR, NPC_NAMES

if TYPE_CHECKING:
    pass


class CharacterIO:
    """Mixin providing persistence for Character: serialization, save, load."""

    # ── Serialization ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize the full character state to a plain dictionary."""
        d = {
            "header": {
                "character_name": self.character_name.get(),
                "player":         self.player.get(),
                "chronicle":      self.chronicle.get(),
                "nature":         self.nature.get(),
                "demeanor":       self.demeanor.get(),
                "clan":           self.clan.get(),
                "generation":     self.generation.get(),
                "heaven":         self.heaven.get(),
                "concept":        self.concept.get(),
            },
            "trackers": {
                "blood_value":     self.blood_value.get(),
                "blood_max_value": self.blood_max_value.get(),
                "wounds_value":    self.wounds_value.get(),
                "humanity_value":  self.humanity_value.get(),
                "will_value":      self.will_value.get(),
                "willpower_max":   self.willpower_max.get(),
            },
            "attributes": {
                category: {
                    attr: {
                        "spec": values["spec"].get(),
                        "dots": [v.get() for v in values["vars"]],
                    }
                    for attr, values in attrs.items()
                }
                for category, attrs in self.attributes.items()
            },
            "abilities": {
                category: {
                    ability: {
                        "spec": values["spec"].get(),
                        "dots": [v.get() for v in values["vars"]],
                    }
                    for ability, values in abilities.items()
                }
                for category, abilities in self.abilities.items()
            },
            "custom_abilities": {
                category: [
                    {
                        "name": entry["name"].get(),
                        "spec": entry["spec"].get(),
                        "dots": [v.get() for v in entry["vars"]],
                    }
                    for entry in entries
                ]
                for category, entries in self.custom_abilities.items()
            },
            "advantages": {
                "backgrounds": [
                    {"name": e["name"].get(), "dots": [v.get() for v in e["vars"]]}
                    for e in self.backgrounds
                ],
                "disciplines": [
                    {
                        "name": e["name"].get(),
                        "path": e["path"].get(),
                        "dots": [v.get() for v in e["vars"]],
                    }
                    for e in self.disciplines
                ],
                "virtues": [
                    {"dots": [v.get() for v in e["vars"]]}
                    for e in self.virtues
                ],
                "merits": [
                    {"name": e["name"].get(), "cost": e["cost"].get()}
                    for e in self.merits
                ],
                "flaws": [
                    {"name": e["name"].get(), "cost": e["cost"].get()}
                    for e in self.flaws
                ],
                "combo_disciplines": [sv.get() for sv in self.combo_disciplines],
            },
        }
        if self.chargen_snapshot is not None:
            d["chargen_snapshot"] = self.chargen_snapshot
        return d

    # ── Save ───────────────────────────────────────────────────────────────────

    def save(self, path: Path | None = None) -> None:
        """Write character data to *path*.

        When *path* is None the file is saved to CHARACTERS_DIR under the
        current character name, so different characters never overwrite each
        other.
        """
        save_path = path if path is not None else (
            CHARACTERS_DIR / f"{self.character_name.get()}.json"
        )
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    # ── Load ───────────────────────────────────────────────────────────────────

    def load(self, data: dict) -> None:
        """
        Restore character state from a dictionary.

        Does not call apply_trackers(); the caller must invoke it
        after any required UI refresh (e.g. refresh_blood_cells).
        """
        header = data.get("header", {})
        self.character_name.set(header.get("character_name", choice(NPC_NAMES)))
        self.player.set(header.get("player", ""))
        self.chronicle.set(header.get("chronicle", ""))
        self.nature.set(header.get("nature", ""))
        self.demeanor.set(header.get("demeanor", ""))
        self.clan.set(header.get("clan", ""))
        self.generation.set(header.get("generation", "13th"))
        self.heaven.set(header.get("heaven", ""))
        self.concept.set(header.get("concept", ""))

        trackers = data.get("trackers", {})
        self.blood_max_value.set(trackers.get("blood_max_value", 10))
        self.blood_value.set(trackers.get("blood_value", 10))
        self.wounds_value.set(trackers.get("wounds_value", -1))
        self.humanity_value.set(trackers.get("humanity_value", 0))
        self.will_value.set(trackers.get("will_value", 0))
        self.willpower_max.set(trackers.get("willpower_max", 10))

        for category, attrs in data.get("attributes", {}).items():
            for attr, values in attrs.items():
                if category in self.attributes and attr in self.attributes[category]:
                    self.attributes[category][attr]["spec"].set(values.get("spec", ""))
                    for i, dot in enumerate(values.get("dots", [])):
                        if i < len(self.attributes[category][attr]["vars"]):
                            self.attributes[category][attr]["vars"][i].set(dot)

        for category, abilities in data.get("abilities", {}).items():
            for ability, values in abilities.items():
                if category in self.abilities and ability in self.abilities[category]:
                    self.abilities[category][ability]["spec"].set(values.get("spec", ""))
                    for i, dot in enumerate(values.get("dots", [])):
                        if i < len(self.abilities[category][ability]["vars"]):
                            self.abilities[category][ability]["vars"][i].set(dot)

        for category, entries in data.get("custom_abilities", {}).items():
            if category in self.custom_abilities:
                for i, entry_data in enumerate(entries):
                    if i < len(self.custom_abilities[category]):
                        self.custom_abilities[category][i]["name"].set(
                            entry_data.get("name", ""))
                        self.custom_abilities[category][i]["spec"].set(
                            entry_data.get("spec", ""))
                        for j, dot in enumerate(entry_data.get("dots", [])):
                            if j < len(self.custom_abilities[category][i]["vars"]):
                                self.custom_abilities[category][i]["vars"][j].set(dot)

        advantages = data.get("advantages", {})

        for i, entry in enumerate(advantages.get("backgrounds", [])):
            if i < len(self.backgrounds):
                self.backgrounds[i]["name"].set(entry.get("name", ""))
                for j, dot in enumerate(entry.get("dots", [])):
                    if j < len(self.backgrounds[i]["vars"]):
                        self.backgrounds[i]["vars"][j].set(dot)

        for i, entry in enumerate(advantages.get("disciplines", [])):
            if i < len(self.disciplines):
                self.disciplines[i]["name"].set(entry.get("name", ""))
                self.disciplines[i]["path"].set(entry.get("path", ""))
                for j, dot in enumerate(entry.get("dots", [])):
                    if j < len(self.disciplines[i]["vars"]):
                        self.disciplines[i]["vars"][j].set(dot)

        for i, entry in enumerate(advantages.get("virtues", [])):
            if i < len(self.virtues):
                for j, dot in enumerate(entry.get("dots", [])):
                    if j < len(self.virtues[i]["vars"]):
                        self.virtues[i]["vars"][j].set(dot)

        for i, entry in enumerate(advantages.get("merits", [])):
            if i < len(self.merits):
                self.merits[i]["name"].set(entry.get("name", ""))
                self.merits[i]["cost"].set(entry.get("cost", 0))

        for i, entry in enumerate(advantages.get("flaws", [])):
            if i < len(self.flaws):
                self.flaws[i]["name"].set(entry.get("name", ""))
                self.flaws[i]["cost"].set(entry.get("cost", 0))

        for i, name in enumerate(advantages.get("combo_disciplines", [])):
            if i < len(self.combo_disciplines):
                self.combo_disciplines[i].set(name)

        raw_snap = data.get("chargen_snapshot")
        if raw_snap is not None:
            self.chargen_snapshot = raw_snap
        else:
            # Legacy save: treat current values as the chargen baseline (0 XP spent).
            self.capture_chargen_snapshot()

    def load_from_file(self) -> bool:
        """Load character data from the legacy single-file path.

        Returns True if the file was found and loaded, False otherwise.
        Kept for migration use only; prefer loading via CHARACTERS_DIR.
        Does not call apply_trackers(); the caller is responsible for sequencing.
        """
        if not CHARACTER_FILE_PATH.exists():
            return False

        with open(CHARACTER_FILE_PATH, encoding="utf-8") as f:
            self.load(json.load(f))

        return True

    # ── Apply ──────────────────────────────────────────────────────────────────

    def apply_trackers(self) -> None:
        """Apply tracker values to their BooleanVar dot arrays.

        Must be called after load() and after any UI cell refresh.
        """
        self.set_blood(load=True)
        self.set_wounds(load=True)
        self.set_humanity(load=True)
        self.set_will(load=True)
        self.dex_value.set(
            sum(v.get() for v in self.attributes["Physical"]["Dexterity"]["vars"])
        )
        self.wits_value.set(
            sum(v.get() for v in self.attributes["Mental"]["Wits"]["vars"])
        )
