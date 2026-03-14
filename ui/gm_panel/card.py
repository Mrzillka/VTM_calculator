from __future__ import annotations

from tkinter import BooleanVar, ttk
from typing import TYPE_CHECKING, Callable

from config import WOUND_LEVELS
from game.npc import NPC
from game.roller import Roller

if TYPE_CHECKING:
    from bot.tg_bot import TgBot


class NPCCard(ttk.Frame):
    """Compact stat card for a single NPC or player character."""

    def __init__(
        self,
        parent,
        npc: NPC,
        on_remove: Callable[[], None],
        bot: "TgBot | None" = None,
        send_to_tg: BooleanVar | None = None,
    ) -> None:
        super().__init__(parent, relief="solid", borderwidth=1, padding=5)
        self.npc = npc
        self._on_remove = on_remove
        self._bot = bot
        self._send_to_tg = send_to_tg
        self._blood_dots: list[ttk.Label] = []
        self._wound_dots: list[ttk.Label] = []
        self._will_dots: list[ttk.Label] = []
        self._last_roll_msg: str = ""
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=3)
        self._build_blood_row()
        self._build_wounds_row()
        self._build_will_row()
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=3)
        self._build_roll()
        self._build_notes()

    def _build_header(self) -> None:
        frm = ttk.Frame(self)
        frm.pack(fill="x")
        ttk.Entry(frm, textvariable=self.npc.character_name,
                  width=18, style="card.TEntry").pack(side="left", expand=True, fill="x")
        ttk.Button(frm, text="✕", width=2, style="card.S.TButton",
                   command=self._on_remove).pack(side="right")

    # ── Blood ───────────────────────────────────────────────────────────────────

    def _build_blood_row(self) -> None:
        frm = ttk.Frame(self)
        frm.pack(fill="x", pady=1)

        ttk.Label(frm, text="♥", style="card.S.TLabel", width=2).pack(side="left")

        dots_frm = ttk.Frame(frm)
        dots_frm.pack(side="left")
        for i in range(10):
            lbl = ttk.Label(dots_frm, text="○", style="card.Dot.TLabel", cursor="hand2")
            lbl.grid(row=0, column=i)
            lbl.bind("<Button-1>", lambda e, idx=i: self._click_blood(idx))
            self._blood_dots.append(lbl)

        ttk.Label(frm, textvariable=self.npc.blood_current,
                  style="card.S.TLabel", width=2).pack(side="left", padx=(4, 0))
        ttk.Label(frm, text="/", style="card.S.TLabel").pack(side="left")
        ttk.Spinbox(frm, from_=1, to=40, textvariable=self.npc.blood_max,
                    width=3, style="card.TSpinbox").pack(side="left")
        ttk.Button(frm, text="+", width=2, style="card.S.TButton",
                   command=lambda: self._step_blood(1)).pack(side="left", padx=(4, 0))
        ttk.Button(frm, text="−", width=2, style="card.S.TButton",
                   command=lambda: self._step_blood(-1)).pack(side="left")

        self.npc.blood_current.trace_add("write", lambda *_: self._refresh_blood())
        self.npc.blood_max.trace_add("write", lambda *_: self._refresh_blood())
        self._refresh_blood()

    def _click_blood(self, idx: int) -> None:
        cur = self.npc.blood_current.get()
        mx = self.npc.blood_max.get()
        self.npc.blood_current.set(min(idx if cur == idx + 1 else idx + 1, mx))

    def _step_blood(self, delta: int) -> None:
        cur = self.npc.blood_current.get()
        self.npc.blood_current.set(max(0, min(cur + delta, self.npc.blood_max.get())))

    def _refresh_blood(self) -> None:
        cur = self.npc.blood_current.get()
        mx = self.npc.blood_max.get()
        if cur > mx:
            self.npc.blood_current.set(mx)
            return
        for i, lbl in enumerate(self._blood_dots):
            if i >= mx:
                lbl.configure(text="·", foreground="gray", cursor="")
                lbl.unbind("<Button-1>")
            elif i < cur:
                lbl.configure(text="●", foreground="", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, idx=i: self._click_blood(idx))
            else:
                lbl.configure(text="○", foreground="", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, idx=i: self._click_blood(idx))

    # ── Wounds ──────────────────────────────────────────────────────────────────

    def _build_wounds_row(self) -> None:
        frm = ttk.Frame(self)
        frm.pack(fill="x", pady=1)

        ttk.Label(frm, text="✚", style="card.S.TLabel", width=2).pack(side="left")
        ttk.Label(frm, textvariable=self.npc.wounds_display,
                  style="card.S.TLabel", width=16, anchor="w").pack(side="left")

        dots_frm = ttk.Frame(frm)
        dots_frm.pack(side="left")
        for i in range(len(WOUND_LEVELS)):
            lbl = ttk.Label(dots_frm, text="○", style="card.Dot.TLabel", cursor="hand2")
            lbl.grid(row=0, column=i)
            lbl.bind("<Button-1>", lambda e, idx=i: self.npc.set_wounds(idx))
            self._wound_dots.append(lbl)

        ttk.Button(frm, text="Heal", style="card.S.TButton",
                   command=self.npc.heal).pack(side="right")

        self.npc.wounds_value.trace_add("write", lambda *_: self._refresh_wounds())
        self._refresh_wounds()

    def _refresh_wounds(self) -> None:
        level = self.npc.wounds_value.get()
        for i, lbl in enumerate(self._wound_dots):
            lbl.configure(text="●" if i <= level else "○")

    # ── Willpower ───────────────────────────────────────────────────────────────

    def _build_will_row(self) -> None:
        frm = ttk.Frame(self)
        frm.pack(fill="x", pady=1)

        ttk.Label(frm, text="✦", style="card.S.TLabel", width=2).pack(side="left")

        dots_frm = ttk.Frame(frm)
        dots_frm.pack(side="left")
        for i in range(10):
            lbl = ttk.Label(dots_frm, text="○", style="card.Dot.TLabel", cursor="hand2")
            lbl.grid(row=0, column=i)
            lbl.bind("<Button-1>", lambda e, idx=i: self._click_will(idx))
            self._will_dots.append(lbl)

        ttk.Label(frm, textvariable=self.npc.will_current,
                  style="card.S.TLabel", width=2).pack(side="left", padx=(4, 0))
        ttk.Label(frm, text="/", style="card.S.TLabel").pack(side="left")
        ttk.Spinbox(frm, from_=1, to=10, textvariable=self.npc.will_max,
                    width=3, style="card.TSpinbox").pack(side="left")

        self.npc.will_current.trace_add("write", lambda *_: self._refresh_will())
        self.npc.will_max.trace_add("write", lambda *_: self._refresh_will())
        self._refresh_will()

    def _click_will(self, idx: int) -> None:
        cur = self.npc.will_current.get()
        mx = self.npc.will_max.get()
        if idx >= mx:
            return
        self.npc.will_current.set(min(idx if cur == idx + 1 else idx + 1, mx))

    def _refresh_will(self) -> None:
        cur = self.npc.will_current.get()
        mx = self.npc.will_max.get()
        if cur > mx:
            self.npc.will_current.set(mx)
            return
        for i, lbl in enumerate(self._will_dots):
            if i >= mx:
                lbl.configure(text="·", foreground="gray", cursor="")
                lbl.unbind("<Button-1>")
            elif i < cur:
                lbl.configure(text="●", foreground="", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, idx=i: self._click_will(idx))
            else:
                lbl.configure(text="○", foreground="", cursor="hand2")
                lbl.bind("<Button-1>", lambda e, idx=i: self._click_will(idx))

    # ── Roll ────────────────────────────────────────────────────────────────────

    def _build_roll(self) -> None:
        roll_frm = ttk.Frame(self)
        roll_frm.pack(fill="x", pady=1)

        ttk.Label(roll_frm, text="🎲", style="card.S.TLabel").pack(side="left")
        ttk.Spinbox(roll_frm, from_=1, to=30, textvariable=self.npc.dice_pool,
                    width=3, style="card.TSpinbox").pack(side="left", padx=(2, 0))
        ttk.Label(roll_frm, text="D:", style="card.S.TLabel").pack(side="left", padx=(4, 0))
        ttk.Spinbox(roll_frm, from_=2, to=10, textvariable=self.npc.difficulty,
                    width=3, style="card.TSpinbox").pack(side="left", padx=(2, 0))
        ttk.Button(roll_frm, text="Roll!", style="card.M.TButton",
                   command=self._do_roll).pack(side="left", padx=(6, 0))

        res_frm = ttk.Frame(self)
        res_frm.pack(fill="x", pady=1)
        ttk.Label(res_frm, textvariable=self.npc.last_roll_result,
                  style="card.S.TLabel", anchor="w").pack(side="left")
        ttk.Button(res_frm, text="📤", width=3, style="card.S.TButton",
                   command=self._send_tg).pack(side="right")

    def _do_roll(self) -> None:
        roller = Roller(
            dice_number=self.npc.dice_pool.get(),
            difficulty=self.npc.difficulty.get(),
            penalty=self.npc.roll_penalty.get(),
        )
        result = roller.roll()
        dice_str = ", ".join(map(str, result.all_dice))
        self.npc.last_roll_result.set(
            f"{result.outcome}  {result.successes:+d}  [{dice_str}]"
        )
        self._last_roll_msg = (
            f"<b><i>{self.npc.character_name.get()}</i> rolled:</b>\n"
            f"<i>{dice_str}</i>\n"
            f"on <b>{self.npc.dice_pool.get()} dice</b> "
            f"with <b>difficulty {self.npc.difficulty.get()}</b>.\n"
            f"<b>It's a {result.outcome}!</b>\n"
            f"<b><u>Net successes: {result.successes}</u></b>\n"
            f"        Wounds penalty: {self.npc.roll_penalty.get()} die(s)"
        )
        if self._send_to_tg and self._send_to_tg.get():
            self._send_tg()

    def _send_tg(self) -> None:
        if self._bot and self._bot.chat_id and self._last_roll_msg:
            self._bot.send_async(self._last_roll_msg)

    # ── Notes ───────────────────────────────────────────────────────────────────

    def _build_notes(self) -> None:
        ttk.Entry(self, textvariable=self.npc.notes,
                  width=30, style="card.TEntry").pack(fill="x", pady=(4, 0))
