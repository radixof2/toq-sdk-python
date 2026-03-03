"""toq SDK client implementation."""

import json
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import httpx
import httpx_sse

DEFAULT_URL = "http://127.0.0.1:9010"
URL_ENV = "TOQ_API_URL"
DAEMON_NOT_RUNNING = "toq daemon is not running. Run 'toq up' first."


class ToqError(Exception):
    """Raised when the SDK cannot communicate with the daemon."""


def connect(url: Optional[str] = None) -> "Client":
    """Connect to the local toq daemon (sync)."""
    resolved = url or os.environ.get(URL_ENV, DEFAULT_URL)
    return Client(resolved)


def connect_async(url: Optional[str] = None) -> "AsyncClient":
    """Connect to the local toq daemon (async)."""
    resolved = url or os.environ.get(URL_ENV, DEFAULT_URL)
    return AsyncClient(resolved)


# ── Sync Client ──────────────────────────────────────────


class Client:
    """Sync client to the local toq daemon API."""

    def __init__(self, base_url: str) -> None:
        self._url = base_url.rstrip("/")
        self._http = httpx.Client(base_url=self._url, timeout=60)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = self._http.request(method, path, **kwargs)
        except httpx.ConnectError as exc:
            raise ToqError(DAEMON_NOT_RUNNING) from exc
        resp.raise_for_status()
        return resp

    # ── Messages ─────────────────────────────────────────

    def send(
        self,
        to: str,
        text: str,
        *,
        thread_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        wait: bool = True,
        timeout: int = 30,
    ) -> dict:
        """Send a message to a remote agent."""
        body: dict = {"to": to, "body": {"text": text}}
        if thread_id:
            body["thread_id"] = thread_id
        if reply_to:
            body["reply_to"] = reply_to
        resp = self._request(
            "POST",
            "/v1/messages",
            json=body,
            params={"wait": str(wait).lower(), "timeout": timeout},
        )
        return resp.json()

    # ── Peers ────────────────────────────────────────────

    def peers(self) -> list:
        return self._request("GET", "/v1/peers").json()["peers"]

    def block(self, public_key: str) -> None:
        self._request("POST", "/v1/peers/%s/block" % public_key)

    def unblock(self, public_key: str) -> None:
        self._request("DELETE", "/v1/peers/%s/block" % public_key)

    # ── Approvals ────────────────────────────────────────

    def approvals(self) -> list:
        return self._request("GET", "/v1/approvals").json()["approvals"]

    def approve(self, approval_id: str) -> None:
        self._request(
            "POST", "/v1/approvals/%s" % approval_id, json={"decision": "approve"}
        )

    def deny(self, approval_id: str) -> None:
        self._request(
            "POST", "/v1/approvals/%s" % approval_id, json={"decision": "deny"}
        )

    # ── Discovery ────────────────────────────────────────

    def discover(self, host: str) -> list:
        return self._request("GET", "/v1/discover", params={"host": host}).json()["agents"]

    def discover_local(self) -> list:
        return self._request("GET", "/v1/discover/local").json()["agents"]

    # ── Daemon ───────────────────────────────────────────

    def health(self) -> str:
        return self._request("GET", "/v1/health").text

    def status(self) -> dict:
        return self._request("GET", "/v1/status").json()

    def shutdown(self, graceful: bool = True) -> None:
        self._request("POST", "/v1/daemon/shutdown", json={"graceful": graceful})

    def logs(self) -> list:
        return self._request("GET", "/v1/logs").json()["entries"]

    def clear_logs(self) -> None:
        self._request("DELETE", "/v1/logs")

    def diagnostics(self) -> dict:
        return self._request("GET", "/v1/diagnostics").json()

    def check_upgrade(self) -> dict:
        return self._request("GET", "/v1/upgrade/check").json()

    # ── Connections ──────────────────────────────────────

    def connections(self) -> list:
        return self._request("GET", "/v1/connections").json()["connections"]

    # ── Keys ─────────────────────────────────────────────

    def rotate_keys(self) -> dict:
        return self._request("POST", "/v1/keys/rotate").json()

    # ── Backup ───────────────────────────────────────────

    def export_backup(self, passphrase: str) -> str:
        return self._request(
            "POST", "/v1/backup/export", json={"passphrase": passphrase}
        ).json()["data"]

    def import_backup(self, passphrase: str, data: str) -> None:
        self._request(
            "POST", "/v1/backup/import", json={"passphrase": passphrase, "data": data}
        )

    # ── Config ───────────────────────────────────────────

    def config(self) -> dict:
        return self._request("GET", "/v1/config").json()["config"]

    def update_config(self, **updates: Any) -> dict:
        return self._request("PATCH", "/v1/config", json=updates).json()["config"]

    # ── Agent Card ───────────────────────────────────────

    def card(self) -> dict:
        return self._request("GET", "/v1/card").json()


# ── Message ──────────────────────────────────────────────


@dataclass
class Message:
    """An incoming message from a remote agent."""

    id: str
    type: str
    sender: str
    body: Any
    thread_id: Optional[str]
    reply_to: Optional[str]
    content_type: Optional[str]
    timestamp: str
    _client: "AsyncClient"

    async def reply(self, text: str) -> dict:
        """Reply to this message."""
        return await self._client.send(
            self.sender, text, thread_id=self.thread_id, reply_to=self.id
        )


# ── Async Client ─────────────────────────────────────────


class AsyncClient:
    """Async client to the local toq daemon API."""

    def __init__(self, base_url: str) -> None:
        self._url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(base_url=self._url, timeout=60)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = await self._http.request(method, path, **kwargs)
        except httpx.ConnectError as exc:
            raise ToqError(DAEMON_NOT_RUNNING) from exc
        resp.raise_for_status()
        return resp

    # ── Messages ─────────────────────────────────────────

    async def send(
        self,
        to: str,
        text: str,
        *,
        thread_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        wait: bool = True,
        timeout: int = 30,
    ) -> dict:
        """Send a message to a remote agent."""
        body: dict = {"to": to, "body": {"text": text}}
        if thread_id:
            body["thread_id"] = thread_id
        if reply_to:
            body["reply_to"] = reply_to
        resp = await self._request(
            "POST",
            "/v1/messages",
            json=body,
            params={"wait": str(wait).lower(), "timeout": timeout},
        )
        return resp.json()

    async def messages(self) -> AsyncIterator[Message]:
        """Stream incoming messages via SSE (async only)."""
        async with httpx_sse.aconnect_sse(
            self._http, "GET", "/v1/messages"
        ) as source:
            async for event in source.aiter_sse():
                if not event.data:
                    continue
                data = json.loads(event.data)
                yield Message(
                    id=data["id"],
                    type=data["type"],
                    sender=data["from"],
                    body=data.get("body"),
                    thread_id=data.get("thread_id"),
                    reply_to=data.get("reply_to"),
                    content_type=data.get("content_type"),
                    timestamp=data["timestamp"],
                    _client=self,
                )

    # ── Peers ────────────────────────────────────────────

    async def peers(self) -> list:
        return (await self._request("GET", "/v1/peers")).json()["peers"]

    async def block(self, public_key: str) -> None:
        await self._request("POST", "/v1/peers/%s/block" % public_key)

    async def unblock(self, public_key: str) -> None:
        await self._request("DELETE", "/v1/peers/%s/block" % public_key)

    # ── Approvals ────────────────────────────────────────

    async def approvals(self) -> list:
        return (await self._request("GET", "/v1/approvals")).json()["approvals"]

    async def approve(self, approval_id: str) -> None:
        await self._request(
            "POST", "/v1/approvals/%s" % approval_id, json={"decision": "approve"}
        )

    async def deny(self, approval_id: str) -> None:
        await self._request(
            "POST", "/v1/approvals/%s" % approval_id, json={"decision": "deny"}
        )

    # ── Discovery ────────────────────────────────────────

    async def discover(self, host: str) -> list:
        return (await self._request("GET", "/v1/discover", params={"host": host})).json()["agents"]

    async def discover_local(self) -> list:
        return (await self._request("GET", "/v1/discover/local")).json()["agents"]

    # ── Daemon ───────────────────────────────────────────

    async def health(self) -> str:
        return (await self._request("GET", "/v1/health")).text

    async def status(self) -> dict:
        return (await self._request("GET", "/v1/status")).json()

    async def shutdown(self, graceful: bool = True) -> None:
        await self._request("POST", "/v1/daemon/shutdown", json={"graceful": graceful})

    async def logs(self) -> list:
        return (await self._request("GET", "/v1/logs")).json()["entries"]

    async def clear_logs(self) -> None:
        await self._request("DELETE", "/v1/logs")

    async def diagnostics(self) -> dict:
        return (await self._request("GET", "/v1/diagnostics")).json()

    async def check_upgrade(self) -> dict:
        return (await self._request("GET", "/v1/upgrade/check")).json()

    # ── Connections ──────────────────────────────────────

    async def connections(self) -> list:
        return (await self._request("GET", "/v1/connections")).json()["connections"]

    # ── Keys ─────────────────────────────────────────────

    async def rotate_keys(self) -> dict:
        return (await self._request("POST", "/v1/keys/rotate")).json()

    # ── Backup ───────────────────────────────────────────

    async def export_backup(self, passphrase: str) -> str:
        return (await self._request(
            "POST", "/v1/backup/export", json={"passphrase": passphrase}
        )).json()["data"]

    async def import_backup(self, passphrase: str, data: str) -> None:
        await self._request(
            "POST", "/v1/backup/import", json={"passphrase": passphrase, "data": data}
        )

    # ── Config ───────────────────────────────────────────

    async def config(self) -> dict:
        return (await self._request("GET", "/v1/config")).json()["config"]

    async def update_config(self, **updates: Any) -> dict:
        return (await self._request("PATCH", "/v1/config", json=updates)).json()["config"]

    # ── Agent Card ───────────────────────────────────────

    async def card(self) -> dict:
        return (await self._request("GET", "/v1/card")).json()
