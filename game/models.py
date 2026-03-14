from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


@dataclass(frozen=True)
class RollResult:
    """Raw dice roll output from Roller."""
    dice: list[int]
    specialisation_dice: list[int]
    successes: int

    @property
    def all_dice(self) -> list[int]:
        return self.dice + self.specialisation_dice

    @property
    def outcome(self) -> str:
        if self.successes >= 1:
            return "SUCCESS"
        if self.successes < 0:
            return "BOTCH"
        return "FAILURE"


@dataclass
class RollRecord:
    """Single roll entry stored in the application history."""
    dice_number: int
    difficulty: int
    auto_success: int
    dice: list[int]
    spec_dice: list[int]
    successes: int
    probability: float

    @property
    def outcome(self) -> str:
        if self.successes >= 1:
            return "SUCCESS"
        if self.successes < 0:
            return "BOTCH"
        return "FAILURE"