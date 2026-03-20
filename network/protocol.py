from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game.models import RollRecord

# ── Message type identifiers ──────────────────────────────────────────────────

MSG_HELLO          = "hello"           # client → server: identify by name
MSG_ROLL           = "roll"            # bidirectional: dice roll record
MSG_SHEET          = "sheet"           # client → server: full character sheet
MSG_SHEET_TRACKERS = "sheet_trackers"  # client → server: tracker values only
MSG_PING           = "ping"
MSG_PONG           = "pong"


# ── Wire format ───────────────────────────────────────────────────────────────

@dataclass
class Message:
    type: str
    data: dict[str, Any]


def encode(msg: Message) -> bytes:
    """Serialize a Message to a newline-terminated UTF-8 JSON bytes object."""
    return (json.dumps({"type": msg.type, "data": msg.data}) + "\n").encode("utf-8")


def decode(line: str) -> Message:
    """Deserialize a single JSON line into a Message; raises on malformed input."""
    raw = json.loads(line)
    return Message(type=raw["type"], data=raw.get("data", {}))


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
    )