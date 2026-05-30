from __future__ import annotations

from tkinter import ttk

from config import FONT


def configure_main_styles(s: ttk.Style, palette: dict[str, str]) -> None:
    """Register styles for the main application and storyteller windows."""
    bg  = palette["bg"]
    fg  = palette["fg"]
    ebg = palette["entry_bg"]
    efg = palette["entry_fg"]
    bbg = palette["btn_bg"]
    bac = palette["btn_active"]
    bdr = palette["border"]
    tro = palette["trough"]
    dis = palette["disabled_fg"]
    sbg = palette["select_bg"]
    sfg = palette["select_fg"]

    # ── Root defaults ─────────────────────────────────────────────────────────
    s.configure(".", background=bg, foreground=fg, bordercolor=bdr,
                troughcolor=tro, selectbackground=sbg, selectforeground=sfg)

    # ── Frames ────────────────────────────────────────────────────────────────
    s.configure("TFrame",      background=bg)
    s.configure("flat.TFrame", background=bg, relief="flat")
    s.configure("solid.TFrame", background=bg, relief="solid", bordercolor=bdr)

    crim = palette["dot_fg"]   # blood-red / crimson accent

    # ── Labels ────────────────────────────────────────────────────────────────
    s.configure("TLabel",            background=bg, foreground=fg)
    s.configure("title.TLabel",      background=bg, foreground=crim,
                font=(FONT, 20, "bold", "italic"))
    s.configure("L.TLabel",          background=bg, foreground=crim,
                font=(FONT, 18, "bold"))
    s.configure("M.TLabel",          background=bg, foreground=fg,
                font=(FONT, 15, "italic"))
    s.configure("S.TLabel",          background=bg, foreground=fg,
                font=(FONT, 10))
    s.configure("HistoryMeta.TLabel", background=bg,
                foreground=palette["meta_fg"], font=(FONT, 9))
    s.configure("HistoryDice.TLabel", background=bg, foreground=fg,
                font=(FONT, 10))
    s.configure("Success.TLabel",    background=bg,
                foreground=palette["success_fg"], font=(FONT, 13, "bold"))
    s.configure("Failure.TLabel",    background=bg,
                foreground=palette["failure_fg"], font=(FONT, 13, "bold"))
    s.configure("Botch.TLabel",      background=bg,
                foreground=palette["botch_lbl"],  font=(FONT, 13, "bold"))
    s.configure("SuccessCount.TLabel", background=bg,
                foreground=palette["success_fg"], font=(FONT, 11, "bold"))
    s.configure("FailureCount.TLabel", background=bg,
                foreground=palette["failure_fg"], font=(FONT, 11, "bold"))
    s.configure("BotchCount.TLabel",   background=bg,
                foreground=palette["botch_lbl"],  font=(FONT, 11, "bold"))

    # ── Buttons ───────────────────────────────────────────────────────────────
    s.configure("TButton",   background=bbg, foreground=fg,
                bordercolor=bdr, focuscolor=bbg)
    s.map("TButton",
          background=[("active", bac), ("disabled", bbg)],
          foreground=[("disabled", dis)])
    s.configure("L.TButton", font=(FONT, 15))
    s.configure("M.TButton", font=(FONT, 12, "italic"))
    s.configure("S.TButton", font=(FONT, 10))

    # ── Entry ─────────────────────────────────────────────────────────────────
    s.configure("TEntry", fieldbackground=ebg, foreground=efg,
                selectbackground=sbg, selectforeground=sfg,
                insertcolor=efg, bordercolor=bdr)
    s.map("TEntry", fieldbackground=[("disabled", ebg)],
          foreground=[("disabled", dis)])
    s.configure("my.TEntry", font=(FONT, 10))

    # ── Spinbox ───────────────────────────────────────────────────────────────
    s.configure("TSpinbox", fieldbackground=ebg, foreground=efg,
                background=bbg, selectbackground=sbg, selectforeground=sfg,
                insertcolor=efg, bordercolor=bdr, arrowcolor=fg)
    s.map("TSpinbox", fieldbackground=[("disabled", ebg)],
          foreground=[("disabled", dis)])
    s.configure("my.TSpinbox", font=(FONT, 10))

    # ── Checkbutton ───────────────────────────────────────────────────────────
    s.configure("TCheckbutton", background=bg, foreground=fg)
    s.map("TCheckbutton", background=[("active", bg)])
    s.configure("my.TCheckbutton", font=(FONT, 10))

    # ── Scale ─────────────────────────────────────────────────────────────────
    s.configure("Horizontal.TScale", background=bg, troughcolor=tro,
                bordercolor=bdr)
    s.configure("my.Horizontal.TScale", font=(FONT, 10))
    s.configure("Vertical.TScale", background=bg, troughcolor=tro,
                bordercolor=bdr)

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    s.configure("TScrollbar", background=tro, troughcolor=bg,
                arrowcolor=fg, bordercolor=bdr)
    s.map("TScrollbar", background=[("active", bac)])

    # ── Combobox ─────────────────────────────────────────────────────────────
    s.configure("TCombobox", fieldbackground=ebg, foreground=efg,
                background=bbg, selectbackground=sbg, selectforeground=sfg,
                insertcolor=efg, bordercolor=bdr, arrowcolor=fg)
    s.map("TCombobox",
          fieldbackground=[("readonly", bbg)],
          foreground=[("disabled", dis)])

    # ── Notebook ─────────────────────────────────────────────────────────────
    s.configure("TNotebook", background=bg, bordercolor=bdr, tabmargins=0)
    s.configure("TNotebook.Tab", background=palette["tab_bg"], foreground=palette["disabled_fg"],
                padding=(8, 4))
    s.map("TNotebook.Tab",
          background=[("selected", palette["tab_sel"]), ("active", bac)],
          foreground=[("selected", crim), ("active", fg)])

    # ── Separator ─────────────────────────────────────────────────────────────
    s.configure("TSeparator", background=bdr)


def configure_sheet_styles(s: ttk.Style, palette: dict[str, str]) -> None:
    """Register styles for the character sheet window."""
    bg  = palette["bg"]
    fg  = palette["fg"]
    ebg = palette["entry_bg"]
    efg = palette["entry_fg"]
    bbg = palette["btn_bg"]
    bac = palette["btn_active"]
    bdr = palette["border"]
    sbg = palette["select_bg"]
    sfg = palette["select_fg"]
    dis = palette["disabled_fg"]

    s.configure("TFrame",       background=bg)
    s.configure("flat.TFrame",  background=bg, relief="flat")
    s.configure("solid.TFrame", background=bg, relief="solid", bordercolor=bdr)

    s.configure("sheet.TButton",      background=bbg, foreground=fg,
                bordercolor=bdr, focuscolor=bbg, font=(FONT, 15))
    s.map("sheet.TButton",
          background=[("active", bac), ("disabled", bbg)],
          foreground=[("disabled", dis)])
    s.configure("sheet.save.TButton", font=(FONT, 12))

    s.configure("sheet.TEntry",    fieldbackground=ebg, foreground=efg,
                selectbackground=sbg, selectforeground=sfg,
                insertcolor=efg, bordercolor=bdr, font=(FONT, 10))
    s.map("sheet.TEntry", fieldbackground=[("disabled", ebg)],
          foreground=[("disabled", dis)])

    s.configure("sheet.TSpinbox", fieldbackground=ebg, foreground=efg,
                background=bbg, selectbackground=sbg, selectforeground=sfg,
                insertcolor=efg, bordercolor=bdr, arrowcolor=fg,
                font=(FONT, 10))
    s.map("sheet.TSpinbox", fieldbackground=[("disabled", ebg)],
          foreground=[("disabled", dis)])

    s.configure("sheet.TCheckbutton", background=bg, foreground=fg,
                font=(FONT, 10))
    s.map("sheet.TCheckbutton", background=[("active", bg)])

    crim = palette["dot_fg"]
    s.configure("sheet.title.TLabel", background=bg, foreground=crim,
                font=(FONT, 15, "bold", "italic"))
    s.configure("sheet.L.TLabel",     background=bg, foreground=crim,
                font=(FONT, 15, "italic"))
    s.configure("sheet.M.TLabel",     background=bg, foreground=fg,
                font=(FONT, 12, "italic"))
    s.configure("sheet.S.TLabel",     background=bg, foreground=fg,
                font=(FONT, 10))
    s.configure("sheet.Dot.TLabel",   background=bg, foreground=fg,
                font=(FONT, 12))
    s.configure("sheet.Sep.TLabel",   background=bg,
                foreground=palette["sep_fg"], font=(FONT, 8))

    s.configure("TScrollbar", background=palette["trough"], troughcolor=bg,
                arrowcolor=fg, bordercolor=bdr)
    s.map("TScrollbar", background=[("active", palette["btn_active"])])
