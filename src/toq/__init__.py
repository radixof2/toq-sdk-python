"""toq protocol Python SDK.

Thin client to the local toq daemon. The daemon handles all protocol
complexity (crypto, TLS, handshake, connections). This SDK provides
sync and async interfaces for agent code.

Sync usage:
    import toq
    client = toq.connect()
    client.send("toq://peer.com/agent", "hello")

Async usage:
    import toq
    client = toq.connect_async()
    await client.send("toq://peer.com/agent", "hello")
    async for msg in client.messages():
        await msg.reply("got it")
"""

from toq._client import AsyncClient, Client, Message, ToqError, connect, connect_async

__all__ = ["AsyncClient", "Client", "Message", "ToqError", "connect", "connect_async"]
