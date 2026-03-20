from __future__ import annotations

from collections import defaultdict


class Calculator:
    """
    Args:
        dice_number:    number of dice in the pool.
        difficulty:     roll difficulty (2–10).
        success_needed: minimum net successes required.
        auto_successes: automatic successes added before threshold check.
        specialisation: whether specialisation (10-rerolls) is active.
    """

    SIDES: int = 10

    def __init__(
            self,
            dice_number: int = 1,
            difficulty: int = 6,
            success_needed: int = 1,
            auto_successes: int = 0,
            specialisation: bool = False,
    ) -> None:
        self.dice_number    = dice_number
        self.difficulty     = difficulty
        self.success_needed = success_needed
        self.auto_successes = auto_successes
        self.specialisation = specialisation

    def get_probability(self) -> float:
        """Return success probability as a percentage (0–100)."""
        die_dist = self._single_die_distribution()

        dp: dict[int, float] = {0: 1.0}
        for _ in range(self.dice_number):
            new_dp: dict[int, float] = defaultdict(float)
            for score, prob in dp.items():
                for delta, p in die_dist.items():
                    new_dp[score + delta] += prob * p
            dp = dict(new_dp)

        threshold = self.success_needed - self.auto_successes
        return sum(p for s, p in dp.items() if s >= threshold) * 100.0

    def _single_die_distribution(self) -> dict[int, float]:
        """
        Return {net_score: probability} for one die roll.

        Without specialisation a 10 is a regular hit.
        With specialisation a 10 grants +1 and triggers an extra die roll;
        chains are modelled to depth 20 (residual probability ≈ 10⁻²⁰).
        """
        p_10  = 1.0 / self.SIDES
        # Base outcomes, excluding the 10-face:
        base: dict[int, float] = {
            -1: 1.0 / self.SIDES,
             0: max(0.0, (self.difficulty - 2) / self.SIDES),
             1: max(0.0, (self.SIDES - self.difficulty) / self.SIDES),
        }

        if not self.specialisation:
            base[1] = base.get(1, 0.0) + p_10
            return base

        # Specialisation: rolling 10 → +1 and roll again (may chain).
        # dist[k] = base[k] + sum_{depth≥1} (p_10^depth * base[k - depth])
        dist: dict[int, float] = dict(base)
        chain_p = p_10
        for depth in range(1, 21):
            for score, p in base.items():
                k = score + depth
                dist[k] = dist.get(k, 0.0) + chain_p * p
            chain_p *= p_10
        return dist