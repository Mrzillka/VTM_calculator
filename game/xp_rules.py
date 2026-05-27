from __future__ import annotations

XP_COSTS: dict[str, int] = {
    "attribute":              4,
    "ability":                2,
    "new_ability":            3,   # flat cost for 0→1
    "secondary_ability":      1,
    "new_secondary_ability":  2,   # flat cost for 0→1
    "background":             0,
    "discipline_inclan":      5,
    "discipline_outclan":     7,
    "new_discipline_outclan": 10,  # flat cost for 0→1 out-of-clan
    "virtue":                 2,
    "willpower":              1,
    "humanity":               2,
}


def xp_for_increase(
    trait_type: str,
    from_dots: int,
    to_dots: int,
    *,
    is_inclan: bool = True,
) -> int:
    """Return XP cost to raise a trait from from_dots to to_dots.

    Trait types: "attribute", "ability", "background", "discipline",
    "virtue", "willpower", "humanity".
    Returns 0 if to_dots <= from_dots.

    Per-dot cost formula: target_rating × multiplier, summed for each increment.
    First-dot special cases:
      - ability 0→1:            3 XP flat (new_ability)
      - secondary ability 0→1:            2 XP flat (new_ability)
      - discipline 0→1 out-of-clan: 10 XP flat (new_discipline_outclan)
    """
    if to_dots <= from_dots:
        return 0

    total = 0
    start = from_dots

    # First-dot flat costs (only when starting from 0)
    if start == 0:
        if trait_type == "ability":
            total += XP_COSTS["new_ability"]
            start = 1
        elif trait_type == "secondary_ability":
            total += XP_COSTS["new_secondary_ability"]
            start = 1
        elif trait_type == "discipline":
            total += XP_COSTS["new_discipline_outclan"]
            start = 1

    # Per-dot cost: (target_rating - 1) × multiplier for each increment
    if trait_type != "discipline" and trait_type:
        mult = XP_COSTS[trait_type] if trait_type else None
    elif trait_type == "discipline":
        mult = XP_COSTS["discipline_inclan"] if is_inclan else XP_COSTS["discipline_outclan"]
    else:
        return total

    for target in range(start + 1, to_dots + 1):
        total += (target - 1) * mult

    return total
