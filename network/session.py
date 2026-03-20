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
_RECONNECT_DELAY = 5   # seconds between reconnect attempts
_PUBLISH_TIMEOUT = 15  # seconds for a single POST

# Sentinel pushed to the outgoing queue to stop the publish worker.
_STOP_SENTINEL = object()


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

    Outgoing messages are handled by a single dedicated daemon thread so
    that a slow POST can never block the tkinter thread or accumulate
    unbounded background threads.
    """

    def __init__(
        self,
        topic: str,
        event_queue: "queue.Queue[tuple[str, Any]]",
    ) -> None:
        self._topic = topic
        self._sender_id = uuid.uuid4().hex
        self._queue = event_queue

        # Subscribe-side
        self._stop_event = threading.Event()
        self._subscribe_client: httpx.Client | None = None
        self._subscribe_lock = threading.Lock()

        # Publish-side: single worker thread drains _publish_queue
        self._publish_queue: queue.Queue[object] = queue.Queue()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def topic(self) -> str:
        return self._topic

    def start(self) -> None:
        """Start the subscribe listener and publish worker as daemon threads."""
        self._stop_event.clear()
        threading.Thread(target=self._subscribe_loop, daemon=True).start()
        threading.Thread(target=self._publish_worker, daemon=True).start()

    def stop(self) -> None:
        """
        Signal both threads to stop and interrupt any blocking SSE stream.

        The threads are daemons so they will not prevent process exit, but
        calling stop() releases the network connection immediately.
        """
        self._stop_event.set()
        # Close the active httpx client from the outside to unblock iter_lines().
        with self._subscribe_lock:
            if self._subscribe_client is not None:
                try:
                    self._subscribe_client.close()
                except Exception:
                    pass
                self._subscribe_client = None
        # Wake up the publish worker so it can exit.
        self._publish_queue.put(_STOP_SENTINEL)

    def publish(self, msg_type: str, data: dict[str, Any]) -> None:
        """Enqueue a message for the publish worker; never blocks the caller."""
        if not self._stop_event.is_set():
            self._publish_queue.put((msg_type, data))

    # ── Subscribe loop ────────────────────────────────────────────────────────

    def _subscribe_loop(self) -> None:
        """
        Reconnecting SSE loop.

        ``since`` is updated to the current time on every reconnect so that
        only messages arriving after reconnection are replayed — not the
        entire session history.
        """
        while not self._stop_event.is_set():
            # Compute `since` fresh on every connection attempt to avoid
            # replaying old messages after a reconnect.
            since = str(int(time.time()))
            url = f"{_NTFY_BASE}/{self._topic}/sse?since={since}"

            try:
                client = httpx.Client(timeout=None)
                with self._subscribe_lock:
                    if self._stop_event.is_set():
                        client.close()
                        return
                    self._subscribe_client = client

                with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if self._stop_event.is_set():
                            return
                        if not line.startswith("data:"):
                            continue
                        raw = line[5:].strip()
                        if not raw or raw == "{}":
                            continue
                        self._handle_line(raw)

            except Exception as exc:
                if self._stop_event.is_set():
                    return
                logger.warning(
                    "ntfy subscribe error, retrying in %ds: %s",
                    _RECONNECT_DELAY, exc,
                )
            finally:
                with self._subscribe_lock:
                    self._subscribe_client = None

            if not self._stop_event.is_set():
                self._stop_event.wait(timeout=_RECONNECT_DELAY)

    def _handle_line(self, raw: str) -> None:
        """Parse one SSE data line and enqueue the inner event if valid."""
        try:
            outer = json.loads(raw)
            # ntfy sends keepalive events; skip them.
            if outer.get("event") == "keepalive":
                return
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

    # ── Publish worker ────────────────────────────────────────────────────────

    def _publish_worker(self) -> None:
        """Single background thread that drains the outgoing message queue."""
        while True:
            item = self._publish_queue.get()
            if item is _STOP_SENTINEL:
                return
            msg_type, data = item  # type: ignore[misc]
            self._post(msg_type, data)  # type: ignore[arg-type]

    def _post(self, msg_type: str, data: dict[str, Any]) -> None:
        payload = {
            "type":      msg_type,
            "data":      data,
            "sender_id": self._sender_id,
        }
        body = base64.b64encode(_pack(payload)).decode()
        try:
            httpx.post(
                f"{_NTFY_BASE}/{self._topic}",
                content=body.encode(),
                timeout=_PUBLISH_TIMEOUT,
            )
        except Exception as exc:
            logger.error("ntfy publish error (%s): %s", msg_type, exc)