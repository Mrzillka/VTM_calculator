from __future__ import annotations

from functools import wraps
from tkinter import Widget
from tkinter import ttk
from typing import Callable


def place_widgets(grid: list[list[Widget | None]]) -> None:
    """Place widgets in a grid layout (row=y, column=x)."""
    for row_idx, row in enumerate(grid):
        for col_idx, widget in enumerate(row):
            widget.grid(column=col_idx, row=row_idx)
            widget.update()


def frm(padding: int = 5, style: str = "flat.TFrame") -> Callable:
    """
    Decorator that wraps a method in a ttk.Frame.

    The decorated method receives the new frame as its first positional
    argument after ``self``.  An optional ``parent`` keyword argument
    controls the frame's parent widget; when omitted ``self`` is used.
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, parent: ttk.Frame | None = None, *args, **kwargs) -> ttk.Frame:
            frame = ttk.Frame(
                parent if parent is not None else self,
                padding=padding,
                style=style,
            )
            method(self, frame, *args, **kwargs)
            return frame
        return wrapper
    return decorator