"""toq SDK client implementation."""

import json
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import httpx
import httpx_sse

DEFAULT_URL = "http://127.0.0.1:9010"
URL_ENV = "TOQ_API_URL"


def connect(url: Optional[str] = None) -> "Client":
    """Connect to the local toq daemon."""
    resolved = url or os.environ.get(URL_ENV, DEFAULT_URL)
    return Client(resolved)


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
    _client: "Client"

    async def reply(self, text: str) -> dict:
        """Reply to this message."""
        return await self._client.send(
            self.sender, text, thread_id=self.thread_id, reply_to=self.id
        )


class Client:
    """Async client to the local toq daemon API."""

    def __init__(self, base_url: str) -> None:
        self._url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(base_url=self._url, timeout=60)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

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
        resp = await self._http.post(
            "/v1/messages",
            json=body,
            params={"wait": str(wait).lower(), "timeout": timeout},
        )
        resp.raise_for_status()
        return resp.json()

    async def messages(self) -> AsyncIterator[Message]:
        """Stream incoming messages via SSE."""
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
        resp = await self._http.get("/v1/peers")
        resp.raise_for_status()
        return resp.json()["peers"]

    async def block(self, public_key: str) -> None:
        resp = await self._http.post("/v1/peers/%s/block" % public_key)
        resp.raise_for_status()

    async def unblock(self, public_key: str) -> None:
        resp = await self._http.delete("/v1/peers/%s/block" % public_key)
        resp.raise_for_status()

    # ── Approvals ────────────────────────────────────────

    async def approvals(self) -> list:
        resp = await self._http.get("/v1/approvals")
        resp.raise_for_status()
        return resp.json()["approvals"]

    async def approve(self, approval_id: str) -> None:
        resp = await self._http.post(
            "/v1/approvals/%s" % approval_id, json={"decision": "approve"}
        )
        resp.raise_for_status()

    async def deny(self, approval_id: str) -> None:
        resp = await self._http.post(
            "/v1/approvals/%s" % approval_id, json={"decision": "deny"}
        )
        resp.raise_for_status()

    # ── Discovery ────────────────────────────────────────

    async def discover(self, host: str) -> list:
        resp = await self._http.get("/v1/discover", params={"host": host})
        resp.raise_for_status()
        return resp.json()["agents"]

    async def discover_local(self) -> list:
        resp = await self._http.get("/v1/discover/local")
        resp.raise_for_status()
        return resp.json()["agents"]

    # ── Daemon ───────────────────────────────────────────

    async def health(self) -> str:
        resp = await self._http.get("/v1/health")
        resp.raise_for_status()
        return resp.text

    async def status(self) -> dict:
        resp = await self._http.get("/v1/status")
        resp.raise_for_status()
        return resp.json()

    async def shutdown(self, graceful: bool = True) -> None:
        resp = await self._http.post(
            "/v1/daemon/shutdown", json={"graceful": graceful}
        )
        resp.raise_for_status()

    async def logs(self) -> list:
        resp = await self._http.get("/v1/logs")
        resp.raise_for_status()
        return resp.json()["entries"]

    async def clear_logs(self) -> None:
        resp = await self._http.delete("/v1/logs")
        resp.raise_for_status()

    async def diagnostics(self) -> dict:
        resp = await self._http.get("/v1/diagnostics")
        resp.raise_for_status()
        return resp.json()

    async def check_upgrade(self) -> dict:
        resp = await self._http.get("/v1/upgrade/check")
        resp.raise_for_status()
        return resp.json()

    # ── Connections ──────────────────────────────────────

    async def connections(self) -> list:
        resp = await self._http.get("/v1/connections")
        resp.raise_for_status()
        return resp.json()["connections"]

    # ── Keys ─────────────────────────────────────────────

    async def rotate_keys(self) -> dict:
        resp = await self._http.post("/v1/keys/rotate")
        resp.raise_for_status()
        return resp.json()

    # ── Backup ───────────────────────────────────────────

    async def export_backup(self, passphrase: str) -> str:
        resp = await self._http.post(
            "/v1/backup/export", json={"passphrase": passphrase}
        )
        resp.raise_for_status()
        return resp.json()["data"]

    async def import_backup(self, passphrase: str, data: str) -> None:
        resp = await self._http.post(
            "/v1/backup/import", json={"passphrase": passphrase, "data": data}
        )
        resp.raise_for_status()

    # ── Config ───────────────────────────────────────────

    async def config(self) -> dict:
        resp = await self._http.get("/v1/config")
        resp.raise_for_status()
        return resp.json()["config"]

    async def update_config(self, **updates: Any) -> dict:
        resp = await self._http.patch("/v1/config", json=updates)
        resp.raise_for_status()
        return resp.json()["config"]

    # ── Agent Card ───────────────────────────────────────

    async def card(self) -> dict:
        resp = await self._http.get("/v1/card")
        resp.raise_for_status()
        return resp.json()
