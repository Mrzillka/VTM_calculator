from __future__ import annotations

XP_COSTS: dict[str, int] = {
    "attribute":              4,
    "ability":                2,
    "new_ability":            3,   # flat cost for 0→1
    "background":             2,
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
        elif trait_type == "discipline" and not is_inclan:
            total += XP_COSTS["new_discipline_outclan"]
            start = 1

    # Per-dot cost: target_rating × multiplier for each increment
    if trait_type == "attribute":
        mult = XP_COSTS["attribute"]
    elif trait_type == "ability":
        mult = XP_COSTS["ability"]
    elif trait_type == "background":
        mult = XP_COSTS["background"]
    elif trait_type == "discipline":
        mult = XP_COSTS["discipline_inclan"] if is_inclan else XP_COSTS["discipline_outclan"]
    elif trait_type == "virtue":
        mult = XP_COSTS["virtue"]
    elif trait_type == "willpower":
        mult = XP_COSTS["willpower"]
    elif trait_type == "humanity":
        mult = XP_COSTS["humanity"]
    else:
        return total

    for target in range(start + 1, to_dots + 1):
        total += target * mult

    return total
