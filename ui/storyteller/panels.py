from __future__ import annotations

import json
import shutil
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from config import NPC_DIR, PC_DIR
from game.character import Character
from lang import locale
from ui.constants import MOUSEWHEEL_DIVISOR


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _ratio_var(value_var: tk.IntVar, max_var: tk.IntVar) -> tk.StringVar:
    """Return a StringVar that stays formatted as 'value/max' via traces."""
    out = tk.StringVar()

    def _update(*_) -> None:
        out.set(f"{value_var.get()}/{max_var.get()}")

    value_var.trace_add("write", _update)
    max_var.trace_add("write", _update)
    _update()
    return out


def _stat_pair(
    parent: ttk.Frame,
    title: str,
    var: tk.Variable,
    *,
    row: int,
    col: int,
) -> None:
    """Render a 'Title: value' pair into *parent* at the given grid position."""
    ttk.Label(parent, text=f"{title}:", style="HistoryMeta.TLabel",
              anchor="e", width=8).grid(row=row, column=col, sticky="e")
    ttk.Label(parent, textvariable=var, style="S.TLabel",
              anchor="w", width=8).grid(row=row, column=col + 1, sticky="w", padx=(2, 8))


def _make_scroll_canvas(parent: ttk.Frame, *, width: int, height: int) -> ttk.Frame:
    """
    Build a Canvas + vertical Scrollbar at row=1 of *parent* and return the inner Frame.

    *parent* must use grid layout; row=0 is reserved for a header.
    """
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
    sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)

    canvas.grid(row=1, column=0, sticky="nsew")
    sb.grid(row=1, column=1, sticky="ns")
    parent.grid_rowconfigure(1, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    inner = ttk.Frame(canvas)
    wid = canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

    def _scroll(e: tk.Event) -> None:
        canvas.yview_scroll(int(-1 * (e.delta / MOUSEWHEEL_DIVISOR)), "units")

    canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _scroll))
    canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
    canvas.bind("<Button-4>", lambda _: canvas.yview_scroll(-1, "units"))
    canvas.bind("<Button-5>", lambda _: canvas.yview_scroll(1, "units"))

    return inner


def _panel_header(parent: ttk.Frame, title: str, btn_text: str, btn_cmd) -> None:
    """Render a two-column header (title left, button right) at row=0 of *parent*."""
    hdr = ttk.Frame(parent, style="flat.TFrame")
    ttk.Label(hdr, text=title, style="M.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Button(hdr, text=btn_text, style="S.TButton", command=btn_cmd).grid(
        row=0, column=1, padx=(8, 0), sticky="e"
    )
    hdr.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
    hdr.grid_columnconfigure(0, weight=1)


# ── PC Panel ───────────────────────────────────────────────────────────────────

class PCPanel(ttk.Frame):
    """Scrollable GM panel showing read-only player character summary cards."""

    WIDTH = 260
    HEIGHT = 420

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="solid.TFrame", padding=4)
        self._entries: list[dict] = []
        self._sheet_wins: dict[Path, tk.Toplevel] = {}
        self._build()
        self._load_directory()

    def _build(self) -> None:
        _panel_header(self, "Players", "+ Load PC", self._browse_and_load)
        self._inner = _make_scroll_canvas(self, width=self.WIDTH, height=self.HEIGHT)

    # ── Network callbacks ──────────────────────────────────────────────────────

    def on_sheet_received(self, data: dict) -> None:
        """
        Apply a full character sheet received from a player over the network.

        Matches by character_name.  If no existing entry matches, a new
        in-memory card is created (not persisted to disk on the GM side).
        """
        name = data.get("header", {}).get("character_name", "")
        for entry in self._entries:
            if entry["char"].character_name.get() == name:
                entry["char"].load(data)
                entry["char"].apply_trackers()
                return

        # Unknown character: create a live in-memory card.
        char = Character()
        char.load(data)
        char.apply_trackers()
        path = PC_DIR / f"_live_{uuid.uuid4().hex[:8]}.json"
        entry: dict = {"char": char, "path": path, "card": None}
        self._entries.append(entry)
        card = _build_pc_card(
            self._inner, char,
            on_open=lambda c=char, p=path: self._open_sheet(c, p),
            on_remove=lambda e=entry: self._remove_entry(e),
        )
        entry["card"] = card
        card.pack(fill="x", padx=2, pady=(0, 4))

    def on_trackers_received(self, data: dict) -> None:
        """
        Apply tracker-only update received from a player over the network.

        Silently ignored if the character name is not found in the panel.
        Concurrent updates from different players are safe because each name
        maps to a distinct Character instance.
        """
        name = data.get("character_name", "")
        trackers = data.get("trackers", {})
        for entry in self._entries:
            if entry["char"].character_name.get() == name:
                char = entry["char"]
                char.blood_max_value.set(
                    trackers.get("blood_max_value", char.blood_max_value.get()))
                char.blood_value.set(
                    trackers.get("blood_value", char.blood_value.get()))
                char.wounds_value.set(
                    trackers.get("wounds_value", char.wounds_value.get()))
                char.humanity_value.set(
                    trackers.get("humanity_value", char.humanity_value.get()))
                char.will_value.set(
                    trackers.get("will_value", char.will_value.get()))
                char.willpower_max.set(
                    trackers.get("willpower_max", char.willpower_max.get()))
                char.apply_trackers()
                return

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_directory(self) -> None:
        if not PC_DIR.exists():
            return
        for path in sorted(PC_DIR.glob("*.json")):
            # Skip temporary live cards written by on_sheet_received.
            if path.stem.startswith("_live_"):
                continue
            self._load_file(path)

    def _load_file(self, path: Path) -> None:
        try:
            char = Character()
            with open(path, encoding="utf-8") as f:
                char.load(json.load(f))
            char.apply_trackers()
        except Exception as exc:
            messagebox.showerror("PC Load Error", f"{path.name}: {exc}")
            return
        entry: dict = {"char": char, "path": path, "card": None}
        self._entries.append(entry)
        card = _build_pc_card(
            self._inner, char,
            on_open=lambda c=char, p=path: self._open_sheet(c, p),
            on_remove=lambda e=entry: self._remove_entry(e),
        )
        entry["card"] = card
        card.pack(fill="x", padx=2, pady=(0, 4))

    def _browse_and_load(self) -> None:
        src = filedialog.askopenfilename(
            title="Load Player Character",
            filetypes=[("JSON files", "*.json")],
        )
        if not src:
            return
        src_path = Path(src)
        dst = PC_DIR / src_path.name
        if dst.exists():
            if dst.resolve() == src_path.resolve():
                return
            if not messagebox.askyesno(
                "Load PC",
                f"'{src_path.name}' is already loaded. Overwrite?",
            ):
                return
            for entry in self._entries:
                if entry["path"].resolve() == dst.resolve():
                    self._remove_entry(entry)
                    break
        shutil.copy2(src, dst)
        self._load_file(dst)

    def _remove_entry(self, entry: dict) -> None:
        name = entry["char"].character_name.get()
        if not messagebox.askyesno("Remove PC", f"Remove '{name}' from the panel?"):
            return
        win = self._sheet_wins.pop(entry["path"], None)
        if win and win.winfo_exists():
            win.destroy()
        entry["path"].unlink(missing_ok=True)
        self._entries.remove(entry)
        entry["card"].destroy()

    def _open_sheet(self, char: Character, path: Path) -> None:
        win = self._sheet_wins.get(path)
        if win and win.winfo_exists():
            win.lift()
            win.focus_force()
            return
        from ui.charsheet.root import CharsheetWindow
        win = CharsheetWindow(character=char, read_only=True)
        self._sheet_wins[path] = win


# ── NPC Panel ──────────────────────────────────────────────────────────────────

class NPCPanel(ttk.Frame):
    """Scrollable GM panel for creating and managing NPC summary cards."""

    WIDTH = 280
    HEIGHT = 420

    def __init__(
        self,
        parent: ttk.Frame,
        *,
        on_roster_change: Callable[[], None] | None = None,
        on_set_roller: Callable[[str], None] | None = None,
        on_quick_roll: Callable[[str, int, bool], None] | None = None,
    ) -> None:
        super().__init__(parent, style="solid.TFrame", padding=4)
        self._on_roster_change = on_roster_change
        self._on_set_roller = on_set_roller
        self._on_quick_roll = on_quick_roll
        self._entries: list[dict] = []
        self._sheet_wins: dict[Path, tk.Toplevel] = {}
        self._build()
        self._load_directory()

    def get_npc_entries(self) -> list[dict]:
        """Return the live list of NPC entries (read-only intent)."""
        return self._entries

    def _build(self) -> None:
        _panel_header(self, "NPCs", "+ New NPC", self._create_npc)
        self._inner = _make_scroll_canvas(self, width=self.WIDTH, height=self.HEIGHT)

    def _notify(self) -> None:
        if self._on_roster_change:
            self._on_roster_change()

    def _load_directory(self) -> None:
        if not NPC_DIR.exists():
            return
        for path in sorted(NPC_DIR.glob("*.json")):
            self._load_file(path)

    def _load_file(self, path: Path) -> None:
        try:
            char = Character()
            with open(path, encoding="utf-8") as f:
                char.load(json.load(f))
            char.apply_trackers()
        except Exception as exc:
            messagebox.showerror("NPC Load Error", f"{path.name}: {exc}")
            return
        entry: dict = {"char": char, "path": path, "card": None}
        self._entries.append(entry)
        self._append_card(entry)
        self._notify()
        char.character_name.trace_add("write", lambda *_: self._notify())

    def _create_npc(self) -> None:
        char = Character()
        path = NPC_DIR / f"{uuid.uuid4().hex[:12]}.json"
        char.save(path=path)
        entry: dict = {"char": char, "path": path, "card": None}
        self._entries.append(entry)
        self._append_card(entry)
        self._notify()
        char.character_name.trace_add("write", lambda *_: self._notify())
        self._open_sheet(char, path)

    def _append_card(self, entry: dict) -> None:
        char = entry["char"]
        path = entry["path"]
        set_roller_cb = (
            (lambda c=char: self._on_set_roller(c.character_name.get()))
            if self._on_set_roller else None
        )
        quick_roll_cb = (
            (lambda rname, pool, nb: self._on_quick_roll(rname, pool, nb))
            if self._on_quick_roll else None
        )
        card = _build_npc_card(
            self._inner, char,
            on_open=lambda c=char, p=path: self._open_sheet(c, p),
            on_remove=lambda e=entry: self._remove_entry(e),
            on_set_roller=set_roller_cb,
            on_quick_roll=quick_roll_cb,
        )
        entry["card"] = card
        card.pack(fill="x", padx=2, pady=(0, 4))

    def _remove_entry(self, entry: dict) -> None:
        name = entry["char"].character_name.get()
        if not messagebox.askyesno("Delete NPC", f"Delete '{name}'?"):
            return
        win = self._sheet_wins.pop(entry["path"], None)
        if win and win.winfo_exists():
            win.destroy()
        entry["path"].unlink(missing_ok=True)
        self._entries.remove(entry)
        entry["card"].destroy()
        self._notify()

    def _open_sheet(self, char: Character, path: Path) -> None:
        win = self._sheet_wins.get(path)
        if win and win.winfo_exists():
            win.lift()
            win.focus_force()
            return
        from ui.charsheet.root import CharsheetWindow
        win = CharsheetWindow(character=char, save_path=path)
        self._sheet_wins[path] = win


# ── Card builders ──────────────────────────────────────────────────────────────

def _card_buttons(
    parent: ttk.Frame,
    on_open: Callable,
    on_remove: Callable,
    *,
    on_set_roller: Callable | None = None,
) -> ttk.Frame:
    frm = ttk.Frame(parent, style="flat.TFrame")
    col = 0
    if on_set_roller:
        ttk.Button(frm, text="▶", style="S.TButton", width=2,
                   command=on_set_roller).grid(row=0, column=col, padx=(0, 4))
        col += 1
    ttk.Button(frm, text="Sheet", style="S.TButton", command=on_open).grid(row=0, column=col)
    ttk.Button(frm, text="✕", style="S.TButton", width=2, command=on_remove).grid(
        row=0, column=col + 1, padx=(4, 0)
    )
    return frm


def _build_pc_card(
    parent: ttk.Frame,
    char: Character,
    *,
    on_open: Callable,
    on_remove: Callable,
) -> ttk.Frame:
    """Compact read-only PC summary card showing key GM stats."""
    frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
    frame.grid_columnconfigure(0, weight=1)

    ttk.Label(frame, textvariable=char.character_name, style="M.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    _card_buttons(frame, on_open, on_remove).grid(row=0, column=1, sticky="e")

    sub = ttk.Frame(frame, style="flat.TFrame")
    ttk.Label(sub, textvariable=char.player, style="HistoryMeta.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    ttk.Label(sub, textvariable=char.clan, style="HistoryMeta.TLabel").grid(
        row=0, column=1, padx=(6, 0), sticky="w"
    )
    sub.grid(row=1, column=0, columnspan=2, sticky="w")

    stats = ttk.Frame(frame, style="flat.TFrame")
    _stat_pair(stats, "Blood",    _ratio_var(char.blood_value, char.blood_max_value), row=0, col=0)
    _stat_pair(stats, "Wounds",   char.wounds_display,                                row=0, col=2)
    _stat_pair(stats, "Will",     _ratio_var(char.will_value,  char.willpower_max),   row=1, col=0)
    _stat_pair(stats, "Humanity", char.humanity_value,                                row=1, col=2)
    stats.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
    return frame


def _build_npc_card(
    parent: ttk.Frame,
    char: Character,
    *,
    on_open: Callable,
    on_remove: Callable,
    on_set_roller: Callable | None = None,
    on_quick_roll: Callable[[str, int, bool], None] | None = None,
) -> ttk.Frame:
    """Compact editable NPC summary card showing key GM stats."""
    frame = ttk.Frame(parent, style="solid.TFrame", padding=6)
    frame.grid_columnconfigure(0, weight=1)

    ttk.Label(frame, textvariable=char.character_name, style="M.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    _card_buttons(frame, on_open, on_remove, on_set_roller=on_set_roller).grid(
        row=0, column=1, sticky="e"
    )

    sub = ttk.Frame(frame, style="flat.TFrame")
    ttk.Label(sub, textvariable=char.clan,    style="HistoryMeta.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(sub, textvariable=char.concept, style="HistoryMeta.TLabel").grid(row=0, column=1, padx=(6, 0), sticky="w")
    sub.grid(row=1, column=0, columnspan=2, sticky="w")

    stats = ttk.Frame(frame, style="flat.TFrame")
    _stat_pair(stats, "Blood",  _ratio_var(char.blood_value, char.blood_max_value), row=0, col=0)
    _stat_pair(stats, "Wounds", char.wounds_display,                                row=0, col=2)
    _stat_pair(stats, "Will",   _ratio_var(char.will_value,  char.willpower_max),   row=1, col=0)
    stats.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

    if on_quick_roll:
        # (locale_key, attr1, attr2, no_botch, grid_row, grid_col, conditional_on_attr2)
        # Reuses sheet.ability_names.* keys; only "soak" needs its own key.
        # Max 2 columns so buttons fit within the card width.
        _FAST_ROLLS = [
            ("sheet.ability_names.Brawl",    "Strength",  "Brawl",    False, 0, 0, False),
            ("sheet.ability_names.Dodge",    "Dexterity", "Dodge",     False, 0, 1, False),
            ("npc_card.soak",                "Stamina",   "Fortitude", True,  1, 0, False),
            ("sheet.ability_names.Melee",    "Dexterity", "Melee",     False, 1, 1, True),
            ("sheet.ability_names.Firearms", "Dexterity", "Firearms",  False, 2, 0, True),
        ]

        btn_row = ttk.Frame(frame, style="flat.TFrame")
        btn_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        _trace_registrations: list[tuple[tk.IntVar, str]] = []

        def _make_btn(
            grow: int, gcol: int,
            locale_key: str,
            attr1: str, attr2: str,
            no_botch: bool,
            conditional: bool,
        ) -> None:
            base_pool = char.get_stat_value(attr1) + char.get_stat_value(attr2)
            if conditional and char.get_stat_value(attr2) < 1:
                return

            label_var = tk.StringVar()

            def _update(*_) -> None:
                if not frame.winfo_exists():
                    return
                effective = max(1, base_pool + char.roll_penalty.get())
                label_var.set(f"{locale.t(locale_key)} {effective}d")

            _update()
            tid = char.roll_penalty.trace_add("write", _update)
            _trace_registrations.append((char.roll_penalty, tid))
            locale.on_change(_update)

            def _click(pool=base_pool, nb=no_botch) -> None:
                effective = max(1, pool + char.roll_penalty.get())
                on_quick_roll(char.character_name.get(), effective, nb)

            ttk.Button(
                btn_row, textvariable=label_var, style="S.TButton", command=_click,
            ).grid(row=grow, column=gcol, sticky="ew", padx=(0, 3), pady=(0, 2))

        for lkey, a1, a2, nb, r, c, cond in _FAST_ROLLS:
            _make_btn(r, c, lkey, a1, a2, nb, cond)

        def _cleanup_traces(*_) -> None:
            for var, tid in _trace_registrations:
                try:
                    var.trace_remove("write", tid)
                except Exception:
                    pass

        frame.bind("<Destroy>", _cleanup_traces, add=True)

    return frame