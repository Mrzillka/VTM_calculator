from __future__ import annotations

import logging
import tkinter as tk
from functools import wraps
from tkinter import Widget
from tkinter import ttk
from typing import Callable

from config import resource_path

logger = logging.getLogger(__name__)


def apply_icon(window: tk.Wm, icon_name: str, *, inherit: bool = True) -> None:
    """
    Apply an .ico file as window icon (title bar, taskbar, Alt+Tab).

    Args:
        window:   any tkinter window (Tk or Toplevel).
        icon_name: filename relative to the project/bundle root (e.g. 'icon.ico').
        inherit:  passed to wm_iconphoto — True propagates the icon to all
                  future Toplevel children; False applies only to this window.
    """
    path = resource_path(icon_name)
    if not path.exists():
        return
    try:
        from PIL import Image, ImageTk
        window.wm_iconbitmap(str(path))
        img = ImageTk.PhotoImage(Image.open(path))
        window.wm_iconphoto(inherit, img)
        window._icon_ref = img  # type: ignore[attr-defined]  # prevent GC
    except Exception as exc:
        logger.debug("Could not apply icon %s: %s", icon_name, exc)


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