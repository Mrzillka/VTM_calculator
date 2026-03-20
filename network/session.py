from __future__ import annotations

import base64
import gzip
import json
import logging
import queue
import threading
import time
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_NTFY_BASE = "https://ntfy.sh"
_RECONNECT_DELAY = 5  # seconds between reconnect attempts


def _pack(payload: dict[str, Any]) -> bytes:
    """gzip-compress a dict and return raw bytes."""
    return gzip.compress(json.dumps(payload).encode())


def _unpack(data: bytes) -> dict[str, Any]:
    """Decompress and parse bytes received from ntfy.sh."""
    return json.loads(gzip.decompress(data))


class NtfySession:
    """
    Symmetric publish/subscribe session over ntfy.sh.

    Both the Storyteller and Player apps use the same class — there is no
    server or client role.  All participants publish to and subscribe from
    the shared topic ``ntfy.sh/{topic}``.

    Each instance tags outgoing messages with a random ``sender_id`` so
    that echoed messages are silently discarded.

    Inbound events are placed on *event_queue* as ``(event_type, data)``
    tuples for the tkinter main thread to consume via ``root.after()``
    polling.
    """

    def __init__(
        self,
        topic: str,
        event_queue: "queue.Queue[tuple[str, Any]]",
    ) -> None:
        self._topic = topic
        self._sender_id = uuid.uuid4().hex
        self._queue = event_queue
        self._active = False

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def topic(self) -> str:
        return self._topic

    def start(self) -> None:
        """Begin subscribing in a daemon thread."""
        self._active = True
        threading.Thread(target=self._subscribe_loop, daemon=True).start()

    def stop(self) -> None:
        """Request the subscription thread to exit on the next iteration."""
        self._active = False

    def publish(self, msg_type: str, data: dict[str, Any]) -> None:
        """Fire-and-forget publish in a daemon thread."""
        threading.Thread(
            target=self._post,
            args=(msg_type, data),
            daemon=True,
        ).start()

    # ── Subscribe loop ────────────────────────────────────────────────────────

    def _subscribe_loop(self) -> None:
        """Reconnecting SSE loop; only receives messages published after start."""
        since = str(int(time.time()))
        url = f"{_NTFY_BASE}/{self._topic}/sse?since={since}"

        while self._active:
            try:
                with httpx.Client(timeout=None) as client:
                    with client.stream("GET", url) as resp:
                        resp.raise_for_status()
                        for line in resp.iter_lines():
                            if not self._active:
                                return
                            if not line.startswith("data:"):
                                continue
                            raw = line[5:].strip()
                            if not raw or raw == "{}":
                                continue
                            self._handle_line(raw)
            except Exception as exc:
                if not self._active:
                    return
                logger.warning(
                    "ntfy subscribe error, retrying in %ds: %s",
                    _RECONNECT_DELAY, exc,
                )
                time.sleep(_RECONNECT_DELAY)

    def _handle_line(self, raw: str) -> None:
        """Parse one SSE data line and enqueue the inner event if valid."""
        try:
            outer = json.loads(raw)
            if outer.get("event") == "keepalive":
                return
            # We always send gzip-compressed bytes encoded as base64 in the
            # ntfy "message" field.
            encoded = outer.get("message", "")
            if not encoded:
                return
            inner = _unpack(base64.b64decode(encoded))
            if inner.get("sender_id") == self._sender_id:
                return  # own message echoed back — ignore
            event_type = inner.get("type")
            data = inner.get("data", {})
            if event_type:
                self._queue.put((event_type, data))
        except Exception as exc:
            logger.debug("ntfy parse error: %s  raw=%r", exc, raw[:120])

    # ── Publish ───────────────────────────────────────────────────────────────

    def _post(self, msg_type: str, data: dict[str, Any]) -> None:
        payload = {
            "type":      msg_type,
            "data":      data,
            "sender_id": self._sender_id,
        }
        # gzip-compress and base64-encode so the payload survives as a
        # printable string in the ntfy "message" field.
        body = base64.b64encode(_pack(payload)).decode()
        try:
            httpx.post(
                f"{_NTFY_BASE}/{self._topic}",
                content=body.encode(),
                timeout=15,
            )
        except Exception as exc:
            logger.error("ntfy publish error: %s", exc)