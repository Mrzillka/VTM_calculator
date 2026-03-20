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
        no_botch:       if True, 1s are treated as misses (damage/soak mode).
    """

    SIDES: int = 10

    def __init__(
            self,
            dice_number: int = 1,
            difficulty: int = 6,
            success_needed: int = 1,
            auto_successes: int = 0,
            specialisation: bool = False,
            no_botch: bool = False,
    ) -> None:
        self.dice_number    = dice_number
        self.difficulty     = difficulty
        self.success_needed = success_needed
        self.auto_successes = auto_successes
        self.specialisation = specialisation
        self.no_botch       = no_botch

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
        With specialisation a 10 grants +1 and triggers an extra die roll.

        When no_botch is True, 1s count as misses instead of -1 botches.
        Chains are modelled to depth 20 (residual probability ≈ 10⁻²⁰).
        """
        p_10 = 1.0 / self.SIDES

        if self.no_botch:
            # 1 through difficulty-1: miss; difficulty through 10: hit
            base: dict[int, float] = {
                0: max(0.0, (self.difficulty - 1) / self.SIDES),
                1: max(0.0, (self.SIDES - self.difficulty + 1) / self.SIDES),
            }
            if not self.specialisation:
                return base
            # Adjust for specialisation chains (10 face already counted as hit in base)
            dist: dict[int, float] = {k: v for k, v in base.items() if k != 1 or True}
            # Remove the 10-face hit from base[1] and re-add with chaining
            base_no_10 = dict(base)
            base_no_10[1] = max(0.0, base_no_10.get(1, 0.0) - p_10)
            dist = dict(base_no_10)
            chain_p = p_10
            for depth in range(1, 21):
                for score, p in base_no_10.items():
                    k = score + depth
                    dist[k] = dist.get(k, 0.0) + chain_p * p
                chain_p *= p_10
            return dist
        else:
            # Base outcomes, excluding the 10-face:
            base = {
                -1: 1.0 / self.SIDES,
                 0: max(0.0, (self.difficulty - 2) / self.SIDES),
                 1: max(0.0, (self.SIDES - self.difficulty) / self.SIDES),
            }

            if not self.specialisation:
                base[1] = base.get(1, 0.0) + p_10
                return base

            dist = dict(base)
            chain_p = p_10
            for depth in range(1, 21):
                for score, p in base.items():
                    k = score + depth
                    dist[k] = dist.get(k, 0.0) + chain_p * p
                chain_p *= p_10
            return dist