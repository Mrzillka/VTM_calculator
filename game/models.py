from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


def _compute_outcome(successes: int) -> str:
    if successes >= 1:
        return "SUCCESS"
    if successes < 0:
        return "BOTCH"
    return "FAILURE"


@dataclass(frozen=True)
class RollResult:
    """Raw dice roll output from Roller."""
    dice: tuple[int, ...]
    specialisation_dice: tuple[int, ...]
    successes: int

    @property
    def all_dice(self) -> tuple[int, ...]:
        return self.dice + self.specialisation_dice

    @property
    def outcome(self) -> str:
        return _compute_outcome(self.successes)


@dataclass
class RollRecord:
    """Single roll entry stored in the application history."""
    dice_number: int
    difficulty: int
    auto_success: int
    dice: list[int]
    specialisation_dice: list[int]
    successes: int
    probability: float
    # Empty string means the Storyteller rolled (no specific character).
    roller_name: str = field(default="")
    roll_type: Literal["NORMAL", "DAMAGE", "INITIATIVE"] = field(default="NORMAL")

    @property
    def outcome(self) -> str:
        return _compute_outcome(self.successes)