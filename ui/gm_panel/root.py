from __future__ import annotations

import json
import logging
import tkinter as tk
from tkinter import BooleanVar, Toplevel, ttk
from typing import TYPE_CHECKING

from config import FONT, NPC_FILE_PATH
from game.npc import NPC
from ui.gm_panel.interface import GMInterface

if TYPE_CHECKING:
    from bot.tg_bot import TgBot

logger = logging.getLogger(__name__)


class GMRoot(Toplevel):
    """GM screen window: tracks all NPC and player cards in one place."""

    def __init__(self, parent=None, bot: "TgBot | None" = None) -> None:
        super().__init__(parent)
        self.title("GM Screen")
        self.geometry("1100x700")
        self.minsize(600, 400)
        self.resizable(True, True)

        self.bot = bot
        self.send_to_tg = BooleanVar(value=False)
        self.npcs: list[NPC] = []

        self._configure_styles()
        self._build()
        self._load()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _configure_styles(self) -> None:
        s = ttk.Style()
        defs = {
            "card.TEntry":     {"font": (FONT, 10)},
            "card.TSpinbox":   {"font": (FONT, 10)},
            "card.S.TButton":  {"font": (FONT, 9)},
            "card.M.TButton":  {"font": (FONT, 11, "bold")},
            "card.S.TLabel":   {"font": (FONT, 10)},
            "card.Dot.TLabel": {"font": (FONT, 10)},
        }
        for name, opts in defs.items():
            s.configure(name, **opts)

    def _build(self) -> None:
        self._build_toolbar()
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=6, pady=(0, 4))
        self._build_scrollable_area()

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(fill="x")

        ttk.Button(bar, text="+ Add NPC", style="card.S.TButton",
                   command=self.add_npc).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="💾 Save", style="card.S.TButton",
                   command=self.save).pack(side="left", padx=(0, 12))

        tg_dot = ttk.Label(bar, text="○", style="card.Dot.TLabel", cursor="hand2")
        tg_lbl = ttk.Label(bar, text="Send to Telegram", style="card.S.TLabel", cursor="hand2")

        def _toggle(e=None) -> None:
            self.send_to_tg.set(not self.send_to_tg.get())

        self.send_to_tg.trace_add(
            "write",
            lambda *_: tg_dot.configure(text="●" if self.send_to_tg.get() else "○"),
        )
        tg_dot.bind("<Button-1>", _toggle)
        tg_lbl.bind("<Button-1>", _toggle)
        tg_dot.pack(side="left")
        tg_lbl.pack(side="left", padx=(2, 0))

    def _build_scrollable_area(self) -> None:
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(win_id, width=e.width),
        )
        self._setup_mousewheel(canvas)

        self._interface = GMInterface(inner, self)
        self._interface.pack(fill="both", expand=True)

    def _setup_mousewheel(self, canvas: tk.Canvas) -> None:
        def _scroll(e: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def _bind(e: tk.Event = None) -> None:
            self.bind_all("<MouseWheel>", _scroll)
            self.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            self.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def _unbind(e: tk.Event = None) -> None:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")

        self.bind("<Enter>", _bind)
        self.bind("<Leave>", _unbind)

    # ── NPC management ─────────────────────────────────────────────────────────

    def add_npc(self, npc: NPC | None = None) -> None:
        """Add an NPC card; creates a default NPC if none provided."""
        if npc is None:
            npc = NPC(name=f"NPC {len(self.npcs) + 1}")
        self.npcs.append(npc)
        self._interface.add_card(npc)

    def remove_npc(self, npc: NPC) -> None:
        if npc in self.npcs:
            self.npcs.remove(npc)

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self) -> None:
        with open(NPC_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([npc.to_dict() for npc in self.npcs], f, indent=2, ensure_ascii=False)

    def _load(self) -> None:
        if not NPC_FILE_PATH.exists():
            return
        try:
            with open(NPC_FILE_PATH, encoding="utf-8") as f:
                for entry in json.load(f):
                    self.add_npc(NPC.from_dict(entry))
        except Exception:
            logger.exception("Failed to load NPC data from %s", NPC_FILE_PATH)

    def _on_close(self) -> None:
        self.save()
        self.destroy()
