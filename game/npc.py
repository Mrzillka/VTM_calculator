from __future__ import annotations

from tkinter import IntVar, StringVar

from config import WOUND_LEVELS


class NPC:
    """Lightweight character model for GM screen cards."""

    def __init__(
        self,
        name: str = "NPC",
        blood_max: int = 10,
        blood_current: int = 10,
        will_max: int = 5,
        will_current: int = 5,
        wounds_value: int = -1,
        dice_pool: int = 5,
        difficulty: int = 6,
        notes: str = "",
    ) -> None:
        self.character_name = StringVar(value=name)
        self.blood_max = IntVar(value=blood_max)
        self.blood_current = IntVar(value=blood_current)
        self.will_max = IntVar(value=will_max)
        self.will_current = IntVar(value=will_current)
        self.wounds_value = IntVar(value=wounds_value)
        self.wounds_display = StringVar(value=self._fmt(wounds_value))
        self.roll_penalty = IntVar(value=self._penalty(wounds_value))
        self.dice_pool = IntVar(value=dice_pool)
        self.difficulty = IntVar(value=difficulty)
        self.notes = StringVar(value=notes)
        self.last_roll_result = StringVar(value="—")

        self.wounds_value.trace_add("write", lambda *_: self._sync_wounds())

    # ── Internal ───────────────────────────────────────────────────────────────

    def _sync_wounds(self) -> None:
        level = self.wounds_value.get()
        self.wounds_display.set(self._fmt(level))
        self.roll_penalty.set(self._penalty(level))

    @staticmethod
    def _fmt(level: int) -> str:
        if level < 0:
            return "Unharmed"
        wl = WOUND_LEVELS[level]
        return f"{wl.name} ({wl.penalty:+d})" if wl.penalty else wl.name

    @staticmethod
    def _penalty(level: int) -> int:
        return 0 if level < 0 else WOUND_LEVELS[level].penalty

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_wounds(self, clicked: int) -> None:
        """Set wound level; clicking the top dot clears it."""
        filled = self.wounds_value.get() + 1  # index → dot count
        threshold = clicked if filled == clicked + 1 else clicked + 1
        self.wounds_value.set(threshold - 1)

    def heal(self) -> None:
        """Spend one blood point to remove one wound level."""
        level = self.wounds_value.get()
        if level >= 0 and self.blood_current.get() > 0:
            self.blood_current.set(self.blood_current.get() - 1)
            self.wounds_value.set(level - 1)

    # ── Persistence ────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.character_name.get(),
            "blood_max": self.blood_max.get(),
            "blood_current": self.blood_current.get(),
            "will_max": self.will_max.get(),
            "will_current": self.will_current.get(),
            "wounds_value": self.wounds_value.get(),
            "dice_pool": self.dice_pool.get(),
            "difficulty": self.difficulty.get(),
            "notes": self.notes.get(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        return cls(
            name=data.get("name", "NPC"),
            blood_max=data.get("blood_max", 10),
            blood_current=data.get("blood_current", 10),
            will_max=data.get("will_max", 5),
            will_current=data.get("will_current", 5),
            wounds_value=data.get("wounds_value", -1),
            dice_pool=data.get("dice_pool", 5),
            difficulty=data.get("difficulty", 6),
            notes=data.get("notes", ""),
        )
