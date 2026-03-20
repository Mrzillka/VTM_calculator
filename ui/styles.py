from __future__ import annotations

from tkinter import ttk

from config import FONT

_MAIN_STYLES: dict[str, dict] = {
    "flat.TFrame":          {"relief": "flat"},
    "solid.TFrame":         {"relief": "solid"},
    "L.TButton":            {"font": (FONT, 15)},
    "M.TButton":            {"font": (FONT, 12, "italic")},
    "S.TButton":            {"font": (FONT, 10)},
    "my.TEntry":            {"font": (FONT, 10)},
    "my.Horizontal.TScale": {"font": (FONT, 10)},
    "my.TSpinbox":          {"font": (FONT, 10)},
    "my.TCheckbutton":      {"font": (FONT, 10)},
    "title.TLabel":         {"font": (FONT, 20, "bold", "italic")},
    "L.TLabel":             {"font": (FONT, 18, "bold")},
    "M.TLabel":             {"font": (FONT, 15, "italic")},
    "S.TLabel":             {"font": (FONT, 10)},
    "HistoryMeta.TLabel":   {"font": (FONT, 9),  "foreground": "gray"},
    "HistoryDice.TLabel":   {"font": (FONT, 10)},
    "Success.TLabel":       {"font": (FONT, 13, "bold"), "foreground": "#2e7d32"},
    "Failure.TLabel":       {"font": (FONT, 13, "bold"), "foreground": "#757575"},
    "Botch.TLabel":         {"font": (FONT, 13, "bold"), "foreground": "#c62828"},
    "SuccessCount.TLabel":  {"font": (FONT, 11, "bold"), "foreground": "#2e7d32"},
    "FailureCount.TLabel":  {"font": (FONT, 11, "bold"), "foreground": "#757575"},
    "BotchCount.TLabel":    {"font": (FONT, 11, "bold"), "foreground": "#c62828"},
}

_SHEET_STYLES: dict[str, dict] = {
    "flat.TFrame":          {"relief": "flat"},
    "solid.TFrame":         {"relief": "solid"},
    "sheet.TButton":        {"font": (FONT, 15)},
    "sheet.save.TButton":   {"font": (FONT, 12)},
    "sheet.TEntry":         {"font": (FONT, 10)},
    "sheet.TSpinbox":       {"font": (FONT, 10)},
    "sheet.TCheckbutton":   {"font": (FONT, 10)},
    "sheet.title.TLabel":   {"font": (FONT, 15, "bold", "italic")},
    "sheet.L.TLabel":       {"font": (FONT, 15, "italic")},
    "sheet.M.TLabel":       {"font": (FONT, 12, "italic")},
    "sheet.S.TLabel":       {"font": (FONT, 10)},
    "sheet.Dot.TLabel":     {"font": (FONT, 12)},
    "sheet.Sep.TLabel":     {"font": (FONT, 8),  "foreground": "gray"},
}


def configure_main_styles(s: ttk.Style) -> None:
    """Register styles for the main application and storyteller windows."""
    for name, opts in _MAIN_STYLES.items():
        s.configure(name, **opts)


def configure_sheet_styles(s: ttk.Style) -> None:
    """Register styles for the character sheet window."""
    for name, opts in _SHEET_STYLES.items():
        s.configure(name, **opts)