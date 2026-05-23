from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AffiliationRules:
    """Point allocation for a given sect/affiliation at character creation."""
    attr_pools: list[int]     # [primary, secondary, tertiary] extra dots beyond 1
    ability_pools: list[int]  # [primary, secondary, tertiary]
    backgrounds: int
    disciplines: int
    virtues: int
    freebies: int


AFFILIATIONS: dict[str, AffiliationRules] = {
    "Camarilla":   AffiliationRules([7, 5, 3], [13, 9, 5], 5, 3, 7, 15),
    "Anarch":      AffiliationRules([6, 5, 3], [13, 9, 5], 5, 3, 7, 15),
    "Sabbat":      AffiliationRules([7, 5, 3], [13, 9, 5], 3, 3, 7, 15),
    "Independent": AffiliationRules([7, 5, 3], [13, 9, 5], 5, 3, 7, 15),
}

CLANS: tuple[str, ...] = (
    "Brujah", "Gangrel", "Malkavian", "Nosferatu", "Toreador", "Tremere", "Ventrue",
    "Lasombra", "Tzimisce",
    "Assamite", "Followers of Set", "Giovanni", "Ravnos",
    "Salubri", "Baali", "Daughters of Cacophony", "Gargoyle", "Kiasyd",
    "Nagaraja", "Samedi", "True Brujah",
    "Caitiff",
)

CLAN_DISCIPLINES: dict[str, tuple[str, ...]] = {
    "Brujah":                  ("Celerity", "Potence", "Presence"),
    "Gangrel":                 ("Animalism", "Fortitude", "Protean"),
    "Malkavian":               ("Auspex", "Dementation", "Obfuscate"),
    "Nosferatu":               ("Animalism", "Obfuscate", "Potence"),
    "Toreador":                ("Auspex", "Celerity", "Presence"),
    "Tremere":                 ("Auspex", "Dominate", "Thaumaturgy"),
    "Ventrue":                 ("Dominate", "Fortitude", "Presence"),
    "Lasombra":                ("Dominate", "Obtenebration", "Potence"),
    "Tzimisce":                ("Animalism", "Auspex", "Vicissitude"),
    "Assamite":                ("Celerity", "Obfuscate", "Quietus"),
    "Followers of Set":        ("Obfuscate", "Presence", "Serpentis"),
    "Giovanni":                ("Dominate", "Necromancy", "Potence"),
    "Ravnos":                  ("Animalism", "Chimerstry", "Fortitude"),
    "Salubri":                 ("Auspex", "Fortitude", "Obeah"),
    "Baali":                   ("Daimonion", "Obfuscate", "Presence"),
    "Daughters of Cacophony":  ("Fortitude", "Melpominee", "Presence"),
    "Gargoyle":                ("Fortitude", "Potence", "Visceratika"),
    "Kiasyd":                  ("Dominate", "Mytherceria", "Obtenebration"),
    "Nagaraja":                ("Dominate", "Necromancy", "Thaumaturgy"),
    "Samedi":                  ("Fortitude", "Obfuscate", "Thanatosis"),
    "True Brujah":             ("Potence", "Presence", "Temporis"),
    "Caitiff":                 (),
}

ARCHETYPES: tuple[str, ...] = (
    "Architect", "Autocrat", "Bon Vivant", "Bravo", "Caregiver",
    "Celebrant", "Child", "Competitor", "Conformist", "Conniver",
    "Curmudgeon", "Deviant", "Director", "Enigma", "Eye of the Storm",
    "Fanatic", "Gallant", "Judge", "Loner", "Martyr",
    "Masochist", "Monster", "Penitent", "Perfectionist", "Rebel",
    "Rogue", "Survivor", "Thrill-Seeker", "Traditionalist", "Trickster",
    "Visionary",
)

GENERATION_CHOICES: tuple[str, ...] = tuple(f"{g}th" for g in range(4, 16))


class CharGen:
    """Stateless helpers for character generation.

    All methods are static so they can be reused by a future random-generator
    without instantiating a Wizard or any tkinter widget.
    """

    @staticmethod
    def rules_for(affiliation: str) -> AffiliationRules:
        return AFFILIATIONS.get(affiliation, AFFILIATIONS["Camarilla"])

    @staticmethod
    def clan_disciplines(clan: str) -> tuple[str, ...]:
        return CLAN_DISCIPLINES.get(clan, ())

    @staticmethod
    def dots_in_category(character, category: str, source: str) -> int:
        """Sum of dots currently set across all stats in a category."""
        if source == "attributes":
            return sum(
                sum(v.get() for v in stat["vars"])
                for stat in character.attributes[category].values()
            )
        if source == "abilities":
            return sum(
                sum(v.get() for v in stat["vars"])
                for stat in character.abilities[category].values()
            )
        return 0

    # ── Future random-generator stubs ─────────────────────────────────────────

    @staticmethod
    def random_concept() -> dict:
        return {}

    @staticmethod
    def random_attributes(rules: AffiliationRules) -> dict:
        return {}
