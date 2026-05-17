# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install base dependencies
poetry install

# Install all dependencies including network (ntfy.sh + Telegram) and dev tools
poetry install --with network,dev

# Run the player app (character sheet + roller)
poetry run python main.py

# Run the Storyteller app
poetry run python main_storyteller.py

# Run the Telegram bot
poetry run python bot/tg_bot.py
```

There are no tests or linters configured in this project.

## Architecture

Two separate tkinter applications sharing the same `game/` logic layer.

### State ownership

`Root` (a `Tk` subclass) owns **all mutable state** as tkinter Vars (`IntVar`, `BooleanVar`, `StringVar`). `Interface` (a `ttk.Frame` subclass) is a **pure view** — it reads and writes `root.*` vars directly and never holds its own domain state.

- **Player app**: `main.py` → `ui/root.py::Root` → `ui/interface.py::Interface`
- **Storyteller app**: `main_storyteller.py` → `ui/storyteller/root.py::Root` → `ui/storyteller/interface.py::Interface`

### Game logic (`game/`)

| File | Purpose |
|---|---|
| `roller.py` | `Roller` — performs a d10 pool roll with VTM rules (specialisation re-rolls 10s recursively; `no_botch=True` for damage/soak) |
| `calculator.py` | `Calculator` — exact success probability via dynamic programming over single-die distributions |
| `models.py` | `RollResult` (frozen output from `Roller`) and `RollRecord` (history entry with metadata) |
| `character.py` | `Character(CharacterIO)` — all character sheet state as tkinter Vars; mutation methods (`set_blood`, `heal`, `end_scene`, etc.) |
| `character_io.py` | `CharacterIO` — `save()` / `load()` / `to_dict()` for JSON persistence |

### UI patterns (`ui/`)

- **`@frm` decorator** (`ui/utils.py`): wraps any builder method in a `ttk.Frame`. Methods decorated with `@frm` receive the new frame as their first arg and return it — this is how the entire widget tree is constructed.
- **`place_widgets(grid)`**: a thin wrapper around `.grid()` that accepts a 2-D list and assigns `row`/`column` automatically.
- **`BaseInterface`** (`ui/base_interface.py`): shared between both apps. Provides the scrollable roll-history panel and `LocaleWidgetsMixin` (`_tlabel`, `_tbutton`) which auto-register widgets for live language switching.
- **Locale-aware widgets**: always create text widgets via `_tlabel`/`_tbutton` or call `locale.register(widget, key)` directly. This ensures they update when the user switches language at runtime.
- `ui/charsheet/` — character sheet popup (separate `Toplevel`); `ui/storyteller/` — storyteller-specific panels (NPC list, PC tracker, session control).

### Localisation (`lang.py`, `locales/`)

`locale` is a module-level singleton of `_Locale`. Use `locale.t("dot.separated.key")` to get a string. Add new strings to both `locales/en.json` and `locales/ru.json`. Use `locale.reverse_lookup_en(section, value)` when you need to canonicalise a displayed string back to its English key (e.g. when serialising character data).

### Network (`network/`)

`NtfySession` connects both apps to a shared [ntfy.sh](https://ntfy.sh) topic. It runs two daemon threads: a reconnecting SSE subscriber and a single publish worker that drains a `queue.Queue`. The tkinter thread polls an inbound `queue.Queue` every 100 ms via `root.after()` — never call tkinter from the network threads.

Messages are gzip-compressed, base64-encoded JSON. Each instance tags outgoing messages with a random `sender_id` so echoed messages are silently discarded on receive.

### Data persistence

Characters are saved as JSON files at:
- **Windows**: `%APPDATA%\VTM Roller\characters\{name}.json`
- **macOS**: `~/Library/Application Support/VTM Roller/characters/`
- **Linux**: `$XDG_DATA_HOME/VTM Roller/characters/` (or `~/.local/share/`)

Bot token and preferences (`LANG_PREF`, `CHAT_ID`, `SESSION_CODE`, `LAST_CHARACTER`) are stored in `%APPDATA%\VTM Roller\.env`. The project-root `.env` is only for local dev overrides.

`installer.py` is a standalone distribution wizard for Storyteller builds — it writes the `.env` file for end users and is not part of the regular dev workflow.

### Configuration (`config.py`)

All game constants live here: `GENERATION_RULES`, `DISCIPLINES`, `MERITS`, `FLAWS`, `WOUND_LEVELS`, `BACKGROUNDS`. `resource_path()` resolves asset paths correctly whether running from source or a PyInstaller bundle.
