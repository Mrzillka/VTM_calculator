from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

LOCALE_DIR = Path(__file__).parent / "locales"
_SUPPORTED: tuple[str, ...] = ("en", "ru")


class _Locale:
    """
    Application locale manager.

    Loads strings from ``locales/<lang>.json`` and notifies registered
    callbacks whenever the active language changes.  Access via the
    module-level :data:`locale` singleton.
    """

    def __init__(self, lang: str = "en") -> None:
        self._lang: str = lang if lang in _SUPPORTED else "en"
        self._data: dict[str, Any] = {}
        self._callbacks: list[Callable[[], None]] = []
        self._load()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        path = LOCALE_DIR / f"{self._lang}.json"
        with open(path, encoding="utf-8") as f:
            self._data = json.load(f)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def lang(self) -> str:
        return self._lang

    def t(self, key: str) -> str:
        """Return translated string for a dot-separated *key*; falls back to the key itself."""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, dict):
                node = node.get(part, key)
            else:
                return key
        return str(node)

    def raw(self, key: str) -> Any:
        """Return the raw JSON value (list, dict, str, …) for a dot-separated *key*."""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, dict):
                node = node.get(part)
                if node is None:
                    return None
            else:
                return None
        return node

    def switch(self) -> None:
        """Cycle to the next supported language and invoke all registered callbacks."""
        idx = _SUPPORTED.index(self._lang)
        self._lang = _SUPPORTED[(idx + 1) % len(_SUPPORTED)]
        self._load()

        dead: list[int] = []
        for i, cb in enumerate(self._callbacks):
            try:
                cb()
            except Exception:
                dead.append(i)
        for i in reversed(dead):
            self._callbacks.pop(i)

    def set_lang(self, lang: str) -> None:
        """
        Set language without notifying callbacks.

        Intended for restoring a persisted preference before any widgets
        are built, so no callbacks need updating yet.
        """
        self._lang = lang if lang in _SUPPORTED else "en"
        self._load()

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register *callback* to be called on every language switch."""
        self._callbacks.append(callback)

    def register(self, widget: Any, key: str, attr: str = "text") -> None:
        """
        Bind *widget.attr* to locale *key*.

        The widget is reconfigured immediately and on every subsequent
        language switch.  Dead widget references are silently pruned.
        """
        def _update() -> None:
            widget.configure(**{attr: self.t(key)})

        _update()
        self._callbacks.append(_update)


# ---------------------------------------------------------------------------
# Module-level singleton — import and use this everywhere.
# The initial language is read from the LANG environment variable so that
# ui/root.py can restore a persisted preference before any widget is built.
# ---------------------------------------------------------------------------
locale = _Locale(os.environ.get("LANG_PREF", "en"))