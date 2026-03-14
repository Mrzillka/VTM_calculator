from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from game.npc import NPC
from ui.gm_panel.card import NPCCard

if TYPE_CHECKING:
    from ui.gm_panel.root import GMRoot


class GMInterface(ttk.Frame):
    """Scrollable grid of NPC cards."""

    COLS: int = 3

    def __init__(self, parent, root: "GMRoot") -> None:
        super().__init__(parent, padding=6)
        self.root = root
        self._cards: list[tuple[NPC, NPCCard]] = []

    def add_card(self, npc: NPC) -> None:
        card = NPCCard(
            parent=self,
            npc=npc,
            on_remove=lambda: self._remove_card(npc),
            bot=self.root.bot,
            send_to_tg=self.root.send_to_tg,
        )
        self._cards.append((npc, card))
        self._relayout()

    def _remove_card(self, npc: NPC) -> None:
        self.root.remove_npc(npc)
        for n, c in self._cards:
            if n is npc:
                c.destroy()
                break
        self._cards = [(n, c) for n, c in self._cards if n is not npc]
        self._relayout()

    def _relayout(self) -> None:
        for idx, (_, card) in enumerate(self._cards):
            row, col = divmod(idx, self.COLS)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nw")
