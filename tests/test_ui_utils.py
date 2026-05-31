"""Tests for ui.utils — the @frm decorator and place_widgets grid helper.

Both create real ttk widgets, so they use the session ``tk_root`` fixture.
"""
from __future__ import annotations

from tkinter import ttk

from ui.utils import frm, place_widgets


class _Builder(ttk.Frame):
    """Stand-in interface object: like real interfaces, it IS a ttk.Frame, so
    ``self`` is a valid widget master for the @frm default-parent path."""

    def __init__(self, master):
        super().__init__(master)
        self.built_with = None

    @frm()
    def section(self, frame):
        self.built_with = frame
        ttk.Label(frame, text="hello")


# ── @frm decorator ───────────────────────────────────────────────────────────

def test_frm_returns_a_frame_and_passes_it_to_the_method(tk_root):
    builder = _Builder(tk_root)
    result = builder.section(parent=tk_root)
    assert isinstance(result, ttk.Frame)
    assert result is builder.built_with


def test_frm_defaults_parent_to_self(tk_root):
    builder = _Builder(tk_root)
    frame = builder.section()                       # parent omitted
    assert frame.master is builder                  # frame is a child of self


def test_frm_uses_explicit_parent_when_given(tk_root):
    builder = _Builder(tk_root)
    other = ttk.Frame(tk_root)
    frame = builder.section(parent=other)
    assert frame.master is other


def test_frm_populates_children(tk_root):
    builder = _Builder(tk_root)
    frame = builder.section(parent=tk_root)
    assert len(frame.winfo_children()) == 1         # the Label we added


# ── place_widgets ────────────────────────────────────────────────────────────

def test_place_widgets_assigns_row_and_column(tk_root):
    parent = ttk.Frame(tk_root)
    a = ttk.Label(parent, text="a")
    b = ttk.Label(parent, text="b")
    c = ttk.Label(parent, text="c")
    place_widgets([[a, b], [c]])

    assert (a.grid_info()["row"], a.grid_info()["column"]) == (0, 0)
    assert (b.grid_info()["row"], b.grid_info()["column"]) == (0, 1)
    assert (c.grid_info()["row"], c.grid_info()["column"]) == (1, 0)


def test_place_widgets_skips_none_cells(tk_root):
    parent = ttk.Frame(tk_root)
    a = ttk.Label(parent, text="a")
    b = ttk.Label(parent, text="b")
    place_widgets([[None, a], [b]])

    # The None at column 0 is skipped (not collapsed) — a stays at column 1.
    assert (a.grid_info()["row"], a.grid_info()["column"]) == (0, 1)
    assert (b.grid_info()["row"], b.grid_info()["column"]) == (1, 0)
