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
        self._all_data: dict[str, dict[str, Any]] = {}
        self._callbacks: list[Callable[[], None]] = []
        self._load_all()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_all(self) -> None:
        """Load every supported locale file into _all_data and set _data."""
        for lang in _SUPPORTED:
            path = LOCALE_DIR / f"{lang}.json"
            with open(path, encoding="utf-8") as f:
                self._all_data[lang] = json.load(f)
        self._data = self._all_data[self._lang]

    def _load(self) -> None:
        self._data = self._all_data[self._lang]

    @staticmethod
    def _navigate(data: dict[str, Any], section: str) -> dict[str, Any]:
        """Return the nested dict at *section* (dot-separated), or {} if not found."""
        node: Any = data
        for part in section.split("."):
            if isinstance(node, dict):
                node = node.get(part, {})
            else:
                return {}
        return node if isinstance(node, dict) else {}

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

    def reverse_lookup_en(self, section: str, value: str) -> str:
        """
        Find the English canonical key for *value* in *section*.

        Searches all supported locales so it works even when *value* is a
        translation from a different language than the currently active one.
        Returns *value* unchanged if it is not found in any locale (i.e. a
        user-entered custom string).
        """
        if not value:
            return value
        for lang_data in self._all_data.values():
            section_map = self._navigate(lang_data, section)
            reverse = {v: k for k, v in section_map.items()}
            if value in reverse:
                return reverse[value]
        return value

    def translate_known(self, section: str, value: str) -> str:
        """
        Translate *value* to the active language if it is a known entry in *section*.

        Searches all supported locales for a reverse match, then returns the
        equivalent string in the active language.  Returns *value* unchanged if
        it is not a known entry (i.e. a user-entered custom string).
        """
        en_key = self.reverse_lookup_en(section, value)
        current_map = self._navigate(self._data, section)
        return current_map.get(en_key, value)

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