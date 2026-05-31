"""Tests for network.session.NtfySession and its codec helpers.

The session normally runs two daemon threads doing real HTTP against ntfy.sh.
None of these tests call ``start()``; they drive the pure seams directly:

* ``_pack`` / ``_unpack``        — the gzip+JSON codec
* ``publish`` / ``stop``         — the outgoing-queue contract
* ``_handle_line``               — inbound SSE parsing (fed hand-built frames)
* ``_post`` / ``_publish_worker``— outgoing encoding (with httpx monkeypatched)
"""
from __future__ import annotations

import base64
import json
import queue

import pytest

from network import session as session_mod
from network.session import NtfySession, _pack, _unpack


@pytest.fixture
def event_queue():
    return queue.Queue()


@pytest.fixture
def sess(event_queue):
    return NtfySession("test-topic", event_queue)


def _make_frame(*, msg_type="roll", data=None, sender_id="other-sender", event="message"):
    """Build a raw SSE ``data:`` line exactly as ntfy.sh delivers it.

    Layering mirrors the send path: inner payload -> JSON -> gzip -> base64,
    wrapped in ntfy's ``{"event", "message"}`` envelope.
    """
    inner = {"type": msg_type, "data": data or {}, "sender_id": sender_id}
    outer = {"event": event}
    if event != "keepalive":
        outer["message"] = base64.b64encode(_pack(inner)).decode()
    return json.dumps(outer)


# ── Codec ────────────────────────────────────────────────────────────────────

def test_pack_round_trip():
    payload = {"type": "roll", "data": {"successes": 3}, "sender_id": "abc"}
    assert _unpack(_pack(payload)) == payload


def test_pack_output_is_gzip():
    # gzip magic number 0x1f 0x8b.
    assert _pack({"a": 1})[:2] == b"\x1f\x8b"


# ── Construction ─────────────────────────────────────────────────────────────

def test_topic_property(sess):
    assert sess.topic == "test-topic"


def test_sender_id_is_unique_hex(event_queue):
    a = NtfySession("t", event_queue)
    b = NtfySession("t", event_queue)
    assert a._sender_id != b._sender_id
    assert len(a._sender_id) == 32
    int(a._sender_id, 16)  # raises if not valid hex


# ── publish / stop queue contract ────────────────────────────────────────────

def test_publish_enqueues_message(sess):
    sess.publish("roll", {"successes": 2})
    assert sess._publish_queue.get_nowait() == ("roll", {"successes": 2})


def test_publish_is_a_noop_after_stop(sess):
    sess.stop()
    sess.publish("roll", {"successes": 2})
    # stop() enqueues the stop sentinel; publish() after stop adds nothing.
    assert sess._publish_queue.get_nowait() is session_mod._STOP_SENTINEL
    with pytest.raises(queue.Empty):
        sess._publish_queue.get_nowait()


def test_stop_sets_the_stop_event(sess):
    assert not sess._stop_event.is_set()
    sess.stop()
    assert sess._stop_event.is_set()


# ── Inbound parsing (_handle_line) ───────────────────────────────────────────

def test_handle_line_enqueues_foreign_message(sess, event_queue):
    sess._handle_line(_make_frame(msg_type="roll", data={"successes": 4}))
    assert event_queue.get_nowait() == ("roll", {"successes": 4})


def test_handle_line_discards_own_echo(sess, event_queue):
    # A message tagged with our own sender_id must be ignored.
    sess._handle_line(_make_frame(sender_id=sess._sender_id))
    assert event_queue.empty()


def test_handle_line_skips_keepalive(sess, event_queue):
    sess._handle_line(_make_frame(event="keepalive"))
    assert event_queue.empty()


def test_handle_line_skips_message_without_type(sess, event_queue):
    inner = {"data": {"x": 1}, "sender_id": "other"}  # no "type"
    raw = json.dumps({"event": "message", "message": base64.b64encode(_pack(inner)).decode()})
    sess._handle_line(raw)
    assert event_queue.empty()


def test_handle_line_defaults_missing_data_to_empty_dict(sess, event_queue):
    inner = {"type": "sheet", "sender_id": "other"}  # no "data"
    raw = json.dumps({"event": "message", "message": base64.b64encode(_pack(inner)).decode()})
    sess._handle_line(raw)
    assert event_queue.get_nowait() == ("sheet", {})


def test_handle_line_swallows_malformed_input(sess, event_queue):
    # Garbage must be caught and logged, never raised to the SSE loop.
    sess._handle_line("not json at all")
    sess._handle_line(json.dumps({"event": "message", "message": "@@not-base64@@"}))
    assert event_queue.empty()


# ── Outbound encoding (_post / _publish_worker) ──────────────────────────────

def test_post_encodes_payload_and_calls_httpx(sess, monkeypatch):
    captured = {}

    def fake_post(url, *, content, timeout):
        captured["url"] = url
        captured["content"] = content

    monkeypatch.setattr(session_mod.httpx, "post", fake_post)

    sess._post("roll", {"successes": 1})

    assert captured["url"].endswith("/test-topic")
    # Decode the wire body back into the original payload.
    decoded = _unpack(base64.b64decode(captured["content"].decode()))
    assert decoded["type"] == "roll"
    assert decoded["data"] == {"successes": 1}
    assert decoded["sender_id"] == sess._sender_id


def test_post_swallows_httpx_errors(sess, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(session_mod.httpx, "post", boom)
    # Must not propagate — the publish worker should survive a failed POST.
    sess._post("roll", {"successes": 1})


def test_publish_worker_drains_until_sentinel(sess, monkeypatch):
    posted = []
    monkeypatch.setattr(sess, "_post", lambda mt, d: posted.append((mt, d)))

    sess._publish_queue.put(("roll", {"successes": 2}))
    sess._publish_queue.put(("sheet", {"name": "X"}))
    sess._publish_queue.put(session_mod._STOP_SENTINEL)

    sess._publish_worker()  # returns when it hits the sentinel

    assert posted == [("roll", {"successes": 2}), ("sheet", {"name": "X"})]
