"""Tests for the toq SDK client."""

import pytest
import toq


def test_connect_default():
    client = toq.connect()
    assert client._url == "http://127.0.0.1:9010"
    assert isinstance(client, toq.Client)


def test_connect_async_default():
    client = toq.connect_async()
    assert client._url == "http://127.0.0.1:9010"
    assert isinstance(client, toq.AsyncClient)


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
    client = toq.connect_async()
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


def test_sync_daemon_not_running():
    client = toq.connect("http://127.0.0.1:19999")
    with pytest.raises(toq.ToqError, match="not running"):
        client.status()


@pytest.mark.asyncio
async def test_async_daemon_not_running():
    client = toq.connect_async("http://127.0.0.1:19999")
    with pytest.raises(toq.ToqError, match="not running"):
        await client.status()


# --- Client method tests with mocked HTTP ---


class MockResponse:
    def __init__(self, status_code=200, json_data=None, text_data="ok"):
        self.status_code = status_code
        self._json = json_data or {}
        self._text = text_data

    def json(self):
        return self._json

    @property
    def text(self):
        return self._text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def test_sync_send(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse(json_data={"id": "m1", "status": "delivered", "thread_id": "t1", "timestamp": "now"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.send("toq://host/agent", "hello")
    assert result["status"] == "delivered"


def test_sync_peers(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse(json_data={"peers": [{"public_key": "k1", "address": "a1", "status": "connected", "last_seen": "now"}]})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.peers()
    assert len(result) == 1
    assert result[0]["public_key"] == "k1"


def test_sync_block(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.block("ed25519:abc")  # should not raise


def test_sync_unblock(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.unblock("ed25519:abc")  # should not raise


def test_sync_approvals(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse(json_data={"approvals": [{"id": "k1", "public_key": "k1", "address": "a1", "requested_at": "now"}]})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.approvals()
    assert len(result) == 1


def test_sync_approve(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.approve("k1")  # should not raise


def test_sync_deny(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.deny("k1")  # should not raise


def test_sync_health(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse(text_data="ok")
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.health()
    assert result == "ok"


def test_sync_status(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse(json_data={"status": "running", "address": "toq://localhost/agent"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.status()
    assert result["status"] == "running"


def test_sync_shutdown(monkeypatch):
    client = toq.connect("http://localhost:9010")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.shutdown()  # should not raise
