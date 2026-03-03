"""toq protocol Python SDK.

Thin client to the local toq daemon. The daemon handles all protocol
complexity (crypto, TLS, handshake, connections). This SDK provides
a clean async interface for agent code.

Usage:
    import toq

    client = toq.connect()
    response = await client.send("toq://peer.com/agent", "hello")

    async for msg in client.messages():
        await msg.reply("got it")
"""

from toq._client import Client, Message, ToqError, connect

__all__ = ["Client", "Message", "ToqError", "connect"]
