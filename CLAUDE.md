# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install base dependencies
poetry install

# Install all dependencies including network (ntfy.sh + Telegram) and dev tools
poetry install --with network,dev

# Run the player app (roller + character sheet + creation wizard)
poetry run python main.py

# Run the Storyteller app (NPC/PC tracking + session control)
poetry run python main_storyteller.py

# Run the Telegram bot
poetry run python bot/tg_bot.py

# Build a distributable executable (PyInstaller wrapper)
poetry run python build.py

# Run the test suite (pytest; lives in tests/)
poetry run python -m pytest
```

No linters are configured. Tests (pytest, in `tests/`) cover the `game/` logic
layer, the `network/` protocol/session layer, and the `ui/` helpers + roll
pipelines. The tkinter-bound tests use a session-scoped hidden `Tk()` root
fixture (`tk_root` / `character`) defined in `tests/conftest.py`. Patterns:

- **`game/`** — pure modules tested directly; `Roller` randomness is made
  deterministic by monkeypatching `game.roller.randint`.
- **`network/`** — tests never start the session's daemon threads; they drive
  the codec, queue contract, and `_handle_line`/`_post` seams directly,
  monkeypatching `httpx` for I/O.
- **`ui/`** — `theme`/`utils`/`constants` tested directly. The
  `PlayerRoot`/`StorytellerRoot` roll pipelines are tested by building the
  instance with `object.__new__(...)` (skipping the heavy `__init__`) and wiring
  only the Vars/Character each method reads, then calling the real methods.
  `roll_initiative` uses `from random import randint` *inside* the method, so
  initiative tests patch `random.randint`, not `game.roller.randint`.

## Architecture

Two separate tkinter applications sharing the same `game/` logic and `ui/` infrastructure layers.

### State ownership

A `Root` window (a `Tk` subclass) owns **all mutable state** as tkinter Vars
(`IntVar`, `BooleanVar`, `StringVar`) plus a `Character` instance for sheet
state. The matching `Interface` (a `ttk.Frame` subclass) is a **pure view** — it
reads and writes `root.*` / `root.character.*` vars directly and never holds its
own domain state.

- **Player app**: `main.py` → `ui/player/root.py::PlayerRoot` → `ui/player/interface.py::PlayerInterface`
- **Storyteller app**: `main_storyteller.py` → `ui/storyteller/root.py::StorytellerRoot` → `ui/storyteller/interface.py::StorytellerInterface`

Both root windows own the roll pipeline (`roll_and_calculate`, `roll_damage_soak`,
`roll_initiative`, plus `quick_roll`/`npc_quick_roll`), a `roll_history` list, an
`on_roll`/`_emit_roll` callback fan-out, and an optional `NtfySession`. Rolls flow
through `_record_and_emit()`, which appends to history, notifies view callbacks,
publishes to the network session, and (player only) optionally forwards to Telegram.

### Game logic (`game/`)

| File | Purpose |
|---|---|
| `roller.py` | `Roller` — d10 pool roll with VTM rules (specialisation re-rolls 10s recursively; `penalty` shifts the pool; `no_botch=True` for damage/soak) |
| `calculator.py` | `Calculator` — exact success probability via dynamic programming over single-die distributions |
| `models.py` | `RollResult` (frozen `Roller` output) and `RollRecord` (history entry; carries `roller_name` and `roll_type` ∈ `NORMAL`/`DAMAGE`/`QUICK`/`INITIATIVE`). Both expose an `outcome` property (`SUCCESS`/`FAILURE`/`BOTCH`) |
| `character.py` | `Character(CharacterIO)` — all sheet state as tkinter Vars plus mutation helpers; module-level `ATTRIBUTES` / `ABILITIES` taxonomy dicts |
| `character_io.py` | `CharacterIO` — `save()` / `load()` / `to_dict()` for JSON persistence |
| `chargen.py` | Character-creation data + stateless `CharGen` helpers: `AffiliationRules`, `AFFILIATIONS`, `CLANS`, `CLAN_DISCIPLINES`, `ARCHETYPES`, `GENERATION_CHOICES` |
| `xp_rules.py` | `XP_COSTS` table + `xp_for_increase()` — V20 experience costs with first-dot flat-cost special cases |
| `discipline_rules.py` | `DisciplinePower` / `ComboDiscipline` dataclasses; `DISCIPLINE_POWERS` (roll rules for ~30 disciplines) and `COMBO_DISCIPLINES` (combination disciplines) |

The three rule modules (`chargen`, `xp_rules`, `discipline_rules`) are pure data +
static functions with **no tkinter imports** — keep them that way so they stay
reusable and testable in isolation.

### UI patterns (`ui/`)

The widget tree is built bottom-up from `@frm`-decorated builder methods.

- **`@frm(padding, style)` decorator** (`ui/utils.py`): wraps a builder method in a `ttk.Frame`. The method receives the new frame as its first arg (after `self`), populates it, and the wrapper returns the frame. An optional `parent` kwarg overrides the frame's parent.
- **`place_widgets(grid)`** (`ui/utils.py`): thin wrapper around `.grid()` that takes a 2-D list and assigns `row`/`column` automatically.
- **`apply_icon(window, name, inherit=)`** (`ui/utils.py`): platform-aware window icon; on Windows only the root `Tk` gets `wm_iconbitmap` (Toplevels inherit the class icon) to avoid the icon-loss bug fixed in `9c04e6c`.
- **`BaseInterface`** (`ui/base_interface.py`): shared by all interface variants. Provides the scrollable roll-history panel, dot-label rendering (`_dot_trace`, guarded against destroyed widgets), and `LocaleWidgetsMixin` (`_tlabel`, `_tbutton`).
- **Locale-aware widgets**: always create text widgets via `_tlabel`/`_tbutton` or call `locale.register(widget, key)` directly so they update on runtime language switch.
- **`ui/constants.py`**: UI-only constants (window sizes, poll/debounce intervals, roll-parameter ranges, history canvas dimensions).
- **`ui/styles.py`**: `configure_main_styles()` and `configure_sheet_styles()` register all ttk styles from a theme palette.

#### UI sub-packages

- `ui/player/` — player root + interface (roll controls, quick rolls, main attr/ability comboboxes, Telegram & session controls).
- `ui/storyteller/` — `StorytellerRoot`/`StorytellerInterface` (toolbar + tabbed character panel + history) plus `panels.py` (`NPCPanel`, `PCPanel`) and `constants.py` (`NO_ROLLER` sentinel). NPCs/PCs persist under `NPC_DIR`/`PC_DIR`.
- `ui/charsheet/` — character-sheet popup (`CharsheetWindow` Toplevel + `CharsheetInterface`); section builders live in `_section_mixins.py`. Supports a `read_only` mode (used to view sheets pushed from players) and an XP-spending tracker.
- `ui/chargen/` — character-creation wizard (`ChargenWindow` Toplevel + `ChargenInterface`); per-step builders live in `_step_mixins.py`. Uses `game/chargen.py` rules.

### Theming (`ui/theme.py`)

`theme` is a module-level singleton of `_Theme` exposing light/dark palettes
(`_LIGHT` / `_DARK` — a gothic parchment vs. crypt scheme). `theme.palette` returns
the active palette dict; `theme.set_mode()` restores silently from env (no callbacks),
`theme.toggle()` flips mode and fires `on_change` callbacks (pruning dead ones).
Each root's `toggle_theme()` re-runs `configure_main_styles` and re-applies combobox
listbox colors. The mode is persisted as `THEME_PREF` in `.env`.

### Localisation (`lang.py`, `locales/`)

`locale` is a module-level singleton of `_Locale`. Use `locale.t("dot.separated.key")`
to get a string. Add new strings to **both** `locales/en.json` and `locales/ru.json`.
Use `locale.reverse_lookup_en(section, value)` to canonicalise a displayed string back
to its English key (e.g. when serialising character data), and
`locale.translate_known(section, en_value)` for the reverse. `locale.on_change()`
registers callbacks fired on language switch.

### Network (`network/`)

Split into transport and wire-format:

- **`session.py`**: `NtfySession` connects both apps to a shared [ntfy.sh](https://ntfy.sh) topic. It runs two daemon threads — a reconnecting SSE subscriber and a single publish worker that drains a `queue.Queue`. Messages are gzip-compressed JSON; each instance tags outgoing messages with a random sender id so echoes are discarded on receive. The session is **symmetric** — there is no client/server role.
- **`protocol.py`**: message-type constants (`MSG_ROLL`, `MSG_SHEET`, `MSG_SHEET_TRACKERS`) and the `roll_record_to_dict` / `dict_to_roll_record` codecs.

The tkinter thread polls an inbound `queue.Queue` every `NET_POLL_MS` (100 ms) via
`root.after()` (`_poll_net_queue`) — **never call tkinter from the network threads.**
The Storyteller routes `sheet` / `sheet_trackers` events into its PC panel; the player
publishes its sheet (`send_sheet_to_server`) and debounced tracker updates.

### Data persistence

Characters are saved as **per-name JSON files** in a `characters/` subdirectory of
the app-data dir:
- **Windows**: `%APPDATA%\VTM Roller\characters\{name}.json`
- **macOS**: `~/Library/Application Support/VTM Roller/characters/`
- **Linux**: `$XDG_DATA_HOME/VTM Roller/characters/` (or `~/.local/share/`)

Storyteller NPCs and PCs are saved under sibling `npcs/` and `pcs/` directories.
A legacy single-file `character.json` is migrated into `characters/` on first load.
`ensure_app_data_dir()` (called from both `main*.py` entry points) creates these
directories and the `.env` file.

Preferences are stored in `%APPDATA%\VTM Roller\.env`: `BOT_TOKEN`, `CHAT_ID`,
`THREAD_ID`, `LANG_PREF`, `THEME_PREF`, `SESSION_CODE`, `LAST_CHARACTER`,
`UNSKILLED_PENALTY`, `CHARGEN_MIN_WILL`. The project-root `.env` is only for local
dev overrides.

`installer.py` is a standalone distribution wizard for Storyteller builds — it writes
the end-user `.env` and is not part of the regular dev workflow. `build.py` wraps
PyInstaller to produce executables.

### Configuration (`config.py`)

All game constants live here: `GENERATION_RULES` (+ `MIN/MAX/DEFAULT_GENERATION`),
`DISCIPLINES`, `DISCIPLINE_PATHS`, `MERITS`, `FLAWS`, `WOUND_LEVELS` (`WoundLevel`
namedtuples), `BACKGROUNDS`, sheet/tracker grid sizes, and the cross-platform
app-data paths (`APP_DATA_DIR`, `ENV_FILE_PATH`, `CHARACTERS_DIR`, `NPC_DIR`,
`PC_DIR`). `resource_path()` resolves asset paths correctly whether running from
source or a PyInstaller bundle. `FONT` is the shared UI font.
