# VTM Roller

A dice-rolling and character-sheet tool for **Vampire: The Masquerade** (V20 rules), built with Python and tkinter.

## Features

- **Dice roller** — d10 pool rolls with difficulty, auto-successes, specialisation (reroll 10s), and botch detection
- **Probability calculator** — exact success probability for any roll configuration
- **Character sheet** — attributes, disciplines, backgrounds, merits/flaws, wound levels, blood pool, and generation rules (4th–15th generation)
- **Storyteller mode** — separate view for the Storyteller to track multiple characters and roll for NPCs
- **Live session sharing** — Storyteller and players sync rolls in real time over [ntfy.sh](https://ntfy.sh) (no server required)
- **Telegram bot** — roll dice from a Telegram chat via `/roll` commands
- **Roll history** — per-session log of all rolls with outcome and probability
- **Localisation** — English and Russian UI (switchable at runtime)
- **Persistent characters** — character data saved as JSON in the OS app-data directory

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management

## Installation

```bash
git clone <repo-url>
cd vtm-calculator
poetry install
```

For the network session and Telegram bot, install the optional dependency groups:

```bash
poetry install --with network,dev
```

## Running

**Player app (character sheet + roller):**

```bash
poetry run python main.py
```

**Storyteller app:**

```bash
poetry run python main_storyteller.py
```

## Telegram Bot

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. Add `BOT_TOKEN=<your_token>` to `%APPDATA%\VTM Roller\.env` (Windows) or the equivalent path on macOS/Linux.
3. Run the bot:

```bash
poetry run python bot/tg_bot.py
```

## Live Session (ntfy.sh)

Both apps can connect to a shared ntfy.sh topic so the Storyteller sees every player roll (and vice versa) in real time. Enter the same topic name in the session panel of each app — no account or server setup required.

## Project Structure

```
main.py                 # Player app entry point
main_storyteller.py     # Storyteller app entry point
config.py               # Constants, generation rules, app-data paths
lang.py                 # Localisation singleton
game/
  calculator.py         # Exact probability calculator
  roller.py             # Dice roller (VTM rules)
  models.py             # RollResult / RollRecord dataclasses
  character.py          # Character model
ui/
  root.py               # Player app root window
  interface.py          # Player app main interface
  charsheet/            # Character-sheet panels
  storyteller/          # Storyteller app panels
  styles.py             # Shared tkinter styles
network/
  session.py            # ntfy.sh publish/subscribe session
  protocol.py           # Message protocol helpers
bot/
  tg_bot.py             # Telegram bot
locales/
  en.json               # English strings
  ru.json               # Russian strings
```
