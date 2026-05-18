"""Multi-step character creation wizard."""
from __future__ import annotations

from tkinter import IntVar, StringVar
from tkinter import ttk
from typing import Callable, NamedTuple

from game.character import Character
from game.chargen import AffiliationRules, CharGen
from lang import locale
from ui.base_interface import LocaleWidgetsMixin
from ui.chargen._step_mixins import (
    _ConceptMixin, _AttributesMixin, _AbilitiesMixin,
    _AdvantagesMixin, _MeritsMixin, _FreebiesMixin,
)


class StepDef(NamedTuple):
    key: str
    build: Callable[[], ttk.Frame]
    validate: Callable[[], str | None]


class Wizard(
    ttk.Frame, LocaleWidgetsMixin,
    _ConceptMixin, _AttributesMixin, _AbilitiesMixin,
    _AdvantagesMixin, _MeritsMixin, _FreebiesMixin,
):
    """Step-based character creation frame."""

    def __init__(self, parent, character: Character, on_finish=None) -> None:
        super().__init__(parent)
        self.character = character
        self._on_finish = on_finish

        # Wizard-level state
        self.affiliation: StringVar = StringVar()
        self._affil_display_var: StringVar = StringVar()
        self.rules: AffiliationRules | None = None
        self._clan_disciplines: tuple[str, ...] = ()
        self._last_flaw_bonus: int = 0
        self._last_merit_total: int = 0
        self._last_will_auto_cost: int = 0

        # Per-category remaining points (populated in _init_pools)
        _attr_cats  = list(character.attributes.keys())
        _abil_cats  = list(character.abilities.keys())
        self.attr_remaining    = {c: IntVar(value=0) for c in _attr_cats}
        self.ability_remaining = {c: IntVar(value=0) for c in _abil_cats}
        self.bg_remaining      = IntVar(value=0)
        self.disc_remaining    = IntVar(value=0)
        self.virtue_remaining  = IntVar(value=0)
        self.freebie_remaining = IntVar(value=0)

        # Priority tracking (populated in build methods)
        self._attr_priority_cats: list[str] = _attr_cats[:]
        self._attr_priority_vars: list[StringVar] = []
        self._abil_priority_cats: list[str] = _abil_cats[:]
        self._abil_priority_vars: list[StringVar] = []

        self._current_step = 0
        self._step_frames: dict[int, ttk.Frame] = {}

        self._build_chrome()
        self.grid_columnconfigure(0, weight=1)
        self._show_step(0)

    # ── Chrome (header, tutorial, content, nav) ────────────────────────────────

    def _build_chrome(self) -> None:
        # Header
        hdr = ttk.Frame(self, padding=(10, 8, 10, 4))
        hdr.grid(row=0, column=0, sticky="ew")
        self._counter_var = StringVar()
        self._title_var = StringVar()
        ttk.Label(hdr, textvariable=self._counter_var,
                  style="S.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hdr, textvariable=self._title_var,
                  style="M.TLabel").grid(row=1, column=0, sticky="w")

        ttk.Separator(self, orient="horizontal").grid(row=1, column=0, sticky="ew")

        # Tutorial
        self._tutorial_lbl = ttk.Label(
            self, text="", wraplength=500, justify="left",
            style="S.TLabel", padding=(10, 5),
        )
        self._tutorial_lbl.grid(row=2, column=0, sticky="ew")

        ttk.Separator(self, orient="horizontal").grid(row=3, column=0, sticky="ew")

        # Content area (step frames embed here)
        self._content_area = ttk.Frame(self, padding=4)
        self._content_area.grid(row=4, column=0, sticky="nsew")
        self._content_area.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, sticky="ew")

        # Navigation
        nav = ttk.Frame(self, padding=(10, 6))
        nav.grid(row=6, column=0, sticky="ew")
        self._error_var = StringVar()
        ttk.Label(nav, textvariable=self._error_var,
                  foreground="red", style="S.TLabel",
                  wraplength=400).grid(row=0, column=0, columnspan=3, sticky="w")
        self._back_btn = ttk.Button(nav, text="", command=self._go_back, style="S.TButton")
        self._back_btn.grid(row=1, column=0, sticky="w", pady=(4, 0))
        nav.grid_columnconfigure(1, weight=1)
        self._next_btn = ttk.Button(nav, text="", command=self._go_next, style="S.TButton")
        self._next_btn.grid(row=1, column=2, sticky="e", pady=(4, 0))

    # ── Step management ────────────────────────────────────────────────────────

    def _register_steps(self) -> list[StepDef]:
        return [
            StepDef("concept",      self._build_step_concept,     self._validate_concept),
            StepDef("attributes",   self._build_step_attributes,  self._validate_attributes),
            StepDef("abilities",    self._build_step_abilities,    self._validate_abilities),
            StepDef("advantages",   self._build_step_advantages,  self._validate_advantages),
            StepDef("merits_flaws", self._build_step_merits,      self._validate_merits),
            StepDef("freebies",     self._build_step_freebies,    self._validate_freebies),
        ]

    def _show_step(self, idx: int) -> None:
        steps = self._register_steps()
        total = len(steps)

        for f in self._step_frames.values():
            f.grid_remove()

        if idx not in self._step_frames:
            frame = steps[idx].build()
            frame.grid(in_=self._content_area, row=0, column=0, sticky="nsew")
            self._step_frames[idx] = frame
        else:
            self._step_frames[idx].grid()

        self._current_step = idx
        self._error_var.set("")

        step = steps[idx]
        self._counter_var.set(
            f"{locale.t('chargen.step')} {idx + 1} / {total}"
        )
        self._title_var.set(locale.t(f"chargen.steps.{step.key}"))
        self._tutorial_lbl.configure(text=locale.t(f"chargen.tutorial.{step.key}"))

        self._back_btn.configure(
            text=locale.t("chargen.btn_back"),
            state="normal" if idx > 0 else "disabled",
        )
        is_last = idx == total - 1
        self._next_btn.configure(
            text=locale.t("chargen.btn_finish" if is_last else "chargen.btn_next"),
        )

    def _go_next(self) -> None:
        steps = self._register_steps()
        err = steps[self._current_step].validate()
        if err:
            self._error_var.set(err)
            return
        self._error_var.set("")

        if self._current_step == 0:
            self._init_pools()

        if self._current_step == 3:
            self._apply_virtue_trackers()

        if self._current_step == 4:
            self._apply_flaw_bonus()

        if self._current_step == len(steps) - 1:
            self._finish()
        else:
            self._show_step(self._current_step + 1)

    def _go_back(self) -> None:
        if self._current_step > 0:
            self._error_var.set("")
            self._show_step(self._current_step - 1)

    # ── Pool initialisation (called on leaving Step 1) ─────────────────────────

    def _init_pools(self) -> None:
        self.rules = CharGen.rules_for(self.affiliation.get())
        r = self.rules

        attr_cats  = list(self.character.attributes.keys())
        abil_cats  = list(self.character.abilities.keys())

        self._attr_priority_cats = attr_cats[:]
        self._abil_priority_cats = abil_cats[:]

        # Re-sync combobox vars in case step frames are already cached
        if self._attr_priority_vars:
            for var, cat in zip(self._attr_priority_vars, attr_cats):
                var.set(locale.t(f"sheet.attr_categories.{cat}"))
        if self._abil_priority_vars:
            for var, cat in zip(self._abil_priority_vars, abil_cats):
                var.set(locale.t(f"sheet.ability_categories.{cat}"))

        for i, cat in enumerate(attr_cats):
            self.attr_remaining[cat].set(r.attr_pools[i])
        for i, cat in enumerate(abil_cats):
            self.ability_remaining[cat].set(r.ability_pools[i])

        self.bg_remaining.set(r.backgrounds)
        self.disc_remaining.set(r.disciplines)
        # 7 virtue points, but each virtue starts at 1 (3 pre-filled) → 4 remaining
        self.virtue_remaining.set(r.virtues - len(self.character.virtues))
        self.freebie_remaining.set(r.freebies)

        self._clan_disciplines = CharGen.clan_disciplines(self.character.clan.get())

        # Give each attribute its free starting dot
        for cat in self.character.attributes.values():
            for stat in cat.values():
                stat["vars"][0].set(True)
                for v in stat["vars"][1:]:
                    v.set(False)

        # Give each virtue its free starting dot (min 1)
        for virtue_row in self.character.virtues:
            virtue_row["vars"][0].set(True)
            for v in virtue_row["vars"][1:]:
                v.set(False)

    # ── Dot interaction helper (shared by all steps) ───────────────────────────

    def _wizard_dot_click(
        self,
        char_vars: list,
        clicked_idx: int,
        remaining_var: IntVar,
        min_dots: int,
        max_dots: int,
    ) -> None:
        current = sum(v.get() for v in char_vars[:max_dots])
        if current == clicked_idx + 1:
            target = current - 1  # toggle off
        else:
            target = clicked_idx + 1  # fill to clicked position

        if target < min_dots:
            return
        if target > max_dots:
            return

        delta = target - current
        if delta > 0 and remaining_var.get() < delta:
            return  # not enough points

        remaining_var.set(remaining_var.get() - delta)
        for i, v in enumerate(char_vars[:max_dots]):
            v.set(i < target)

    # ── Virtue-derived trackers (called on leaving Step 4) ────────────────────

    def _apply_virtue_trackers(self) -> None:
        """Set starting Willpower and Humanity from virtues per VTM20 rules."""
        from config import CHARGEN_MIN_WILLPOWER
        courage    = sum(v.get() for v in self.character.virtues[2]["vars"][:5])
        conscience = sum(v.get() for v in self.character.virtues[0]["vars"][:5])
        self_ctrl  = sum(v.get() for v in self.character.virtues[1]["vars"][:5])

        will_val     = max(courage, CHARGEN_MIN_WILLPOWER)
        humanity_val = conscience + self_ctrl

        self.character.will_value.set(will_val)
        self.character.set_will(load=True)
        self.character.humanity_value.set(humanity_val)
        self.character.set_humanity(load=True)

        # Dots added by the min-will rule (beyond what Courage alone provides) cost 1 freebie each
        will_auto = will_val - courage
        delta = will_auto - self._last_will_auto_cost
        if delta != 0:
            self.freebie_remaining.set(self.freebie_remaining.get() - delta)
            self._last_will_auto_cost = will_auto

    # ── Flaw bonus ─────────────────────────────────────────────────────────────

    def _apply_flaw_bonus(self) -> None:
        new_bonus = min(7, sum(r["cost"].get() for r in self.character.flaws))
        delta = new_bonus - self._last_flaw_bonus
        if delta != 0:
            self.freebie_remaining.set(self.freebie_remaining.get() + delta)
            self._last_flaw_bonus = new_bonus

    # ── Finish ─────────────────────────────────────────────────────────────────

    def _finish(self) -> None:
        self.character.save()
        if self._on_finish is not None:
            self._on_finish(self.character)
        from ui.charsheet.root import Root as CharacterSheet
        new_sheet = CharacterSheet(character=self.character)
        self.winfo_toplevel().destroy()
        new_sheet.lift()
        new_sheet.focus_force()
