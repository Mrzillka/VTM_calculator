from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DisciplinePower:
    name: str
    level: int                      # minimum dot level required (1-5)
    attribute: str | None           # from character.py ATTRIBUTES; None if no roll
    ability: str | None             # from character.py ABILITIES, or a discipline name for
                                    # self-referential rolls (e.g. "Dominate"); None if no roll
    difficulty: int                 # static fallback difficulty when difficulty_context is None
    difficulty_context: str | None  # overrides difficulty at the table, e.g.
                                    # "target's current Willpower", "10 minus target's Humanity"
    opposition: str | None          # separate resisted roll the target makes, e.g. "Willpower"
    blood_cost: int                 # blood points to activate (0 = free)
    is_automatic: bool              # True = no activation roll (passive, reflexive, etc.)
    notes: str = field(default="")  # per-turn costs or special mechanics


# ---------------------------------------------------------------------------
# Roll rules for all 30 disciplines (V20 base; correct via corrections later)
# Keys match config.py::DISCIPLINES exactly.
# ---------------------------------------------------------------------------

DISCIPLINE_POWERS: dict[str, list[DisciplinePower]] = {

    "Animalism": [
        DisciplinePower("Feral Whispers",        1, "Manipulation", "Animal Ken", 6, None,                          "Wits",      0, False),
        DisciplinePower("Beckoning",             2, "Charisma",     "Survival",   6, None,                          None,        0, False),
        DisciplinePower("Quell the Beast",       3, "Manipulation", "Empathy",    6, "target's current Willpower",  None,        0, False),
        DisciplinePower("Subsume the Spirit",    4, "Manipulation", "Animal Ken", 8, "target's current Willpower",  "Willpower", 1, False),
        DisciplinePower("Drawing Out the Beast", 5, "Stamina",      "Animal Ken", 8, None,                          None,        0, False),
    ],

    "Auspex": [
        DisciplinePower("Heightened Senses",   1, "Perception",   "Alertness",   6, None,                         None,        0, False),
        DisciplinePower("Aura Perception",     2, "Perception",   "Empathy",     8, None,                         None,        0, False),
        DisciplinePower("The Spirit's Touch",  3, "Perception",   "Empathy",     6, None,                         None,        0, False),
        DisciplinePower("Telepathy",           4, "Intelligence", "Subterfuge",  6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Psychic Projection",  5, "Perception",   "Occult",      7, None,                         None,        0, False),
    ],

    # Passive: no named rollable powers; spending 1 blood per action grants extra actions
    "Celerity": [
        DisciplinePower(
            "Extra Action", 1, None, None, 6, None, None, 1, True,
            notes="1 blood per extra action taken, up to Celerity dots per turn",
        ),
    ],

    "Chimerstry": [
        DisciplinePower("Ignis Fatuus",  1, "Manipulation", "Performance", 6, None, None,        0, False),
        DisciplinePower("Fata Morgana",  2, "Manipulation", "Performance", 7, None, None,        1, False),
        DisciplinePower("Apparition",    3, None,           None,          6, None, None,        0, True,
                        notes="animates an existing Chimerstry illusion; no new roll"),
        DisciplinePower("Permanency",    4, "Manipulation", "Performance", 8, None, None,        1, False),
        DisciplinePower("Horrid Reality",5, "Manipulation", "Performance", 8, None, "Willpower", 1, False),
    ],

    "Dementation": [
        DisciplinePower("Passion",         1, "Manipulation", "Empathy",     6, None,                         None,        0, False),
        DisciplinePower("The Haunting",    2, "Manipulation", "Subterfuge",  6, None,                         None,        0, False),
        DisciplinePower("Eyes of Chaos",   3, "Perception",   "Empathy",     7, None,                         None,        0, False),
        DisciplinePower("Voice of Madness",4, "Manipulation", "Expression",  7, None,                         "Willpower", 0, False),
        DisciplinePower("Total Insanity",  5, "Manipulation", "Empathy",     6, "target's current Willpower", "Willpower", 0, False),
    ],

    "Dominate": [
        DisciplinePower("Command",           1, "Manipulation", "Intimidation", 6, "target's current Willpower", None,        0, False),
        DisciplinePower("Mesmerize",         2, "Manipulation", "Leadership",   6, "target's current Willpower", None,        0, False),
        DisciplinePower("The Forgetful Mind",3, "Wits",         "Subterfuge",   6, "target's current Willpower", None,        0, False),
        DisciplinePower("Conditioning",      4, "Manipulation", "Leadership",   6, "target's current Willpower", "Willpower", 0, False,
                        notes="extended action"),
        DisciplinePower("Possession",        5, "Manipulation", "Dominate",     6, "target's current Willpower", "Willpower", 1, False,
                        notes="second stat is own Dominate discipline rating"),
    ],

    # Passive: adds soak dice equal to dots; no activation roll or blood cost
    "Fortitude": [
        DisciplinePower(
            "Soak Bonus", 1, None, None, 6, None, None, 0, True,
            notes="each dot adds one automatic soak die",
        ),
    ],

    "Necromancy": [
        DisciplinePower("Insight",       1, "Perception",   "Occult", 6, None, None, 1, False,
                        notes="Sepulchre Path; other paths have different rolls"),
        DisciplinePower("Summon Soul",   2, "Manipulation", "Occult", 7, None, None, 1, False),
        DisciplinePower("Compel Soul",   3, "Wits",         "Occult", 8, None, None, 1, False),
        DisciplinePower("Haunting",      4, "Manipulation", "Occult", 8, None, None, 1, False),
        DisciplinePower("Torment",       5, "Stamina",      "Occult", 9, None, None, 2, False),
    ],

    "Obfuscate": [
        DisciplinePower("Cloak of Shadows",         1, None,           None,          6, None,                         None,        0, True,
                        notes="automatic while completely still"),
        DisciplinePower("Unseen Presence",          2, "Wits",         "Stealth",     6, None,                         None,        0, False),
        DisciplinePower("Mask of a Thousand Faces", 3, "Manipulation", "Performance", 7, None,                         None,        0, False),
        DisciplinePower("Vanish from the Mind's Eye",4,"Charisma",     "Stealth",     6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Cloak the Gathering",      5, "Wits",         "Stealth",     7, None,                         None,        0, False),
    ],

    "Obtenebration": [
        DisciplinePower("Shadow Play",         1, "Manipulation", "Occult", 6, None, None, 0, False),
        DisciplinePower("Shroud of Night",     2, "Manipulation", "Occult", 6, None, None, 1, False),
        DisciplinePower("Arms of the Abyss",   3, "Manipulation", "Occult", 7, None, None, 1, False),
        DisciplinePower("Black Metamorphosis", 4, "Manipulation", "Occult", 7, None, None, 1, False),
        DisciplinePower("Tenebrous Form",      5, None,           None,     6, None, None, 1, True),
    ],

    # Passive: adds to Strength for damage; no activation roll or blood cost
    "Potence": [
        DisciplinePower(
            "Strength Bonus", 1, None, None, 6, None, None, 0, True,
            notes="each dot adds one die to Strength-based damage rolls",
        ),
    ],

    "Presence": [
        DisciplinePower("Awe",          1, "Charisma", "Performance", 7, None,                         None,        0, False),
        DisciplinePower("Dread Gaze",   2, "Charisma", "Intimidation",6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Entrancement", 3, "Charisma", "Subterfuge",  6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Summon",       4, "Charisma", "Subterfuge",  6, None,                         None,        0, False),
        DisciplinePower("Majesty",      5, "Charisma", "Performance", 6, "target's current Willpower", "Willpower", 0, False),
    ],

    "Protean": [
        DisciplinePower("Eyes of the Beast", 1, None, None, 6, None, None, 0, True),
        DisciplinePower("Feral Claws",       2, None, None, 6, None, None, 1, True),
        DisciplinePower("Earth Meld",        3, None, None, 6, None, None, 1, True),
        DisciplinePower("Shape of the Beast",4, None, None, 6, None, None, 1, True),
        DisciplinePower("Mist Form",         5, None, None, 6, None, None, 1, True),
    ],

    "Quietus": [
        DisciplinePower("Silence of Death", 1, None,          None,      6, None, None, 0, True),
        DisciplinePower("Scorpion's Touch", 2, "Dexterity",   "Medicine",6, None, None, 1, False),
        DisciplinePower("Dagon's Call",     3, "Manipulation","Brawl",   7, None, None, 1, False,
                        notes="extended action over multiple rounds"),
        DisciplinePower("Baal's Caress",    4, "Dexterity",   "Melee",   6, None, None, 1, False,
                        notes="1 blood per round to coat weapon"),
        DisciplinePower("Taste of Death",   5, "Perception",  "Occult",  6, None, None, 2, False),
    ],

    "Serpentis": [
        DisciplinePower("Eyes of the Serpent",1, "Charisma",     "Occult",   6, "target's current Willpower", None, 0, False),
        DisciplinePower("Tongue of the Asp",  2, "Strength",     "Brawl",    6, None,                         None, 1, False),
        DisciplinePower("Skin of the Adder",  3, "Stamina",      "Survival", 6, None,                         None, 1, False),
        DisciplinePower("Form of the Cobra",  4, None,           None,       6, None,                         None, 1, True),
        DisciplinePower("Heart of Darkness",  5, None,           None,       6, None,                         None, 1, True),
    ],

    "Thaumaturgy": [
        DisciplinePower("A Taste for Blood",  1, "Perception",   "Occult",    6, None,                         None,        0, False,
                        notes="Path of Blood; other paths have different rolls"),
        DisciplinePower("Blood Rage",         2, "Manipulation", "Subterfuge",6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Blood of Potency",   3, "Intelligence", "Occult",    6, None,                         None,        1, False,
                        notes="extended action"),
        DisciplinePower("Theft of Vitae",     4, "Intelligence", "Occult",    6, None,                         None,        0, False),
        DisciplinePower("Cauldron of Blood",  5, "Manipulation", "Occult",    6, "target's current Willpower", "Willpower", 0, False),
    ],

    "Vicissitude": [
        DisciplinePower("Malleable Visage", 1, "Stamina",    "Crafts",   6, None, None, 1, False),
        DisciplinePower("Fleshcraft",       2, "Dexterity",  "Medicine", 6, None, None, 1, False),
        DisciplinePower("Bonecraft",        3, "Strength",   "Medicine", 6, None, None, 1, False),
        DisciplinePower("Horrid Form",      4, None,         None,       6, None, None, 1, True),
        DisciplinePower("Blood Form",       5, None,         None,       6, None, None, 1, True,
                        notes="1 blood per turn to maintain"),
    ],

    # --- Bloodline disciplines ---------------------------------------------------

    "Abombwe": [
        DisciplinePower("Harness the Shadows",1, "Manipulation", "Occult",   6, None, None, 0, False),
        DisciplinePower("Eyes of the Wild",   2, "Perception",   "Alertness",6, None, None, 0, False),
        DisciplinePower("The Living Shadow",  3, "Manipulation", "Occult",   7, None, None, 1, False),
        DisciplinePower("Shadow Form",        4, None,           None,       6, None, None, 1, True),
        DisciplinePower("Obeah of Darkness",  5, "Manipulation", "Occult",   8, None, None, 2, False),
    ],

    "Daimonion": [
        DisciplinePower("Sense the Sin",          1, "Perception",   "Empathy",   6, None,                         None,        0, False),
        DisciplinePower("Dement",                 2, "Manipulation", "Subterfuge",6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Possession of the Flesh",3, "Manipulation", "Occult",    6, "target's current Willpower", "Willpower", 1, False),
        DisciplinePower("Daimoinon Form",         4, None,           None,        6, None,                         None,        1, True),
        DisciplinePower("Utter Darkness",         5, "Manipulation", "Occult",    9, None,                         None,        2, False),
    ],

    "Melpominee": [
        DisciplinePower("The Phantom Speaker",  1, "Intelligence", "Performance", 6, None,                         None,        0, False),
        DisciplinePower("Tourette's Voice",     2, "Manipulation", "Performance", 6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("Siren's Beckoning",    3, "Charisma",     "Performance", 6, "target's current Willpower", "Willpower", 0, False),
        DisciplinePower("The Wail of Banshees", 4, "Stamina",      "Performance", 7, None,                         None,        0, False),
        DisciplinePower("The Voice of Pan",     5, "Charisma",     "Performance", 6, "target's current Willpower", "Willpower", 1, False),
    ],

    "Mortis": [
        DisciplinePower("Masque of Death",         1, "Stamina",      "Medicine", 6, None, None,     0, False),
        DisciplinePower("Sense Death",             2, "Perception",   "Occult",   6, None, None,     0, False),
        DisciplinePower("Wither",                  3, "Stamina",      "Medicine", 6, None, "Stamina",1, False),
        DisciplinePower("Black Death",             4, "Stamina",      "Medicine", 8, None, None,     2, False),
        DisciplinePower("Corrupt the Undead Flesh",5, "Manipulation", "Medicine", 9, None, None,     2, False),
    ],

    "Mytherceria": [
        DisciplinePower("Fey Sight",     1, "Perception",   "Occult",      6, None,                         None,        0, False),
        DisciplinePower("Aura of Power", 2, "Manipulation", "Intimidation",6, None,                         None,        0, False),
        DisciplinePower("Folly of Vision",3,"Manipulation", "Occult",      6, "target's current Willpower", "Willpower", 1, False),
        DisciplinePower("Voodoo",        4, "Manipulation", "Occult",      8, None,                         None,        1, False),
        DisciplinePower("Dream Mastery", 5, "Intelligence", "Occult",      8, None,                         None,        2, False),
    ],

    "Obeah": [
        DisciplinePower("Panacea",                      1, "Intelligence", "Medicine", 6, None,                         None,        1, False),
        DisciplinePower("Anesthetic Touch",             2, "Intelligence", "Medicine", 6, None,                         None,        1, False),
        DisciplinePower("Corpore Sano",                 3, "Intelligence", "Medicine", 6, None,                         None,        1, False,
                        notes="extended action"),
        DisciplinePower("Mens Sana",                    4, "Manipulation", "Empathy",  6, "target's current Willpower", "Willpower", 1, False),
        DisciplinePower("Unburdening the Bestial Soul", 5, "Charisma",     "Empathy",  8, "10 minus target's Humanity", None,        2, False),
    ],

    "Sanguinus": [
        DisciplinePower("Bind Fools",        1, "Manipulation", "Subterfuge", 6, None, None, 0, False),
        DisciplinePower("Shared Strength",   2, "Stamina",      "Occult",     6, None, None, 1, False),
        DisciplinePower("Coordinate Attacks",3, "Wits",         "Leadership", 7, None, None, 0, False),
        DisciplinePower("Walk Together",     4, "Intelligence", "Occult",     7, None, None, 1, False),
        DisciplinePower("Coagulate Entity",  5, "Intelligence", "Occult",     8, None, None, 2, False),
    ],

    "Temporis": [
        DisciplinePower("Freeze the Moment",1, "Intelligence", "Occult", 6, None, None, 1, False),
        DisciplinePower("Warp Time",        2, "Intelligence", "Occult", 7, None, None, 1, False),
        DisciplinePower("Rift",             3, "Intelligence", "Occult", 8, None, None, 2, False),
        DisciplinePower("Temporal Haste",   4, "Wits",         "Occult", 7, None, None, 1, False),
        DisciplinePower("Celerity of Ages", 5, None,           None,     6, None, None, 1, True),
    ],

    "Thanatosis": [
        DisciplinePower("Ooze",                 1, "Stamina",      "Medicine", 6, None, None, 0, False),
        DisciplinePower("Putrefaction",         2, "Manipulation", "Medicine", 6, None, None, 1, False),
        DisciplinePower("Scraping the Bones",   3, "Stamina",      "Medicine", 7, None, None, 1, False),
        DisciplinePower("Dust to Dust",         4, "Stamina",      "Medicine", 8, None, None, 1, False),
        DisciplinePower("Withering Nails",      5, "Stamina",      "Medicine", 9, None, None, 2, False),
    ],

    "Visceratika": [
        DisciplinePower("Sanguine Startlement",   1, "Charisma",     "Intimidation",6, "target's current Willpower", None, 0, False),
        DisciplinePower("Encase in Gargoyle Stone",2,"Stamina",      "Occult",      7, None,                         None, 1, False),
        DisciplinePower("Shadow of the Gargoyle", 3, "Manipulation", "Subterfuge",  8, None,                         None, 1, False),
        DisciplinePower("Wings of the Gargoyle",  4, None,           None,          6, None,                         None, 1, True),
        DisciplinePower("Armor of Terra",         5, None,           None,          6, None,                         None, 1, True),
    ],

    # --- Sorcery disciplines (mapped to primary path) ---------------------------

    "Assamite Sorcery": [
        DisciplinePower("Call the Lightning",1, "Intelligence", "Occult", 6, None, None, 1, False,
                        notes="Path of the Levinbolt; other paths have different rolls"),
        DisciplinePower("Focused Strike",    2, "Perception",   "Occult", 7, None, None, 1, False),
        DisciplinePower("Lightning Shield",  3, "Stamina",      "Occult", 6, None, None, 1, False),
        DisciplinePower("Storm Caller",      4, "Intelligence", "Occult", 8, None, None, 2, False),
        DisciplinePower("Thunderstrike",     5, "Intelligence", "Occult", 9, None, None, 2, False),
    ],

    "Koldunic Sorcery": [
        DisciplinePower("Stoneskin",              1, "Stamina",      "Occult", 6, None, None, 1, False,
                        notes="Way of Earth; other Ways have different rolls"),
        DisciplinePower("Rumble",                 2, "Strength",     "Occult", 7, None, None, 1, False),
        DisciplinePower("Swallowed by the Earth", 3, "Manipulation", "Occult", 7, None, None, 1, False),
        DisciplinePower("Earth Melding",          4, "Stamina",      "Occult", 6, None, None, 1, False),
        DisciplinePower("Stasis",                 5, "Stamina",      "Occult", 9, None, None, 2, False),
    ],

    "Setite Sorcery": [
        DisciplinePower("Cobra's Tongue",      1, "Perception",   "Occult",    6, None,                         None,        0, False,
                        notes="Path of the Cobra's Favor; other paths have different rolls"),
        DisciplinePower("Slithering Favor",    2, "Manipulation", "Subterfuge",6, None,                         None,        1, False),
        DisciplinePower("Cobra's Beckoning",   3, "Charisma",     "Occult",    6, "target's current Willpower", "Willpower", 1, False),
        DisciplinePower("Serpent's Reward",    4, "Manipulation", "Occult",    7, None,                         None,        1, False),
        DisciplinePower("Damnation's Promise", 5, "Manipulation", "Occult",    6, "target's current Willpower", "Willpower", 2, False),
    ],
}
