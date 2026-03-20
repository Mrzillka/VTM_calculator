from __future__ import annotations

import json
from pathlib import Path
from random import choice
from tkinter import BooleanVar, IntVar, StringVar

from config import CHARACTER_FILE_PATH, NAMES, WOUND_LEVELS

_ATTRIBUTES = {
    "Physical": ("Strength", "Dexterity", "Stamina"),
    "Social": ("Charisma", "Manipulation", "Appearance"),
    "Mental": ("Perception", "Intelligence", "Wits"),
}

_ABILITIES = {
    "Talents": ("Alertness", "Athletics", "Brawl", "Dodge", "Empathy",
                "Expression", "Intimidation", "Leadership", "Streetwise", "Subterfuge"),
    "Skills": ("Animal Ken", "Crafts", "Drive", "Etiquette", "Firearms",
               "Melee", "Performance", "Security", "Stealth", "Survival"),
    "Knowledges": ("Academics", "Computer", "Finance", "Investigation", "Law",
                   "Linguistics", "Medicine", "Occult", "Politics", "Science"),
}

_VIRTUE_NAMES: tuple[str, ...] = (
    "Conscience / Conviction",
    "Self-Control / Instinct",
    "Courage",
)

_ADVANTAGE_ROWS: int = 7
_MERIT_FLAW_ROWS: int = 7


class Character:
    """
    Holds all character-specific state variables and mutation logic.

    Intended to be owned by the application root and passed to the UI layer.
    All tkinter variables are instantiated here so they can be bound directly
    to widgets without going through the root window.
    """

    _DOTS = 8

    def __init__(self) -> None:
        # Header
        self.character_name = StringVar(value=choice(NAMES))
        self.player = StringVar()
        self.chronicle = StringVar()

        self.nature = StringVar()
        self.demeanor = StringVar()
        self.clan = StringVar()

        self.generation = StringVar(value="13th")
        self.heaven = StringVar()
        self.concept = StringVar()

        self._init_vars()

        self.initiative_bonus_dex = IntVar(value=0)
        self.initiative_bonus_wits = IntVar(value=0)

        self.blood_max_value = IntVar(value=10)
        self.blood = [[BooleanVar(value=False) for _ in range(10)] for _ in range(4)]
        self.blood_value = IntVar(value=10)

        # -1 = unharmed; 0..len(WOUND_LEVELS)-1 = index into WOUND_LEVELS
        self.wounds = [BooleanVar(value=False) for _ in range(len(WOUND_LEVELS))]
        self.wounds_value = IntVar(value=-1)
        self.wounds_display = StringVar(value="Unharmed")
        self.roll_penalty = IntVar(value=0)

        self.humanity = [BooleanVar(value=False) for _ in range(10)]
        self.humanity_value = IntVar(value=0)

        self.will = [BooleanVar(value=False) for _ in range(10)]
        self.will_value = IntVar(value=0)
        self.willpower_max = IntVar(value=10)

    def _init_vars(self) -> None:
        def _dot_row(n: int = self._DOTS) -> list[BooleanVar]:
            return [BooleanVar(value=False) for _ in range(n)]

        self.attributes: dict[str, dict[str, dict[str, StringVar | list[BooleanVar]]]] = {
            category: {
                attribute: {'spec': StringVar(), 'vars': _dot_row()}
                for attribute in attributes
            }
            for category, attributes in _ATTRIBUTES.items()
        }

        self.abilities: dict[str, dict[str, dict[str, StringVar | list[BooleanVar]]]] = {
            category: {
                ability: {'spec': StringVar(), 'vars': _dot_row()}
                for ability in abilities
            }
            for category, abilities in _ABILITIES.items()
        }

        self.backgrounds: list[dict[str, StringVar | list[BooleanVar]]] = [
            {'name': StringVar(), 'vars': _dot_row()}
            for _ in range(_ADVANTAGE_ROWS)
        ]

        self.disciplines: list[dict[str, StringVar | list[BooleanVar]]] = [
            {'name': StringVar(), 'path': StringVar(), 'vars': _dot_row()}
            for _ in range(_ADVANTAGE_ROWS)
        ]

        self.virtues: list[dict[str, StringVar | list[BooleanVar]]] = [
            {'name': StringVar(value=vname), 'vars': _dot_row(5)}
            for vname in _VIRTUE_NAMES
        ]

        self.merits: list[dict[str, StringVar | IntVar]] = [
            {'name': StringVar(), 'cost': IntVar(value=0)}
            for _ in range(_MERIT_FLAW_ROWS)
        ]
        self.flaws: list[dict[str, StringVar | IntVar]] = [
            {'name': StringVar(), 'cost': IntVar(value=0)}
            for _ in range(_MERIT_FLAW_ROWS)
        ]

    # ── Trackers ───────────────────────────────────────────────────────────────

    def set_blood(self, row: int = 0, col: int = 0, *, load: bool = False) -> None:
        """
        Fill blood cells up to the given position, or reload from blood_value.

        Clicking the currently last filled cell toggles it off.
        """
        if load:
            val = self.blood_value.get()
            row, col = divmod(val, 10)
        else:
            if self.blood_value.get() != row * 10 + col + 1:
                col += 1

        for i in range(4):
            for j in range(10):
                self.blood[i][j].set(i < row or (i == row and j < col))

        self.blood_value.set(row * 10 + col)

    def set_wounds(self, clicked: int = 0, *, load: bool = False) -> None:
        """
        Set wound level with toggle-off support.

        When load=True, restores state from wounds_value.
        Otherwise, clicking the last filled dot clears it;
        clicking any other dot fills up to that level.
        wounds_value of -1 means unharmed (no dots filled).
        """
        if load:
            level = self.wounds_value.get()
            for i, var in enumerate(self.wounds):
                var.set(i <= level)
        else:
            filled = sum(v.get() for v in self.wounds)
            threshold = clicked if filled == clicked + 1 else clicked + 1
            for i, var in enumerate(self.wounds):
                var.set(i < threshold)
            level = threshold - 1

        self.wounds_value.set(level)
        if level < 0:
            self.wounds_display.set("Unharmed")
            self.roll_penalty.set(0)
        else:
            wl = WOUND_LEVELS[level]
            self.wounds_display.set(f"{wl.name} {wl.penalty}")
            self.roll_penalty.set(wl.penalty)

    def heal(self) -> None:
        """Spend one blood point to heal one wound level."""
        if self.wounds_value.get() >= 0 and self.blood_value.get() > 0:
            self.blood_value.set(self.blood_value.get() - 1)
            self.wounds_value.set(self.wounds_value.get() - 1)
            self.set_blood(load=True)
            self.set_wounds(load=True)

    def set_humanity(self, clicked: int = 0, *, load: bool = False) -> None:
        """Fill humanity dots up to the given level, with toggle-off support."""
        if load:
            level = self.humanity_value.get()
        else:
            filled = self.humanity_value.get()
            level = clicked if filled == clicked + 1 else clicked + 1
        for i in range(10):
            self.humanity[i].set(i < level)
        self.humanity_value.set(level)

    def set_will(self, clicked: int = 0, *, load: bool = False) -> None:
        """Fill willpower dots up to the given level, with toggle-off support."""
        if load:
            level = self.will_value.get()
        else:
            filled = self.will_value.get()
            level = clicked if filled == clicked + 1 else clicked + 1
        for i in range(10):
            self.will[i].set(i < level)
        self.will_value.set(level)

    # ── Persistence ────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize the full character state to a plain dictionary."""
        return {
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
            "initiative": {
                "dex":  self.initiative_bonus_dex.get(),
                "wits": self.initiative_bonus_wits.get(),
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
            },
        }

    def save(self, path: Path | None = None) -> None:
        """Write all character data to *path*, defaulting to CHARACTER_FILE_PATH."""
        save_path = path if path is not None else CHARACTER_FILE_PATH
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, data: dict) -> None:
        """
        Restore character state from a dictionary.

        Does not call apply_trackers(); the caller must invoke it
        after any required UI refresh (e.g. refresh_blood_cells).
        """
        header = data.get("header", {})
        self.character_name.set(header.get("character_name", choice(NAMES)))
        self.player.set(header.get("player", ""))
        self.chronicle.set(header.get("chronicle", ""))
        self.nature.set(header.get("nature", ""))
        self.demeanor.set(header.get("demeanor", ""))
        self.clan.set(header.get("clan", ""))
        self.generation.set(header.get("generation", "13th"))
        self.heaven.set(header.get("heaven", ""))
        self.concept.set(header.get("concept", ""))

        initiative = data.get("initiative", {})
        self.initiative_bonus_dex.set(initiative.get("dex", 0))
        self.initiative_bonus_wits.set(initiative.get("wits", 0))

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

    def load_from_file(self) -> bool:
        """
        Load character data from the JSON file.

        Returns True if the file was found and loaded, False otherwise.
        Does not call apply_trackers(); the caller is responsible for sequencing.
        """
        if not CHARACTER_FILE_PATH.exists():
            return False

        with open(CHARACTER_FILE_PATH, encoding="utf-8") as f:
            self.load(json.load(f))

        return True

    def apply_trackers(self) -> None:
        """Apply tracker values to their BooleanVar dot arrays.

        Must be called after load() and after any UI cell refresh.
        """
        self.set_blood(load=True)
        self.set_wounds(load=True)
        self.set_humanity(load=True)
        self.set_will(load=True)