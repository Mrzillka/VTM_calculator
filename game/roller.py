from __future__ import annotations

from random import randint

from game.models import RollResult


class Roller:
    """
    Выполняет бросок кубиков по правилам VTM.

    Args:
        dice_number:    количество кубиков.
        difficulty:     сложность броска (2–10).
        auto_success:   автоматические успехи.
        specialisation: включить специализацию (перебросы 10).
        penalty:        штраф (убирает кубики из пула).
    """

    SIDES: int = 10

    def __init__(
            self,
            dice_number: int = 1,
            difficulty: int = 6,
            auto_success: int = 0,
            specialisation: bool = False,
            penalty: int = 0,
    ) -> None:
        self.dice_number = dice_number
        self.difficulty = difficulty
        self.auto_success = auto_success
        self.specialisation = specialisation
        self.penalty = penalty

    def roll(self) -> RollResult:
        """Выполняет бросок и возвращает результат."""
        pool_size = max(1, self.dice_number + self.penalty)
        dice = [randint(1, self.SIDES) for _ in range(pool_size)]
        spec_dice = self._roll_specialisation(dice)

        successes = self._count_successes(dice, spec_dice)
        return RollResult(
            dice=sorted(dice, reverse=True),
            specialisation_dice=spec_dice,
            successes=successes,
        )

    def _roll_specialisation(self, dice: list[int]) -> list[int]:
        """Дополнительные броски за каждую выпавшую 10 при специализации."""
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
        """Подсчитывает нетто-успехи: (успехи + авто) - провалы (единицы)."""
        hits = sum(1 for d in roll_dice + spec_dice if d >= self.difficulty)
        botches = roll_dice.count(1)
        return hits + self.auto_success - botches
