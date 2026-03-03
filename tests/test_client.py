"""Tests for the toq SDK client."""

import toq


def test_connect_default():
    client = toq.connect()
    assert client._url == "http://127.0.0.1:9010"


def test_connect_custom_url():
    client = toq.connect("http://localhost:8080")
    assert client._url == "http://localhost:8080"


def test_connect_env_var(monkeypatch):
    monkeypatch.setenv("TOQ_API_URL", "http://custom:1234")
    client = toq.connect()
    assert client._url == "http://custom:1234"


def test_connect_explicit_overrides_env(monkeypatch):
    monkeypatch.setenv("TOQ_API_URL", "http://from-env:1234")
    client = toq.connect("http://explicit:5678")
    assert client._url == "http://explicit:5678"


def test_message_dataclass():
    client = toq.connect()
    msg = toq.Message(
        id="msg-1",
        type="message.send",
        sender="toq://peer.com/agent",
        body={"text": "hello"},
        thread_id="thr-1",
        reply_to=None,
        content_type="text/plain",
        timestamp="2026-03-02T00:00:00Z",
        _client=client,
    )
    assert msg.id == "msg-1"
    assert msg.sender == "toq://peer.com/agent"
    assert msg.body == {"text": "hello"}


import pytest


@pytest.mark.asyncio
async def test_daemon_not_running():
    client = toq.connect("http://127.0.0.1:19999")
    with pytest.raises(toq.ToqError, match="not running"):
        await client.status()
