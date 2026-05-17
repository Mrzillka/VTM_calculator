from __future__ import annotations

from random import choice
from tkinter import BooleanVar, IntVar, StringVar

from config import (
    BLOOD_COLS, BLOOD_ROWS, DEFAULT_GENERATION, GENERATION_RULES,
    MAX_GENERATION, MAX_DOT_TRACKER, MIN_GENERATION, NPC_NAMES, WOUND_LEVELS,
)
from game.character_io import CharacterIO

ATTRIBUTES = {
    "Physical": ("Strength", "Dexterity", "Stamina"),
    "Social": ("Charisma", "Manipulation", "Appearance"),
    "Mental": ("Perception", "Intelligence", "Wits"),
}

ABILITIES = {
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
_CUSTOM_ABILITY_ROWS: int = 3


class Character(CharacterIO):
    """
    Holds all character-specific state variables and mutation logic.

    Intended to be owned by the application root and passed to the UI layer.
    All tkinter variables are instantiated here so they can be bound directly
    to widgets without going through the root window.
    """

    _DOTS = 8

    def __init__(self) -> None:
        # Header
        self.character_name = StringVar(value=choice(NPC_NAMES))
        self.player = StringVar()
        self.chronicle = StringVar()

        self.nature = StringVar()
        self.demeanor = StringVar()
        self.clan = StringVar()

        self.generation = StringVar(value="13th")
        self.heaven = StringVar()
        self.concept = StringVar()

        self._init_vars()

        # Computed attribute scores (updated via traces on dot BooleanVars).
        self.dex_value  = IntVar(value=0)
        self.wits_value = IntVar(value=0)
        self._wire_attribute_value("Physical", "Dexterity", self.dex_value)
        self._wire_attribute_value("Mental",   "Wits",      self.wits_value)

        # Physical attribute blood boosts (scene-level, not persisted).
        self.str_boost = IntVar(value=0)
        self.dex_boost = IntVar(value=0)
        self.sta_boost = IntVar(value=0)

        default_blood = GENERATION_RULES[DEFAULT_GENERATION]["blood_max"]
        self.blood_max_value = IntVar(value=default_blood)
        self.blood = [[BooleanVar(value=False) for _ in range(BLOOD_COLS)] for _ in range(BLOOD_ROWS)]
        self.blood_value = IntVar(value=default_blood)

        # -1 = unharmed; 0..len(WOUND_LEVELS)-1 = index into WOUND_LEVELS
        self.wounds = [BooleanVar(value=False) for _ in range(len(WOUND_LEVELS))]
        self.wounds_value = IntVar(value=-1)
        self.wounds_display = StringVar(value="Unharmed")
        self.roll_penalty = IntVar(value=0)

        self.humanity = [BooleanVar(value=False) for _ in range(MAX_DOT_TRACKER)]
        self.humanity_value = IntVar(value=0)

        self.will = [BooleanVar(value=False) for _ in range(MAX_DOT_TRACKER)]
        self.will_value = IntVar(value=0)
        self.willpower_max = IntVar(value=MAX_DOT_TRACKER)

        self.blood_per_turn = StringVar(value="1")
        self.generation.trace_add("write", lambda *_: self._on_generation_change())

    def _init_vars(self) -> None:
        def _dot_row(n: int = self._DOTS) -> list[BooleanVar]:
            return [BooleanVar(value=False) for _ in range(n)]

        self.attributes: dict[str, dict[str, dict[str, StringVar | list[BooleanVar]]]] = {
            category: {
                attribute: {'spec': StringVar(), 'vars': _dot_row()}
                for attribute in attributes
            }
            for category, attributes in ATTRIBUTES.items()
        }

        self.abilities: dict[str, dict[str, dict[str, StringVar | list[BooleanVar]]]] = {
            category: {
                ability: {'spec': StringVar(), 'vars': _dot_row()}
                for ability in abilities
            }
            for category, abilities in ABILITIES.items()
        }

        # Extra user-defined ability rows, 3 per category.
        self.custom_abilities: dict[str, list[dict]] = {
            category: [
                {'name': StringVar(), 'spec': StringVar(), 'vars': _dot_row()}
                for _ in range(_CUSTOM_ABILITY_ROWS)
            ]
            for category in ABILITIES
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

    # ── Attribute wiring ───────────────────────────────────────────────────────

    def _wire_attribute_value(
        self, category: str, name: str, out_var: IntVar
    ) -> None:
        """Keep *out_var* equal to the filled-dot count for an attribute."""
        def _update(*_) -> None:
            out_var.set(sum(v.get() for v in self.attributes[category][name]["vars"]))
        for var in self.attributes[category][name]["vars"]:
            var.trace_add("write", _update)
        _update()

    # ── Generation rules ───────────────────────────────────────────────────────

    def _parse_generation(self) -> int:
        digits = "".join(c for c in self.generation.get() if c.isdigit())
        try:
            return max(MIN_GENERATION, min(MAX_GENERATION, int(digits)))
        except ValueError:
            return DEFAULT_GENERATION

    def _on_generation_change(self) -> None:
        rules = GENERATION_RULES.get(self._parse_generation(), GENERATION_RULES[DEFAULT_GENERATION])
        self.blood_max_value.set(rules["blood_max"])
        self.blood_per_turn.set(str(rules["blood_per_turn"]))

    # ── Physical attribute boosts ──────────────────────────────────────────────

    def boost_attribute(
        self, boost_var: IntVar, base_vars: list[BooleanVar]
    ) -> None:
        """Spend 1 blood to raise a physical attribute by 1 for the scene."""
        if self.blood_value.get() <= 0:
            return
        max_trait = GENERATION_RULES.get(
            self._parse_generation(), GENERATION_RULES[13]
        )["max_trait"]
        base = sum(v.get() for v in base_vars)
        if base + boost_var.get() >= max_trait:
            return
        self.blood_value.set(self.blood_value.get() - 1)
        self.set_blood(load=True)
        boost_var.set(boost_var.get() + 1)

    def end_scene(self) -> None:
        """Revert all physical attribute boosts to zero (blood already spent)."""
        self.str_boost.set(0)
        self.dex_boost.set(0)
        self.sta_boost.set(0)

    # ── Trackers ───────────────────────────────────────────────────────────────

    def set_blood(self, row: int = 0, col: int = 0, *, load: bool = False) -> None:
        """
        Fill blood cells up to the given position, or reload from blood_value.

        Clicking the currently last filled cell toggles it off.
        """
        if load:
            val = self.blood_value.get()
            row, col = divmod(val, BLOOD_COLS)
        else:
            if self.blood_value.get() != row * BLOOD_COLS + col + 1:
                col += 1

        for i in range(BLOOD_ROWS):
            for j in range(BLOOD_COLS):
                self.blood[i][j].set(i < row or (i == row and j < col))

        self.blood_value.set(row * BLOOD_COLS + col)

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
            self.wounds_display.set(f"{wl.name} {wl.penalty}" if wl.penalty else wl.name)
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
        for i in range(MAX_DOT_TRACKER):
            self.humanity[i].set(i < level)
        self.humanity_value.set(level)

    def set_will(self, clicked: int = 0, *, load: bool = False) -> None:
        """Fill willpower dots up to the given level, with toggle-off support."""
        if load:
            level = self.will_value.get()
        else:
            filled = self.will_value.get()
            level = clicked if filled == clicked + 1 else clicked + 1
        for i in range(MAX_DOT_TRACKER):
            self.will[i].set(i < level)
        self.will_value.set(level)

    # ── Quick roll helpers ─────────────────────────────────────────────────────

    def get_stat_value(self, name: str) -> int:
        """Dot count for any attribute, ability, custom ability, discipline, or background by name."""
        if not name:
            return 0
        _boosts = {"Strength": self.str_boost, "Dexterity": self.dex_boost, "Stamina": self.sta_boost}
        for cat in self.attributes.values():
            if name in cat:
                base = sum(v.get() for v in cat[name]["vars"])
                return base + _boosts[name].get() if name in _boosts else base
        for cat in self.abilities.values():
            if name in cat:
                return sum(v.get() for v in cat[name]["vars"])
        for cat_rows in self.custom_abilities.values():
            for row in cat_rows:
                if row["name"].get() == name:
                    return sum(v.get() for v in row["vars"])
        for row in self.disciplines:
            if row["name"].get() == name:
                return sum(v.get() for v in row["vars"])
        for row in self.backgrounds:
            if row["name"].get() == name:
                return sum(v.get() for v in row["vars"])
        return 0

    def all_pool_names(self) -> list[str]:
        """All names usable in the second slot of a quick roll (ability, custom, discipline, background)."""
        names: list[str] = [n for cat in self.abilities.values() for n in cat]
        seen = set(names)
        for cat_rows in self.custom_abilities.values():
            for row in cat_rows:
                n = row["name"].get().strip()
                if n and n not in seen:
                    names.append(n)
                    seen.add(n)
        for row in self.disciplines:
            n = row["name"].get().strip()
            if n and n not in seen:
                names.append(n)
                seen.add(n)
        for row in self.backgrounds:
            n = row["name"].get().strip()
            if n and n not in seen:
                names.append(n)
                seen.add(n)
        return names

