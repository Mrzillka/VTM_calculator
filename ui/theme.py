from __future__ import annotations

from typing import Callable

_LIGHT: dict[str, str] = {
    "bg":          "#f0f0f0",
    "fg":          "#000000",
    "entry_bg":    "#ffffff",
    "entry_fg":    "#000000",
    "btn_bg":      "#e1e1e1",
    "btn_active":  "#c8c8c8",
    "border":      "#adadad",
    "trough":      "#c8c8c8",
    "tab_bg":      "#d9d9d9",
    "tab_sel":     "#f0f0f0",
    "select_bg":   "#0078d7",
    "select_fg":   "#ffffff",
    "disabled_fg": "gray",
    # Semantic
    "hit_fg":      "#1b5e20",
    "botch_fg":    "#b71c1c",
    "normal_fg":   "",
    "success_fg":  "#2e7d32",
    "failure_fg":  "#757575",
    "botch_lbl":   "#c62828",
    "meta_fg":     "gray",
    "dot_fg":      "#8b1a1a",
    "spec_fg":     "#555555",
    "delta_pos":   "#2d8a2d",
    "delta_neg":   "#cc3333",
    "virtue_fg":   "crimson",
    "boost_dot":   "green3",
    "sep_fg":      "gray",
}

_DARK: dict[str, str] = {
    "bg":          "#1e1e1e",
    "fg":          "#e0e0e0",
    "entry_bg":    "#2d2d2d",
    "entry_fg":    "#e0e0e0",
    "btn_bg":      "#3c3c3c",
    "btn_active":  "#505050",
    "border":      "#555555",
    "trough":      "#4a4a4a",
    "tab_bg":      "#2d2d2d",
    "tab_sel":     "#1e1e1e",
    "select_bg":   "#0e639c",
    "select_fg":   "#ffffff",
    "disabled_fg": "#666666",
    # Semantic
    "hit_fg":      "#81c784",
    "botch_fg":    "#ef9a9a",
    "normal_fg":   "#e0e0e0",
    "success_fg":  "#81c784",
    "failure_fg":  "#9e9e9e",
    "botch_lbl":   "#ef9a9a",
    "meta_fg":     "#9e9e9e",
    "dot_fg":      "#e57373",
    "spec_fg":     "#9e9e9e",
    "delta_pos":   "#81c784",
    "delta_neg":   "#ef9a9a",
    "virtue_fg":   "#e57373",
    "boost_dot":   "#69f0ae",
    "sep_fg":      "#9e9e9e",
}

_PALETTES: dict[str, dict[str, str]] = {"light": _LIGHT, "dark": _DARK}


class _Theme:
    def __init__(self) -> None:
        self._mode: str = "light"
        self._callbacks: list[Callable[[], None]] = []

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def palette(self) -> dict[str, str]:
        return _PALETTES[self._mode]

    def set_mode(self, mode: str) -> None:
        """Restore from env — no callbacks fired."""
        if mode in _PALETTES:
            self._mode = mode

    def toggle(self) -> None:
        """Flip mode and fire all on_change callbacks; prunes dead ones."""
        self._mode = "dark" if self._mode == "light" else "light"
        dead: list[int] = []
        for i, cb in enumerate(self._callbacks):
            try:
                cb()
            except Exception:
                dead.append(i)
        for i in reversed(dead):
            self._callbacks.pop(i)

    def on_change(self, cb: Callable[[], None]) -> None:
        self._callbacks.append(cb)


theme = _Theme()
