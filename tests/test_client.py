"""Tests for the toq SDK client."""

import pytest
import toq


def test_connect_default():
    client = toq.connect()
    assert client._url == "http://127.0.0.1:9009"
    assert isinstance(client, toq.Client)


def test_connect_async_default():
    client = toq.connect_async()
    assert client._url == "http://127.0.0.1:9009"
    assert isinstance(client, toq.AsyncClient)


def test_connect_custom_url():
    client = toq.connect("http://localhost:8080")
    assert client._url == "http://localhost:8080"


def test_connect_env_var(monkeypatch):
    monkeypatch.setenv("TOQ_URL", "http://custom:1234")
    client = toq.connect()
    assert client._url == "http://custom:1234"


def test_connect_explicit_overrides_env(monkeypatch):
    monkeypatch.setenv("TOQ_URL", "http://from-env:1234")
    client = toq.connect("http://explicit:5678")
    assert client._url == "http://explicit:5678"


def test_connect_workspace_state(monkeypatch, tmp_path):
    monkeypatch.delenv("TOQ_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    toq_dir = tmp_path / ".toq"
    toq_dir.mkdir()
    (toq_dir / "state.json").write_text('{"port": 9042}')
    client = toq.connect()
    assert client._url == "http://127.0.0.1:9042"


def test_connect_env_overrides_workspace(monkeypatch, tmp_path):
    monkeypatch.setenv("TOQ_URL", "http://from-env:1234")
    monkeypatch.chdir(tmp_path)
    toq_dir = tmp_path / ".toq"
    toq_dir.mkdir()
    (toq_dir / "state.json").write_text('{"port": 9042}')
    client = toq.connect()
    assert client._url == "http://from-env:1234"


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
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"id": "m1", "status": "delivered", "thread_id": "t1", "timestamp": "now"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.send("toq://host/agent", "hello")
    assert result["status"] == "delivered"


def test_sync_peers(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"peers": [{"public_key": "k1", "address": "a1", "status": "connected", "last_seen": "now"}]})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.peers()
    assert len(result) == 1
    assert result[0]["public_key"] == "k1"


def test_sync_block(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.block("ed25519:abc")  # should not raise


def test_sync_unblock(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.unblock("ed25519:abc")  # should not raise


def test_sync_approvals(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"approvals": [{"id": "k1", "public_key": "k1", "address": "a1", "requested_at": "now"}]})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.approvals()
    assert len(result) == 1


def test_sync_approve(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.approve("k1")  # should not raise


def test_sync_deny(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.deny("k1")  # should not raise


def test_sync_health(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(text_data="ok")
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.health()
    assert result == "ok"


def test_sync_status(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"status": "running", "address": "toq://localhost/agent"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.status()
    assert result["status"] == "running"


def test_sync_shutdown(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse()
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    client.shutdown()  # should not raise


def test_sync_send_close_thread(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"id": "m1", "status": "delivered", "thread_id": "t1", "timestamp": "now"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.send("toq://host/agent", "goodbye", close_thread=True)
    assert result["status"] == "delivered"


def test_sync_send_multi_recipient(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={
        "results": [
            {"to": "toq://host/a", "id": "m1", "thread_id": "t1", "status": "queued"},
            {"to": "toq://host/b", "id": "m2", "thread_id": "t2", "status": "queued"},
        ],
        "timestamp": "now",
    })
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.send(["toq://host/a", "toq://host/b"], "hello both")
    assert len(result["results"]) == 2


def test_sync_stream_start(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"stream_id": "s1", "thread_id": "t1"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.stream_start("toq://host/agent")
    assert result["stream_id"] == "s1"


def test_sync_stream_chunk(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"chunk_id": "c1"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.stream_chunk("s1", "hello ")
    assert result["chunk_id"] == "c1"


def test_sync_stream_end(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"chunk_id": "e1"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.stream_end("s1", close_thread=True)
    assert result["chunk_id"] == "e1"


def test_sync_revoke(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={})
    called = {}
    def capture(*a, **kw):
        called["method"] = a[0] if a else kw.get("method")
        called["url"] = str(a[1]) if len(a) > 1 else str(kw.get("url"))
        return resp
    monkeypatch.setattr(client._http, "request", capture)
    client.revoke("ed25519:abc+/123=")
    assert called["method"] == "POST"
    assert "/revoke" in called["url"]
    assert "%2B" in called["url"] or "%2F" in called["url"]


def test_sync_history(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"messages": [{"id": "1", "from": "alice", "body": {"text": "hi"}}]})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.history(limit=10, from_addr="alice")
    assert len(result) == 1
    assert result[0]["from"] == "alice"


def test_sync_history_defaults(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"messages": []})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.history()
    assert result == []


def test_sync_block_by_address(monkeypatch):
    client = toq.connect("http://localhost:9009")
    called = {}
    def capture(*a, **kw):
        called["method"] = a[0]
        called["url"] = a[1]
        called["json"] = kw.get("json")
        return MockResponse()
    monkeypatch.setattr(client._http, "request", capture)
    client.block(from_addr="toq://host/*")
    assert called["method"] == "POST"
    assert called["url"].endswith("/v1/block")
    assert called["json"] == {"from": "toq://host/*"}


def test_sync_approve_by_key(monkeypatch):
    client = toq.connect("http://localhost:9009")
    called = {}
    def capture(*a, **kw):
        called["method"] = a[0]
        called["url"] = a[1]
        called["json"] = kw.get("json")
        return MockResponse()
    monkeypatch.setattr(client._http, "request", capture)
    client.approve(key="ed25519:abc")
    assert called["url"].endswith("/v1/approve")
    assert called["json"] == {"key": "ed25519:abc"}


def test_sync_permissions(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"approved": [], "blocked": []})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.permissions()
    assert "approved" in result
    assert "blocked" in result


def test_sync_ping(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"agent_name": "bob", "address": "toq://h/bob", "public_key": "k", "reachable": True})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.ping("toq://h/bob")
    assert result["agent_name"] == "bob"
    assert result["reachable"] is True


def test_sync_handlers(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"handlers": [{"name": "h1", "command": "echo", "enabled": True, "active": 0}]})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.handlers()
    assert len(result) == 1
    assert result[0]["name"] == "h1"


def test_sync_add_handler(monkeypatch):
    client = toq.connect("http://localhost:9009")
    called = {}
    def capture(*a, **kw):
        called["json"] = kw.get("json")
        return MockResponse(json_data={"status": "added", "name": "test"})
    monkeypatch.setattr(client._http, "request", capture)
    result = client.add_handler("test", "echo hi", filter_from=["toq://host/*"])
    assert result["status"] == "added"
    assert called["json"]["name"] == "test"
    assert called["json"]["filter_from"] == ["toq://host/*"]


def test_sync_add_handler_llm(monkeypatch):
    client = toq.connect("http://localhost:9009")
    called = {}
    def capture(*a, **kw):
        called["json"] = kw.get("json")
        return MockResponse(json_data={"status": "added", "name": "chat"})
    monkeypatch.setattr(client._http, "request", capture)
    result = client.add_handler(
        "chat", provider="openai", model="gpt-4o",
        prompt="You are helpful", max_turns=5, auto_close=True,
    )
    assert result["status"] == "added"
    assert called["json"]["name"] == "chat"
    assert called["json"]["provider"] == "openai"
    assert called["json"]["model"] == "gpt-4o"
    assert called["json"]["prompt"] == "You are helpful"
    assert called["json"]["max_turns"] == 5
    assert called["json"]["auto_close"] is True
    assert "command" not in called["json"]


def test_sync_remove_handler(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"status": "removed", "name": "test"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.remove_handler("test")
    assert result["status"] == "removed"


def test_sync_update_handler(monkeypatch):
    client = toq.connect("http://localhost:9009")
    resp = MockResponse(json_data={"status": "updated", "name": "test"})
    monkeypatch.setattr(client._http, "request", lambda *a, **kw: resp)
    result = client.update_handler("test", enabled=False)
    assert result["status"] == "updated"


def test_sync_stop_handler(monkeypatch):
    client = toq.connect("http://localhost:9009")
    called = {}
    def capture(*a, **kw):
        called["json"] = kw.get("json")
        return MockResponse(json_data={"stopped": 2, "name": "test"})
    monkeypatch.setattr(client._http, "request", capture)
    result = client.stop_handler("test")
    assert result["stopped"] == 2
    assert called["json"]["name"] == "test"
    assert "pid" not in called["json"]


def test_sync_stop_handler_with_pid(monkeypatch):
    client = toq.connect("http://localhost:9009")
    called = {}
    def capture(*a, **kw):
        called["json"] = kw.get("json")
        return MockResponse(json_data={"stopped": 1, "name": "test"})
    monkeypatch.setattr(client._http, "request", capture)
    result = client.stop_handler("test", pid=12345)
    assert result["stopped"] == 1
    assert called["json"]["pid"] == 12345
