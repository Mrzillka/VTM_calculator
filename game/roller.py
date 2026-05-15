from __future__ import annotations

from random import randint

from game.models import RollResult


class Roller:
    """
    Performs a dice roll according to VTM rules.

    Args:
        dice_number:    number of dice in the pool.
        difficulty:     roll difficulty (2–10).
        auto_success:   automatic successes.
        specialisation: enable specialisation (reroll 10s).
        penalty:        penalty (removes dice from the pool).
        no_botch:       if True, 1s are treated as misses rather than botches.
    """

    SIDES: int = 10

    def __init__(
            self,
            dice_number: int = 1,
            difficulty: int = 6,
            auto_success: int = 0,
            specialisation: bool = False,
            penalty: int = 0,
            no_botch: bool = False,
    ) -> None:
        self.dice_number = dice_number
        self.difficulty = difficulty
        self.auto_success = auto_success
        self.specialisation = specialisation
        self.penalty = penalty
        self.no_botch = no_botch

    def roll(self) -> RollResult:
        """Perform the roll and return the result."""
        pool_size = max(1, self.dice_number + self.penalty)
        dice = [randint(1, self.SIDES) for _ in range(pool_size)]
        spec_dice = self._roll_specialisation(dice)

        successes = self._count_successes(dice, spec_dice)
        return RollResult(
            dice=tuple(sorted(dice, reverse=True)),
            specialisation_dice=tuple(spec_dice),
            successes=successes,
        )

    def _roll_specialisation(self, dice: list[int]) -> list[int]:
        """Additional rolls for each 10 when specialisation is active."""
        if not self.specialisation:
            return []

        extra: list[int] = []
        for die in dice:
            if die == self.SIDES:
                result = randint(1, self.SIDES)
                extra.append(result)
                while result == self.SIDES:
                    result = randint(1, self.SIDES)
                    extra.append(result)
        return extra

    def _count_successes(self, roll_dice: list[int], spec_dice: list[int]) -> int:
        """
        Count net successes: (hits + auto) - botches.

        When no_botch is True, 1s are ignored (damage/soak mode).
        """
        hits = sum(1 for d in roll_dice + spec_dice if d >= self.difficulty)
        botches = 0 if self.no_botch else roll_dice.count(1)
        return hits + self.auto_success - botches