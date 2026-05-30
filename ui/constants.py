"""UI-only constants shared across both applications."""

# ── Character sheet window ────────────────────────────────────────────────────
SHEET_WIDTH: int = 1150
SHEET_HEIGHT: int = 750
SHEET_MIN_WIDTH: int = 700
SHEET_MIN_HEIGHT: int = 450

# Platform convention: tkinter mouse-wheel delta is in units of 120 per notch.
MOUSEWHEEL_DIVISOR: int = 120

# ── Polling / debounce intervals (ms) ────────────────────────────────────────
NET_POLL_MS: int = 100
TRACKER_DEBOUNCE_MS: int = 500
AUTOSAVE_DEBOUNCE_MS: int = 1500
BOT_STATUS_POLL_MS: int = 1000

# ── Roll-control widget sizes ─────────────────────────────────────────────────
SCALE_LENGTH: int = 125   # pixel width of ttk.Scale widgets

# Roll-parameter ranges
DICE_MIN: int = 1
DICE_MAX: int = 15
DIFFICULTY_MIN: int = 2
DIFFICULTY_MAX: int = 10
AUTO_SUCCESS_MAX: int = 5
SUCCESS_NEEDED_MAX: int = 10
QUICK_BP_MAX: int = 5

# ── History panel canvas dimensions ──────────────────────────────────────────
HISTORY_WIDTH: int = 300
HISTORY_HEIGHT: int = 340
ST_HISTORY_WIDTH: int = 380
ST_HISTORY_HEIGHT: int = 420
