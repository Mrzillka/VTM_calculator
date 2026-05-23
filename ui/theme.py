from __future__ import annotations

from typing import Callable

_LIGHT: dict[str, str] = {
    # Parchment / gothic daylight
    "bg":          "#f5ecd7",   # warm parchment
    "fg":          "#2a1a0e",   # dark sepia
    "entry_bg":    "#fdf6e3",   # pale vellum
    "entry_fg":    "#2a1a0e",
    "btn_bg":      "#c8a97e",   # aged leather
    "btn_active":  "#a07850",   # darker leather on hover
    "border":      "#8b5e3c",   # mahogany border
    "trough":      "#d4b896",   # light leather trough
    "tab_bg":      "#ddc9a0",   # unselected tab — muted parchment
    "tab_sel":     "#f5ecd7",   # selected tab — full parchment
    "select_bg":   "#8b1a1a",   # crimson selection
    "select_fg":   "#fdf6e3",
    "disabled_fg": "#9e8870",   # sepia-toned grey
    # Semantic
    "hit_fg":      "#2e5b1a",   # forest green (success)
    "botch_fg":    "#8b0000",   # dark red (botch die)
    "normal_fg":   "#2a1a0e",
    "success_fg":  "#2e5b1a",
    "failure_fg":  "#7a6652",   # warm grey
    "botch_lbl":   "#8b0000",
    "meta_fg":     "#7a6652",
    "dot_fg":      "#8b1a1a",   # blood-red dots
    "spec_fg":     "#6b4c2a",   # sepia specialisation text
    "delta_pos":   "#2e5b1a",
    "delta_neg":   "#8b0000",
    "virtue_fg":   "#8b0000",   # crimson virtue labels
    "boost_dot":   "#5a8a1a",   # olive green boost
    "sep_fg":      "#8b5e3c",   # mahogany separator
}

_DARK: dict[str, str] = {
    # Crypt / gothic night
    "bg":          "#1a0e0e",   # deep blood-black
    "fg":          "#e8d5b0",   # aged-parchment text
    "entry_bg":    "#2a1515",   # dark crimson-tinted field
    "entry_fg":    "#e8d5b0",
    "btn_bg":      "#4a1f1f",   # blood-wine button
    "btn_active":  "#6b2c2c",   # brighter wine on hover
    "border":      "#8b3a3a",   # dim crimson border
    "trough":      "#3a1a1a",   # very dark wine trough
    "tab_bg":      "#2e1818",   # unselected tab — darker wine
    "tab_sel":     "#1a0e0e",   # selected tab — matches bg
    "select_bg":   "#8b1a1a",   # crimson selection
    "select_fg":   "#e8d5b0",
    "disabled_fg": "#6b5040",   # muted sepia
    # Semantic
    "hit_fg":      "#a8d878",   # pale lime (success on dark)
    "botch_fg":    "#e87070",   # bright red (botch die)
    "normal_fg":   "#e8d5b0",
    "success_fg":  "#a8d878",
    "failure_fg":  "#8a7060",   # warm muted grey
    "botch_lbl":   "#e87070",
    "meta_fg":     "#8a7060",
    "dot_fg":      "#c84040",   # vivid blood-red dots
    "spec_fg":     "#b09070",   # parchment-toned spec text
    "delta_pos":   "#a8d878",
    "delta_neg":   "#e87070",
    "virtue_fg":   "#c84040",   # blood-red virtue labels
    "boost_dot":   "#88cc44",   # bright olive-lime boost
    "sep_fg":      "#6b3535",   # dim crimson separator
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
