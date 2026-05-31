"""Tests for ui.theme — the light/dark palette singleton.

``theme`` is a module-level singleton, so each test snapshots and restores its
mutable state (mode + callbacks) to stay isolated.
"""
from __future__ import annotations

import pytest

from ui.theme import _DARK, _LIGHT, theme


@pytest.fixture(autouse=True)
def restore_theme_state():
    saved_mode = theme._mode
    saved_callbacks = list(theme._callbacks)
    yield
    theme._mode = saved_mode
    theme._callbacks = saved_callbacks


# ── palette / mode ───────────────────────────────────────────────────────────

def test_palette_follows_mode():
    theme.set_mode("light")
    assert theme.palette is _LIGHT
    theme.set_mode("dark")
    assert theme.palette is _DARK


def test_set_mode_ignores_unknown_values():
    theme.set_mode("light")
    theme.set_mode("technicolor")     # invalid -> no change
    assert theme.mode == "light"


def test_set_mode_does_not_fire_callbacks():
    fired = []
    theme.set_mode("light")
    theme.on_change(lambda: fired.append(1))
    theme.set_mode("dark")            # restore path: silent
    assert fired == []


# ── toggle ───────────────────────────────────────────────────────────────────

def test_toggle_flips_mode():
    theme.set_mode("light")
    theme.toggle()
    assert theme.mode == "dark"
    theme.toggle()
    assert theme.mode == "light"


def test_toggle_fires_callbacks():
    calls = []
    theme.on_change(lambda: calls.append(theme.mode))
    theme.set_mode("light")
    theme.toggle()
    assert calls == ["dark"]


def test_toggle_prunes_callbacks_that_raise():
    theme.set_mode("light")
    good = []

    def boom():
        raise RuntimeError("dead widget")

    theme.on_change(boom)
    theme.on_change(lambda: good.append(1))

    theme.toggle()                    # boom raises and should be pruned
    assert len(good) == 1

    theme.toggle()                    # boom is gone; good still fires
    assert len(good) == 2
    assert boom not in theme._callbacks


# ── palette completeness ─────────────────────────────────────────────────────

def test_light_and_dark_define_the_same_keys():
    # A key present in one palette but not the other crashes styling at runtime.
    assert set(_LIGHT) == set(_DARK)


def test_palette_values_are_hex_colors():
    for palette in (_LIGHT, _DARK):
        for key, value in palette.items():
            assert value.startswith("#"), key
            assert len(value) == 7, key
