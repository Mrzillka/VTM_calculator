"""Shared pytest fixtures for the test suite.

The project is run as scripts (``python main.py``) rather than installed as a
package, so the project root must be importable for ``import game.*`` / ``import
config`` to resolve.  pytest already prepends the directory containing the first
``conftest.py`` to ``sys.path`` (default "prepend" import mode), so placing this
file in ``tests/`` is not enough — we add the project root explicitly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@pytest.fixture(scope="session")
def tk_root():
    """A single hidden Tk root for the whole session.

    ``Character`` stores its state in ``tkinter`` ``Var`` objects, which need a
    live interpreter to attach to.  One withdrawn root is enough for every test;
    creating a fresh ``Tk()`` per test is slow and can leak interpreters.
    """
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def character(tk_root):
    """A fresh, default-state ``Character`` bound to the session Tk root."""
    from game.character import Character

    return Character()
