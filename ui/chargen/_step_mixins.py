"""Step frame builders and validators for the character-creation wizard."""
from __future__ import annotations

from tkinter import IntVar, StringVar
from tkinter import ttk
from typing import TYPE_CHECKING

from config import BACKGROUNDS, DISCIPLINES, FLAWS, MERITS
from game.character import ATTRIBUTES, ABILITIES
from lang import locale
from ui.constants import MOUSEWHEEL_DIVISOR

if TYPE_CHECKING:
    from ui.chargen.wizard import Wizard


# ── Helper shared by mixins ────────────────────────────────────────────────────

def _remaining_label(parent: ttk.Frame, var: IntVar) -> ttk.Label:
    lbl = ttk.Label(parent, textvariable=var, style="S.TLabel", width=3)
    var.trace_add("write", lambda *_: _color_remaining(lbl, var))
    _color_remaining(lbl, var)
    return lbl


def _color_remaining(lbl: ttk.Label, var: IntVar) -> None:
    try:
        lbl.configure(foreground="red" if var.get() < 0 else "")
    except Exception:
        pass


# ── Step 1: Concept ───────────────────────────────────────────────────────────

class _ConceptMixin:

    def _build_step_concept(self: "Wizard") -> ttk.Frame:
        from game.chargen import AFFILIATIONS, ARCHETYPES, CLANS, GENERATION_CHOICES
        frm = ttk.Frame(self._content_area, padding=8)

        fields: list[tuple[str, ttk.Widget]] = []

        name_entry = ttk.Entry(frm, textvariable=self.character.character_name,
                               width=28, style="my.TEntry")
        fields.append(("chargen.labels.name", name_entry))

        clan_cb = ttk.Combobox(frm, textvariable=self.character.clan,
                               values=list(CLANS), state="readonly", width=26)
        fields.append(("chargen.labels.clan", clan_cb))

        nature_cb = ttk.Combobox(frm, textvariable=self.character.nature,
                                 values=list(ARCHETYPES), state="readonly", width=26)
        fields.append(("chargen.labels.nature", nature_cb))

        demeanor_cb = ttk.Combobox(frm, textvariable=self.character.demeanor,
                                   values=list(ARCHETYPES), state="readonly", width=26)
        fields.append(("chargen.labels.demeanor", demeanor_cb))

        affil_values = [locale.t(f"chargen.affiliations.{k}") for k in AFFILIATIONS.keys()]
        affil_cb = ttk.Combobox(frm, textvariable=self._affil_display_var,
                                values=affil_values, state="readonly", width=26)

        def _on_affil_sel(e) -> None:
            self.affiliation.set(
                locale.reverse_lookup_en("chargen.affiliations", self._affil_display_var.get())
            )
        affil_cb.bind("<<ComboboxSelected>>", _on_affil_sel)
        fields.append(("chargen.labels.affiliation", affil_cb))

        gen_cb = ttk.Combobox(frm, textvariable=self.character.generation,
                              values=list(GENERATION_CHOICES), state="readonly", width=26)
        fields.append(("chargen.labels.generation", gen_cb))

        for row, (key, widget) in enumerate(fields):
            lbl = ttk.Label(frm, text=locale.t(key), width=18, anchor="e", style="S.TLabel")
            locale.register(lbl, key)
            lbl.grid(row=row, column=0, padx=(0, 6), pady=3, sticky="e")
            widget.grid(row=row, column=1, pady=3, sticky="w")

        return frm

    def _validate_concept(self: "Wizard") -> str | None:
        if not self.character.character_name.get().strip():
            return locale.t("chargen.errors.name_required")
        if not self.character.clan.get():
            return locale.t("chargen.errors.clan_required")
        if not self.affiliation.get():
            return locale.t("chargen.errors.affiliation_required")
        return None


# ── Step 2: Attributes ────────────────────────────────────────────────────────

class _AttributesMixin:

    def _build_step_attributes(self: "Wizard") -> ttk.Frame:
        frm = ttk.Frame(self._content_area, padding=4)

        # ── Priority selection ─────────────────────────────────────────────────
        pri_frm = ttk.Frame(frm)
        pri_frm.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        cats = list(self.character.attributes.keys())
        translated_cats = [locale.t(f"sheet.attr_categories.{c}") for c in cats]
        # _attr_priority_cats[i] = which category has priority i (0=Primary, etc.) — English keys
        self._attr_priority_cats = cats[:]

        self._attr_priority_vars: list[StringVar] = [StringVar(value=tc) for tc in translated_cats]

        pri_labels = [locale.t("chargen.labels.primary"),
                      locale.t("chargen.labels.secondary"),
                      locale.t("chargen.labels.tertiary")]

        for col, (var, plabel) in enumerate(zip(self._attr_priority_vars, pri_labels)):
            ttk.Label(pri_frm, text=plabel, style="S.TLabel").grid(row=0, column=col, padx=8)
            cb = ttk.Combobox(pri_frm, textvariable=var, values=translated_cats,
                              state="readonly", width=10)
            cb.grid(row=1, column=col, padx=8)
            cb.bind("<<ComboboxSelected>>",
                    lambda e, idx=col: self._on_attr_priority_change(idx))

        # ── Attribute dot rows ─────────────────────────────────────────────────
        for row_offset, (cat, attrs) in enumerate(self.character.attributes.items()):
            cat_frm = ttk.Frame(frm, padding=4)
            cat_frm.grid(row=row_offset + 1, column=0, sticky="ew", padx=4, pady=2)
            cat_frm.grid_columnconfigure(0, weight=1)

            cat_lbl = ttk.Label(cat_frm, text=locale.t(f"sheet.attr_categories.{cat}"),
                                style="M.TLabel")
            cat_lbl.grid(row=0, column=0, columnspan=6, pady=(0, 2))

            rem_frm = ttk.Frame(cat_frm)
            rem_frm.grid(row=1, column=0, columnspan=6, pady=(0, 4))
            rem_lbl = ttk.Label(rem_frm, text=locale.t("chargen.labels.remaining") + ":",
                                style="S.TLabel")
            rem_lbl.grid(row=0, column=0)
            locale.register(rem_lbl, "chargen.labels.remaining_prefix")
            _remaining_label(rem_frm, self.attr_remaining[cat]).grid(row=0, column=1, padx=(2, 0))

            for a_row, (attr_name, stat) in enumerate(attrs.items(), start=2):
                name_lbl = ttk.Label(cat_frm,
                                     text=locale.t(f"sheet.attr_names.{attr_name}"),
                                     width=12, anchor="e", style="S.TLabel")
                name_lbl.grid(row=a_row, column=0, sticky="e", padx=(0, 4))
                self._build_attr_dots(cat_frm, a_row, stat["vars"],
                                      self.attr_remaining[cat], min_dots=1)

        return frm

    def _build_attr_dots(self: "Wizard", parent, row, char_vars, remaining_var, min_dots=0):
        for col, var in enumerate(char_vars[:5]):
            dot = ttk.Label(parent, text="●" if var.get() else "○",
                            width=2, style="S.TLabel", cursor="hand2")
            var.trace_add("write",
                          lambda *_, l=dot, v=var: l.configure(text="●" if v.get() else "○"))
            dot.bind("<Button-1>",
                     lambda e, idx=col, cv=char_vars, rv=remaining_var, md=min_dots:
                     self._wizard_dot_click(cv, idx, rv, md, 5))
            dot.grid(row=row, column=col + 1)

    def _on_attr_priority_change(self: "Wizard", changed_slot: int) -> None:
        new_cat = locale.reverse_lookup_en("sheet.attr_categories",
                                           self._attr_priority_vars[changed_slot].get())
        old_cat = self._attr_priority_cats[changed_slot]
        if new_cat == old_cat:
            return
        old_slot = self._attr_priority_cats.index(new_cat)

        # Swap
        self._attr_priority_cats[changed_slot] = new_cat
        self._attr_priority_cats[old_slot] = old_cat
        self._attr_priority_vars[old_slot].set(locale.t(f"sheet.attr_categories.{old_cat}"))

        r = self.rules
        for slot in (changed_slot, old_slot):
            cat = self._attr_priority_cats[slot]
            pool = r.attr_pools[slot]
            n_attrs = len(self.character.attributes[cat])
            spent = sum(
                sum(v.get() for v in stat["vars"][:5])
                for stat in self.character.attributes[cat].values()
            ) - n_attrs  # subtract 1 minimum per attribute
            self.attr_remaining[cat].set(pool - max(0, spent))

    def _validate_attributes(self: "Wizard") -> str | None:
        total = sum(v.get() for v in self.attr_remaining.values())
        if total != 0:
            return locale.t("chargen.errors.attr_points_remaining").format(n=total)
        return None


# ── Step 3: Abilities ─────────────────────────────────────────────────────────

class _AbilitiesMixin:

    def _build_step_abilities(self: "Wizard") -> ttk.Frame:
        frm = ttk.Frame(self._content_area, padding=4)

        cats = list(self.character.abilities.keys())
        translated_cats = [locale.t(f"sheet.ability_categories.{c}") for c in cats]
        self._abil_priority_cats = cats[:]
        self._abil_priority_vars: list[StringVar] = [StringVar(value=tc) for tc in translated_cats]

        # Priority selection row
        pri_frm = ttk.Frame(frm)
        pri_frm.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        pri_labels = [locale.t("chargen.labels.primary"),
                      locale.t("chargen.labels.secondary"),
                      locale.t("chargen.labels.tertiary")]
        for col, (var, plabel) in enumerate(zip(self._abil_priority_vars, pri_labels)):
            ttk.Label(pri_frm, text=plabel, style="S.TLabel").grid(row=0, column=col, padx=8)
            cb = ttk.Combobox(pri_frm, textvariable=var, values=translated_cats,
                              state="readonly", width=12)
            cb.grid(row=1, column=col, padx=8)
            cb.bind("<<ComboboxSelected>>",
                    lambda e, idx=col: self._on_abil_priority_change(idx))

        # Notebook for categories
        nb = ttk.Notebook(frm)
        nb.grid(row=1, column=0, sticky="nsew")
        frm.grid_rowconfigure(1, weight=1)

        for cat, abilities in self.character.abilities.items():
            tab = ttk.Frame(nb, padding=4)
            nb.add(tab, text=locale.t(f"sheet.ability_categories.{cat}"))

            rem_frm = ttk.Frame(tab)
            rem_frm.grid(row=0, column=0, columnspan=6, pady=(0, 4))
            rem_lbl = ttk.Label(rem_frm, text=locale.t("chargen.labels.remaining") + ":",
                                style="S.TLabel")
            rem_lbl.grid(row=0, column=0)
            _remaining_label(rem_frm, self.ability_remaining[cat]).grid(row=0, column=1, padx=(2, 0))

            for a_row, (abil_name, stat) in enumerate(abilities.items(), start=1):
                name_lbl = ttk.Label(tab, text=locale.t(f"sheet.ability_names.{abil_name}"),
                                     width=14, anchor="e", style="S.TLabel")
                name_lbl.grid(row=a_row, column=0, sticky="e", padx=(0, 4), pady=1)
                self._build_abil_dots(tab, a_row, stat["vars"],
                                      self.ability_remaining[cat])

        return frm

    def _build_abil_dots(self: "Wizard", parent, row, char_vars, remaining_var):
        for col, var in enumerate(char_vars[:3]):
            dot = ttk.Label(parent, text="●" if var.get() else "○",
                            width=2, style="S.TLabel", cursor="hand2")
            var.trace_add("write",
                          lambda *_, l=dot, v=var: l.configure(text="●" if v.get() else "○"))
            dot.bind("<Button-1>",
                     lambda e, idx=col, cv=char_vars, rv=remaining_var:
                     self._wizard_dot_click(cv, idx, rv, 0, 3))
            dot.grid(row=row, column=col + 1)

    def _on_abil_priority_change(self: "Wizard", changed_slot: int) -> None:
        new_cat = locale.reverse_lookup_en("sheet.ability_categories",
                                           self._abil_priority_vars[changed_slot].get())
        old_cat = self._abil_priority_cats[changed_slot]
        if new_cat == old_cat:
            return
        old_slot = self._abil_priority_cats.index(new_cat)

        self._abil_priority_cats[changed_slot] = new_cat
        self._abil_priority_cats[old_slot] = old_cat
        self._abil_priority_vars[old_slot].set(locale.t(f"sheet.ability_categories.{old_cat}"))

        r = self.rules
        for slot in (changed_slot, old_slot):
            cat = self._abil_priority_cats[slot]
            pool = r.ability_pools[slot]
            spent = sum(
                sum(v.get() for v in stat["vars"][:3])
                for stat in self.character.abilities[cat].values()
            )
            self.ability_remaining[cat].set(pool - spent)

    def _validate_abilities(self: "Wizard") -> str | None:
        total = sum(v.get() for v in self.ability_remaining.values())
        if total != 0:
            return locale.t("chargen.errors.ability_points_remaining").format(n=total)
        return None


# ── Step 4: Advantages ────────────────────────────────────────────────────────

class _AdvantagesMixin:

    def _build_step_advantages(self: "Wizard") -> ttk.Frame:
        frm = ttk.Frame(self._content_area, padding=4)

        nb = ttk.Notebook(frm)
        nb.pack(fill="both", expand=True)

        nb.add(self._build_backgrounds_tab(nb), text=locale.t("sheet.adv_columns.Backgrounds"))
        nb.add(self._build_disciplines_tab(nb), text=locale.t("sheet.adv_columns.Disciplines"))
        nb.add(self._build_virtues_tab(nb),     text=locale.t("sheet.adv_columns.Virtues"))

        return frm

    def _build_backgrounds_tab(self: "Wizard", parent) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=4)

        rem_frm = ttk.Frame(tab)
        rem_frm.grid(row=0, column=0, columnspan=7, pady=(0, 4))
        rem_lbl = ttk.Label(rem_frm, text=locale.t("chargen.labels.remaining") + ":",
                            style="S.TLabel")
        rem_lbl.grid(row=0, column=0)
        _remaining_label(rem_frm, self.bg_remaining).grid(row=0, column=1, padx=(2, 0))

        bg_names = [""] + list(BACKGROUNDS)
        for row_idx, bg_row in enumerate(self.character.backgrounds[:7], start=1):
            cb = ttk.Combobox(tab, textvariable=bg_row["name"],
                              values=bg_names, width=16)
            cb.grid(row=row_idx, column=0, padx=(0, 4), pady=1)
            for col, var in enumerate(bg_row["vars"][:5]):
                dot = ttk.Label(tab, text="●" if var.get() else "○",
                                width=2, style="S.TLabel", cursor="hand2")
                var.trace_add("write",
                              lambda *_, l=dot, v=var: l.configure(
                                  text="●" if v.get() else "○"))
                dot.bind("<Button-1>",
                         lambda e, idx=col, cv=bg_row["vars"], rv=self.bg_remaining:
                         self._wizard_dot_click(cv, idx, rv, 0, 5))
                dot.grid(row=row_idx, column=col + 1)

        return tab

    def _build_disciplines_tab(self: "Wizard", parent) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=4)

        rem_frm = ttk.Frame(tab)
        rem_frm.grid(row=0, column=0, columnspan=7, pady=(0, 4))
        rem_lbl = ttk.Label(rem_frm, text=locale.t("chargen.labels.remaining") + ":",
                            style="S.TLabel")
        rem_lbl.grid(row=0, column=0)
        _remaining_label(rem_frm, self.disc_remaining).grid(row=0, column=1, padx=(2, 0))

        disc_names = [""] + list(DISCIPLINES)

        for row_idx, disc_row in enumerate(self.character.disciplines[:7], start=1):
            # Pre-populate clan disciplines
            if row_idx - 1 < len(self._clan_disciplines):
                clan_disc = self._clan_disciplines[row_idx - 1]
                if not disc_row["name"].get():
                    disc_row["name"].set(clan_disc)

            cb = ttk.Combobox(tab, textvariable=disc_row["name"],
                              values=disc_names, width=16)
            cb.grid(row=row_idx, column=0, padx=(0, 4), pady=1)
            for col, var in enumerate(disc_row["vars"][:3]):
                dot = ttk.Label(tab, text="●" if var.get() else "○",
                                width=2, style="S.TLabel", cursor="hand2")
                var.trace_add("write",
                              lambda *_, l=dot, v=var: l.configure(
                                  text="●" if v.get() else "○"))
                dot.bind("<Button-1>",
                         lambda e, idx=col, cv=disc_row["vars"], rv=self.disc_remaining:
                         self._wizard_dot_click(cv, idx, rv, 0, 3))
                dot.grid(row=row_idx, column=col + 1)

        return tab

    def _build_virtues_tab(self: "Wizard", parent) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=4)

        rem_frm = ttk.Frame(tab)
        rem_frm.grid(row=0, column=0, columnspan=7, pady=(0, 4))
        rem_lbl = ttk.Label(rem_frm, text=locale.t("chargen.labels.remaining") + ":",
                            style="S.TLabel")
        rem_lbl.grid(row=0, column=0)
        _remaining_label(rem_frm, self.virtue_remaining).grid(row=0, column=1, padx=(2, 0))

        for row_idx, virtue_row in enumerate(self.character.virtues, start=1):
            name_lbl = ttk.Label(tab, text=virtue_row["name"].get(),
                                 width=22, anchor="e", style="S.TLabel")
            name_lbl.grid(row=row_idx, column=0, padx=(0, 4), pady=2)
            for col, var in enumerate(virtue_row["vars"][:5]):
                dot = ttk.Label(tab, text="●" if var.get() else "○",
                                width=2, style="S.TLabel", cursor="hand2")
                var.trace_add("write",
                              lambda *_, l=dot, v=var: l.configure(
                                  text="●" if v.get() else "○"))
                dot.bind("<Button-1>",
                         lambda e, idx=col, cv=virtue_row["vars"], rv=self.virtue_remaining:
                         self._wizard_dot_click(cv, idx, rv, 1, 5))
                dot.grid(row=row_idx, column=col + 1)

        return tab

    def _validate_advantages(self: "Wizard") -> str | None:
        remaining_vars = [self.bg_remaining, self.disc_remaining, self.virtue_remaining]
        if any(v.get() != 0 for v in remaining_vars):
            return locale.t("chargen.errors.adv_points_remaining")
        return None


# ── Step 5: Merits & Flaws ────────────────────────────────────────────────────

class _MeritsMixin:

    def _build_step_merits(self: "Wizard") -> ttk.Frame:
        frm = ttk.Frame(self._content_area, padding=4)

        merit_names = [""] + sorted(MERITS.keys())
        flaw_names  = [""] + sorted(FLAWS.keys())

        # Totals
        merit_total_var = StringVar(value="0")
        flaw_total_var  = StringVar(value="0")

        def _update_totals(*_) -> None:
            m = sum(r["cost"].get() for r in self.character.merits)
            f = sum(r["cost"].get() for r in self.character.flaws)
            merit_total_var.set(str(m))
            flaw_total_var.set(str(f))
            delta = m - self._last_merit_total
            if delta != 0:
                self.freebie_remaining.set(self.freebie_remaining.get() - delta)
                self._last_merit_total = m

        # Headers
        ttk.Label(frm, text=locale.t("sheet.mf.merits"),
                  style="M.TLabel").grid(row=0, column=0, columnspan=2, padx=8)
        ttk.Label(frm, text=locale.t("sheet.mf.flaws"),
                  style="M.TLabel").grid(row=0, column=3, columnspan=2, padx=8)

        # Merit rows
        for row_idx, merit_row in enumerate(self.character.merits, start=1):
            cb = ttk.Combobox(frm, textvariable=merit_row["name"],
                              values=merit_names, width=18)
            cb.grid(row=row_idx, column=0, padx=(4, 2), pady=1)

            cost_sb = ttk.Spinbox(frm, from_=0, to=7, textvariable=merit_row["cost"], width=4)
            cost_sb.grid(row=row_idx, column=1, padx=(0, 8))

            def _on_merit_sel(event, row=merit_row) -> None:
                name = row["name"].get()
                row["cost"].set(MERITS.get(name, 0))
                _update_totals()

            cb.bind("<<ComboboxSelected>>", _on_merit_sel)
            merit_row["cost"].trace_add("write", _update_totals)

        # Flaw rows
        for row_idx, flaw_row in enumerate(self.character.flaws, start=1):
            cb = ttk.Combobox(frm, textvariable=flaw_row["name"],
                              values=flaw_names, width=18)
            cb.grid(row=row_idx, column=3, padx=(8, 2), pady=1)

            cost_sb = ttk.Spinbox(frm, from_=0, to=7, textvariable=flaw_row["cost"], width=4)
            cost_sb.grid(row=row_idx, column=4, padx=(0, 4))

            def _on_flaw_sel(event, row=flaw_row) -> None:
                name = row["name"].get()
                row["cost"].set(FLAWS.get(name, 0))
                _update_totals()

            cb.bind("<<ComboboxSelected>>", _on_flaw_sel)
            flaw_row["cost"].trace_add("write", _update_totals)

        # Totals row
        total_row = len(self.character.merits) + 1
        ttk.Separator(frm, orient="vertical").grid(row=1, column=2,
                                                    rowspan=total_row, sticky="ns", padx=4)
        ttk.Label(frm, text=locale.t("sheet.mf.pts"),
                  style="S.TLabel").grid(row=total_row, column=1)
        ttk.Label(frm, textvariable=merit_total_var,
                  style="S.TLabel").grid(row=total_row, column=0)
        ttk.Label(frm, textvariable=flaw_total_var,
                  style="S.TLabel").grid(row=total_row, column=3)
        ttk.Label(frm, text=locale.t("sheet.mf.pts"),
                  style="S.TLabel").grid(row=total_row, column=4)

        return frm

    def _validate_merits(self: "Wizard") -> str | None:
        flaw_total = sum(r["cost"].get() for r in self.character.flaws)
        if flaw_total > 7:
            return locale.t("chargen.errors.flaw_max")
        return None


# ── Step 6: Freebie Points ────────────────────────────────────────────────────

class _FreebiesMixin:

    def _build_step_freebies(self: "Wizard") -> ttk.Frame:
        frm = ttk.Frame(self._content_area, padding=4)

        rem_frm = ttk.Frame(frm)
        rem_frm.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        rem_lbl = ttk.Label(rem_frm, text=locale.t("chargen.labels.freebie_remaining") + ":",
                            style="M.TLabel")
        rem_lbl.grid(row=0, column=0)
        locale.register(rem_lbl, "chargen.labels.freebie_remaining_prefix")
        _remaining_label(rem_frm, self.freebie_remaining).grid(row=0, column=1, padx=(4, 0))

        nb = ttk.Notebook(frm)
        nb.grid(row=1, column=0, sticky="nsew")
        frm.grid_rowconfigure(1, weight=1)

        nb.add(self._build_freebies_attrs_tab(nb),      text=locale.t("sheet.sections.attributes"))
        nb.add(self._build_freebies_abils_tab(nb),      text=locale.t("sheet.sections.abilities"))
        nb.add(self._build_freebies_advantages_tab(nb), text=locale.t("sheet.sections.advantages"))
        nb.add(self._build_freebies_trackers_tab(nb),   text=locale.t("chargen.labels.trackers"))

        return frm

    def _build_freebies_attrs_tab(self: "Wizard", parent) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=4)
        row_idx = 0
        for cat, attrs in self.character.attributes.items():
            ttk.Label(tab, text=locale.t(f"sheet.attr_categories.{cat}"),
                      style="M.TLabel").grid(row=row_idx, column=0, columnspan=4,
                                             sticky="w", pady=(4, 0))
            row_idx += 1
            for attr_name, stat in attrs.items():
                ttk.Label(tab, text=locale.t(f"sheet.attr_names.{attr_name}"),
                          width=14, anchor="e", style="S.TLabel").grid(
                    row=row_idx, column=0, sticky="e", padx=(0, 4), pady=1)
                val_var = self._make_freebie_val_var(stat["vars"], 5)
                ttk.Label(tab, textvariable=val_var, width=3,
                          anchor="center", style="S.TLabel").grid(row=row_idx, column=1)
                base_dots = sum(v.get() for v in stat["vars"][:5])
                ttk.Button(tab, text="+", width=2, style="S.TButton",
                           command=lambda sv=stat["vars"], rv=self.freebie_remaining:
                           self._freebie_increment(sv, rv, 1, 5, cost=5)).grid(
                    row=row_idx, column=2, padx=2)
                dec_btn = ttk.Button(tab, text="−", width=2, style="S.TButton",
                                     command=lambda sv=stat["vars"], rv=self.freebie_remaining,
                                     mn=base_dots:
                                     self._freebie_decrement(sv, rv, mn, cost=5, max_dots=5))
                dec_btn.grid(row=row_idx, column=3, padx=2)
                self._wire_dec_btn(dec_btn, stat["vars"], base_dots, 5)
                row_idx += 1
        return tab

    def _build_freebies_advantages_tab(self: "Wizard", parent) -> ttk.Frame:
        import tkinter as tk
        outer = ttk.Frame(parent)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tab = ttk.Frame(canvas, padding=4)
        canvas_win = canvas.create_window((0, 0), window=tab, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        tab.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(canvas_win, width=e.width))

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / MOUSEWHEEL_DIVISOR)), "units")
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        row_idx = 0

        # Backgrounds (cost 1)
        ttk.Label(tab, text=locale.t("sheet.adv_columns.Backgrounds"),
                  style="M.TLabel").grid(row=row_idx, column=0, columnspan=4, sticky="w", pady=(2, 0))
        row_idx += 1
        bg_names = [""] + list(BACKGROUNDS)
        for bg_row in self.character.backgrounds:
            cb = ttk.Combobox(tab, textvariable=bg_row["name"], values=bg_names, width=14)
            cb.grid(row=row_idx, column=0, padx=(0, 4), pady=1)
            val_var = self._make_freebie_val_var(bg_row["vars"], 5)
            ttk.Label(tab, textvariable=val_var, width=2, anchor="center",
                      style="S.TLabel").grid(row=row_idx, column=1)
            bg_base = sum(v.get() for v in bg_row["vars"][:5])
            ttk.Button(tab, text="+", width=2, style="S.TButton",
                       command=lambda sv=bg_row["vars"], rv=self.freebie_remaining:
                       self._freebie_increment(sv, rv, 0, 5, cost=1)).grid(
                row=row_idx, column=2, padx=2)
            bg_dec = ttk.Button(tab, text="−", width=2, style="S.TButton",
                                command=lambda sv=bg_row["vars"], rv=self.freebie_remaining,
                                mn=bg_base:
                                self._freebie_decrement(sv, rv, mn, cost=1, max_dots=5))
            bg_dec.grid(row=row_idx, column=3, padx=2)
            self._wire_dec_btn(bg_dec, bg_row["vars"], bg_base, 5)
            row_idx += 1

        # Disciplines (in-clan 7 pts, out-of-clan 10 pts)
        ttk.Label(tab, text=locale.t("sheet.adv_columns.Disciplines"),
                  style="M.TLabel").grid(row=row_idx, column=0, columnspan=4, sticky="w", pady=(6, 0))
        row_idx += 1
        for disc_row in self.character.disciplines:
            cb = ttk.Combobox(tab, textvariable=disc_row["name"],
                              values=[""] + list(DISCIPLINES), width=14)
            cb.grid(row=row_idx, column=0, padx=(0, 4), pady=1)
            val_var = self._make_freebie_val_var(disc_row["vars"], 5)
            ttk.Label(tab, textvariable=val_var, width=2, anchor="center",
                      style="S.TLabel").grid(row=row_idx, column=1)
            disc_base = sum(v.get() for v in disc_row["vars"][:5])
            ttk.Button(tab, text="+", width=2, style="S.TButton",
                       command=lambda nv=disc_row["name"], sv=disc_row["vars"],
                       rv=self.freebie_remaining:
                       self._freebie_increment(
                           sv, rv, 0, 5,
                           cost=(7 if nv.get() in self._clan_disciplines else 10)
                       )).grid(row=row_idx, column=2, padx=2)
            disc_dec = ttk.Button(tab, text="−", width=2, style="S.TButton",
                                  command=lambda nv=disc_row["name"], sv=disc_row["vars"],
                                  rv=self.freebie_remaining, mn=disc_base:
                                  self._freebie_decrement(
                                      sv, rv, mn,
                                      cost=(7 if nv.get() in self._clan_disciplines else 10),
                                      max_dots=5
                                  ))
            disc_dec.grid(row=row_idx, column=3, padx=2)
            self._wire_dec_btn(disc_dec, disc_row["vars"], disc_base, 5)
            row_idx += 1

        # Virtues (cost 2)
        ttk.Label(tab, text=locale.t("sheet.adv_columns.Virtues"),
                  style="M.TLabel").grid(row=row_idx, column=0, columnspan=4, sticky="w", pady=(6, 0))
        row_idx += 1
        for virtue_row in self.character.virtues:
            ttk.Label(tab, text=virtue_row["name"].get(), width=22, anchor="e",
                      style="S.TLabel").grid(row=row_idx, column=0, padx=(0, 4), pady=1, sticky="e")
            val_var = self._make_freebie_val_var(virtue_row["vars"], 5)
            ttk.Label(tab, textvariable=val_var, width=2, anchor="center",
                      style="S.TLabel").grid(row=row_idx, column=1)
            virt_base = sum(v.get() for v in virtue_row["vars"][:5])
            ttk.Button(tab, text="+", width=2, style="S.TButton",
                       command=lambda sv=virtue_row["vars"], rv=self.freebie_remaining:
                       self._freebie_increment(sv, rv, 0, 5, cost=2)).grid(
                row=row_idx, column=2, padx=2)
            virt_dec = ttk.Button(tab, text="−", width=2, style="S.TButton",
                                  command=lambda sv=virtue_row["vars"], rv=self.freebie_remaining,
                                  mn=virt_base:
                                  self._freebie_decrement(sv, rv, mn, cost=2, max_dots=5))
            virt_dec.grid(row=row_idx, column=3, padx=2)
            self._wire_dec_btn(virt_dec, virtue_row["vars"], virt_base, 5)
            row_idx += 1

        # Live-link Conscience + Self-Control → humanity_value
        def _refresh_humanity(*_) -> None:
            conscience = sum(v.get() for v in self.character.virtues[0]["vars"][:5])
            self_ctrl  = sum(v.get() for v in self.character.virtues[1]["vars"][:5])
            self.character.humanity_value.set(conscience + self_ctrl)
            self.character.set_humanity(load=True)

        for virt_idx in (0, 1):
            for v in self.character.virtues[virt_idx]["vars"][:5]:
                v.trace_add("write", _refresh_humanity)

        return outer

    def _build_freebies_trackers_tab(self: "Wizard", parent) -> ttk.Frame:
        from config import MAX_DOT_TRACKER
        tab = ttk.Frame(parent, padding=8)

        # Snapshot base values from Step 4 (Advantages) — freebie spending cannot go below these
        base_will = self.character.will_value.get()
        base_humanity = self.character.humanity_value.get()

        def _will_inc() -> None:
            v = self.character.will_value.get()
            if v >= MAX_DOT_TRACKER or self.freebie_remaining.get() < 1:
                return
            self.freebie_remaining.set(self.freebie_remaining.get() - 1)
            self.character.will_value.set(v + 1)
            self.character.set_will(load=True)

        def _will_dec() -> None:
            v = self.character.will_value.get()
            if v <= base_will:
                return
            self.freebie_remaining.set(self.freebie_remaining.get() + 1)
            self.character.will_value.set(v - 1)
            self.character.set_will(load=True)

        def _humanity_inc() -> None:
            v = self.character.humanity_value.get()
            if v >= MAX_DOT_TRACKER or self.freebie_remaining.get() < 2:
                return
            self.freebie_remaining.set(self.freebie_remaining.get() - 2)
            self.character.humanity_value.set(v + 1)
            self.character.set_humanity(load=True)

        def _humanity_dec() -> None:
            v = self.character.humanity_value.get()
            if v <= base_humanity:
                return
            self.freebie_remaining.set(self.freebie_remaining.get() + 2)
            self.character.humanity_value.set(v - 1)
            self.character.set_humanity(load=True)

        ttk.Label(tab, text=locale.t("sheet.sheet_trackers.willpower"),
                  style="M.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Label(tab, textvariable=self.character.will_value, width=3, anchor="center",
                  style="S.TLabel").grid(row=1, column=1)
        ttk.Button(tab, text="+", width=2, style="S.TButton",
                   command=_will_inc).grid(row=1, column=2, padx=2)
        will_dec_btn = ttk.Button(tab, text="−", width=2, style="S.TButton", command=_will_dec)
        will_dec_btn.grid(row=1, column=3, padx=2)

        def _upd_will_dec(*_):
            will_dec_btn.configure(
                state="disabled" if self.character.will_value.get() <= base_will else "normal"
            )
        self.character.will_value.trace_add("write", _upd_will_dec)
        _upd_will_dec()

        ttk.Label(tab, text=locale.t("sheet.sheet_trackers.humanity"),
                  style="M.TLabel").grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Label(tab, textvariable=self.character.humanity_value, width=3, anchor="center",
                  style="S.TLabel").grid(row=3, column=1)
        ttk.Button(tab, text="+", width=2, style="S.TButton",
                   command=_humanity_inc).grid(row=3, column=2, padx=2)
        hum_dec_btn = ttk.Button(tab, text="−", width=2, style="S.TButton", command=_humanity_dec)
        hum_dec_btn.grid(row=3, column=3, padx=2)

        def _upd_hum_dec(*_):
            hum_dec_btn.configure(
                state="disabled" if self.character.humanity_value.get() <= base_humanity else "normal"
            )
        self.character.humanity_value.trace_add("write", _upd_hum_dec)
        _upd_hum_dec()

        return tab

    def _build_freebies_abils_tab(self: "Wizard", parent) -> ttk.Frame:
        import tkinter as tk
        outer = ttk.Frame(parent)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tab = ttk.Frame(canvas, padding=4)
        canvas_win = canvas.create_window((0, 0), window=tab, anchor="nw")

        def _on_tab_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        tab.bind("<Configure>", _on_tab_configure)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(canvas_win, width=e.width))

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / MOUSEWHEEL_DIVISOR)), "units")
        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        row_idx = 0
        for cat, abilities in self.character.abilities.items():
            ttk.Label(tab, text=locale.t(f"sheet.ability_categories.{cat}"),
                      style="M.TLabel").grid(row=row_idx, column=0, columnspan=7,
                                             sticky="w", pady=(4, 0))
            row_idx += 1
            for abil_name, stat in abilities.items():
                ttk.Label(tab, text=locale.t(f"sheet.ability_names.{abil_name}"),
                          width=14, anchor="e", style="S.TLabel").grid(
                    row=row_idx, column=0, sticky="e", padx=(0, 4), pady=1)
                val_var = self._make_freebie_val_var(stat["vars"], 5)
                ttk.Label(tab, textvariable=val_var, width=3,
                          anchor="center", style="S.TLabel").grid(row=row_idx, column=1)
                base_dots = sum(v.get() for v in stat["vars"][:5])
                ttk.Button(tab, text="+", width=2, style="S.TButton",
                           command=lambda sv=stat["vars"], rv=self.freebie_remaining:
                           self._freebie_increment(sv, rv, 0, 5, cost=2)).grid(
                    row=row_idx, column=2, padx=2)
                abil_dec = ttk.Button(tab, text="−", width=2, style="S.TButton",
                                      command=lambda sv=stat["vars"], rv=self.freebie_remaining,
                                      mn=base_dots:
                                      self._freebie_decrement(sv, rv, mn, cost=2, max_dots=5))
                abil_dec.grid(row=row_idx, column=3, padx=2)
                self._wire_dec_btn(abil_dec, stat["vars"], base_dots, 5)
                row_idx += 1
        return outer

    def _freebie_increment(self: "Wizard", dot_vars, remaining_var, min_dots, max_dots, cost=1) -> None:
        current = sum(v.get() for v in dot_vars[:max_dots])
        if current >= max_dots or remaining_var.get() < cost:
            return
        remaining_var.set(remaining_var.get() - cost)
        dot_vars[current].set(True)

    def _freebie_decrement(self: "Wizard", dot_vars, remaining_var, min_dots, cost=1, max_dots=None) -> None:
        limit = max_dots if max_dots is not None else len(dot_vars)
        current = sum(v.get() for v in dot_vars[:limit])
        if current <= min_dots:
            return
        remaining_var.set(remaining_var.get() + cost)
        dot_vars[current - 1].set(False)

    @staticmethod
    def _wire_dec_btn(btn, dot_vars: list, min_dots: int, max_dots: int) -> None:
        """Disable btn whenever the dot count is already at min_dots."""
        def _upd(*_):
            btn.configure(
                state="disabled" if sum(v.get() for v in dot_vars[:max_dots]) <= min_dots
                else "normal"
            )
        for v in dot_vars[:max_dots]:
            v.trace_add("write", _upd)
        _upd()

    @staticmethod
    def _make_freebie_val_var(dot_vars: list, max_dots: int):
        from tkinter import IntVar
        val_var = IntVar(value=sum(v.get() for v in dot_vars[:max_dots]))

        def _refresh(*_, vv=val_var, sv=dot_vars, md=max_dots) -> None:
            vv.set(sum(v.get() for v in sv[:md]))

        for v in dot_vars[:max_dots]:
            v.trace_add("write", _refresh)
        return val_var

    def _validate_freebies(self: "Wizard") -> str | None:
        return None  # unspent freebies are allowed
