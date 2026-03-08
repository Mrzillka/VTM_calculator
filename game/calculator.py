from __future__ import annotations

from collections import defaultdict


class Calculator:
    """

    Args:
        dice_number:    количество кубиков.
        difficulty:     сложность (2–10).
        success_needed: минимальное количество успехов.
        auto_successes: автоматические успехи.
    """

    SIDES: int = 10

    def __init__(
            self,
            dice_number: int = 1,
            difficulty: int = 6,
            success_needed: int = 1,
            auto_successes: int = 0,
    ) -> None:
        self.dice_number = dice_number
        self.difficulty = difficulty
        self.success_needed = success_needed
        self.auto_successes = auto_successes

    # ── Публичный API ──────────────────────────────────────────────────────────

    def get_probability(self) -> float:
        """
        Возвращает вероятность успеха в процентах (0–100).

        Алгоритм: DP по количеству нетто-успехов после каждого кубика.
        Каждый кубик:
          - даёт +1, если результат >= difficulty   (вероятность p_hit)
          - даёт -1, если результат == 1             (вероятность p_botch)
          - не меняет счёт иначе                     (вероятность p_miss)
        """
        p_hit = (self.SIDES - self.difficulty + 1) / self.SIDES
        p_botch = 1.0 / self.SIDES
        p_miss = max(0.0, (self.difficulty - 2) / self.SIDES)

        # dp: {net_score: вероятность}
        dp: dict[int, float] = {0: 1.0}

        for _ in range(self.dice_number):
            new_dp: dict[int, float] = defaultdict(float)
            for score, prob in dp.items():
                new_dp[score + 1] += prob * p_hit
                new_dp[score - 1] += prob * p_botch
                new_dp[score] += prob * p_miss
            dp = dict(new_dp)

        threshold = self.success_needed - self.auto_successes
        return sum(p for s, p in dp.items() if s >= threshold) * 100.0
