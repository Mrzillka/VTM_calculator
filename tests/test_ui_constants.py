"""Sanity checks for ui.constants — the UI-only numeric constants.

These are just values, but a few invariants (min < max, positive intervals)
guard against fat-finger edits that would silently break sliders or polling.
"""
from __future__ import annotations

from ui import constants as c


def test_roll_parameter_ranges_are_ordered():
    assert c.DICE_MIN < c.DICE_MAX
    assert c.DIFFICULTY_MIN < c.DIFFICULTY_MAX


def test_difficulty_range_matches_d10_rules():
    # VTM difficulties run 2..10.
    assert c.DIFFICULTY_MIN == 2
    assert c.DIFFICULTY_MAX == 10


def test_intervals_are_positive():
    for value in (
        c.NET_POLL_MS,
        c.TRACKER_DEBOUNCE_MS,
        c.AUTOSAVE_DEBOUNCE_MS,
        c.BOT_STATUS_POLL_MS,
        c.MOUSEWHEEL_DIVISOR,
    ):
        assert value > 0


def test_window_minimums_do_not_exceed_defaults():
    assert c.SHEET_MIN_WIDTH <= c.SHEET_WIDTH
    assert c.SHEET_MIN_HEIGHT <= c.SHEET_HEIGHT
