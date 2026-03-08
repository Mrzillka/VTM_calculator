from __future__ import annotations

from random import choice
from tkinter import BooleanVar, IntVar, StringVar

import dotenv

from config import ENV_FILE_PATH, NAMES, WOUND_LEVELS

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

        #
        self.initiative_bonus_dex = IntVar(value=0)
        self.initiative_bonus_wits = IntVar(value=0)

        self.blood_max_value = IntVar(value=10)
        self.blood = [[BooleanVar(value=False) for _ in range(10)] for _ in range(4)]
        self.blood_value = IntVar(value=10)

        self.wounds = [BooleanVar(value=False) for _ in range(9)]
        self.wounds_value = IntVar(value=0)
        self.roll_penalty = IntVar(value=0)

        self.humanity = [BooleanVar(value=False) for _ in range(10)]
        self.humanity_value = IntVar(value=0)

        self.will = [BooleanVar(value=False) for _ in range(10)]
        self.will_value = IntVar(value=0)

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

        # self.attributes["Physical"]["Strength"]['spec'] = StringVar()
        # self.attributes["Physical"]["Strength"]['vars'] = [IntVar(value=1) for _ in range(n)]

    # ── Trackers ───────────────────────────────────────────────────────────────

    def set_blood(self, row: int = 0, col: int = 0, *, load: bool = False) -> None:
        """Fill blood cells up to the given position, or reload from blood_value."""
        if load:
            val = self.blood_value.get()
            row, col = divmod(val, 10)
        else:
            col += 1

        for i in range(4):
            for j in range(10):
                self.blood[i][j].set(i < row or (i == row and j < col))

        self.blood_value.set(row * 10 + col)

    def set_wounds(self, level: int = 0, *, load: bool = False) -> None:
        """Set wound level and update the roll penalty accordingly."""
        if load:
            level = self.wounds_value.get()
        for i in range(9):
            self.wounds[i].set(i <= level)
        self.wounds_value.set(level)
        self.roll_penalty.set(WOUND_LEVELS[level].penalty)

    def heal(self) -> None:
        """Spend one blood point to heal one wound level."""
        if self.wounds_value.get() > 0 and self.blood_value.get() > 0:
            self.blood_value.set(self.blood_value.get() - 1)
            self.wounds_value.set(self.wounds_value.get() - 1)
            self.set_blood(load=True)
            self.set_wounds(load=True)

    def set_humanity(self, level: int = 0, *, load: bool = False) -> None:
        """Fill humanity dots up to the given level."""
        if load:
            level = self.humanity_value.get()
        else:
            level += 1
        for i in range(10):
            self.humanity[i].set(i < level)
        self.humanity_value.set(level)

    def set_will(self, level: int = 0, *, load: bool = False) -> None:
        """Fill willpower dots up to the given level."""
        if load:
            level = self.will_value.get()
        else:
            level += 1
        for i in range(10):
            self.will[i].set(i < level)
        self.will_value.set(level)

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self) -> None:
        """Write character fields to the .env file."""
        kv = {
            "NAME": self.character_name.get(),
            "DEX": str(self.initiative_bonus_dex.get()),
            "WITS": str(self.initiative_bonus_wits.get()),
            "BLOOD": str(self.blood_value.get()),
            "MAX_BLOOD": str(self.blood_max_value.get()),
            "WOUNDS": str(self.wounds_value.get()),
            "HUMANITY": str(self.humanity_value.get()),
            "WILL": str(self.will_value.get()),
        }
        for key, value in kv.items():
            dotenv.set_key(str(ENV_FILE_PATH), key, value)

    def load(self, env: dict[str, str | None]) -> None:
        """
        Restore character state from a dotenv mapping.

        Note: callers must invoke the interface's refresh_blood_cells() between
        blood_max_value being set and blood_value being applied.
        """
        self.character_name.set(env["NAME"])
        self.initiative_bonus_dex.set(int(env["DEX"]))
        self.initiative_bonus_wits.set(int(env["WITS"]))
        self.blood_max_value.set(int(env["MAX_BLOOD"]))
