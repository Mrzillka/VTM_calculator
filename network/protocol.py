from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game.models import RollRecord

# ── Message type identifiers ──────────────────────────────────────────────────

MSG_ROLL           = "roll"            # bidirectional: dice roll record
MSG_SHEET          = "sheet"           # player → storyteller: full character sheet
MSG_SHEET_TRACKERS = "sheet_trackers"  # player → storyteller: tracker values only


# ── RollRecord ↔ dict ─────────────────────────────────────────────────────────

def roll_record_to_dict(record: "RollRecord") -> dict[str, Any]:
    return {
        "dice_number":  record.dice_number,
        "difficulty":   record.difficulty,
        "auto_success": record.auto_success,
        "dice":         record.dice,
        "spec_dice":    record.spec_dice,
        "successes":    record.successes,
        "probability":  record.probability,
        "roller_name":  record.roller_name,
        "roll_type":    record.roll_type,
    }


def dict_to_roll_record(data: dict[str, Any]) -> "RollRecord":
    from game.models import RollRecord  # local import to avoid circular dependency
    return RollRecord(
        dice_number  = data["dice_number"],
        difficulty   = data["difficulty"],
        auto_success = data["auto_success"],
        dice         = data["dice"],
        spec_dice    = data["spec_dice"],
        successes    = data["successes"],
        probability  = data["probability"],
        roller_name  = data.get("roller_name", ""),
        roll_type    = data.get("roll_type", "NORMAL"),
    )