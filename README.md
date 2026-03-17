<p align="center">
  <strong>toq SDK for Python</strong>
</p>

<p align="center">
  Python client for <a href="https://github.com/toqprotocol/toq">toq protocol</a>. Sync and async. Thin wrapper around the local daemon API.
</p>

<p align="center">
  <a href="https://github.com/toqprotocol/toq-sdk-python/actions"><img src="https://github.com/toqprotocol/toq-sdk-python/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/toq/"><img src="https://img.shields.io/pypi/v/toq.svg" alt="PyPI"></a>
  <a href="https://github.com/toqprotocol/toq-sdk-python/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/toq/"><img src="https://img.shields.io/pypi/pyversions/toq.svg" alt="Python"></a>
</p>

---

## Install

```bash
pip install toq
```

Requires Python 3.9+. Dependencies: `httpx`, `httpx-sse`.

## Prerequisites

1. Install the [toq binary](https://github.com/toqprotocol/toq)
2. Run `toq setup`
3. Run `toq up`

## Quick Start

### Sync

```python
import toq

client = toq.connect()

# Send a message
resp = client.send("toq://192.168.1.50/bob", "Hey, are you available?")
print(resp["thread_id"])

# Check status
status = client.status()
print(status["address"])  # toq://192.168.1.50/alice

# List peers
for peer in client.peers():
    print(f"{peer['address']} - {peer['status']}")

# Message history
for msg in client.history(limit=10):
    print(f"[{msg['timestamp']}] {msg['from']}: {msg['body']['text']}")
```

### Async

```python
import toq

client = toq.connect_async()

# Send
await client.send("toq://192.168.1.50/bob", "Hello from async")

# Stream incoming messages (async only)
async for msg in client.messages():
    print(f"From {msg.sender}: {msg.body}")
    await msg.reply("Got it")
```

SSE message streaming (`messages()`) is async only.

### Streaming Delivery

```python
client = toq.connect()

# Send text word-by-word for real-time display
stream = client.stream_start("toq://192.168.1.50/bob")
for word in "Hello from a streaming message".split():
    client.stream_chunk(stream["stream_id"], word + " ")
client.stream_end(stream["stream_id"])
```

## URL Resolution

`toq.connect()` resolves the daemon URL in this order:

1. Explicit URL: `toq.connect("http://127.0.0.1:9009")`
2. `TOQ_URL` environment variable
3. `.toq/state.json` in the current directory
4. `~/.toq/state.json`
5. Default: `http://127.0.0.1:9009`

## API

Both `Client` (sync) and `AsyncClient` (async) expose the same methods.

| Method | Description |
|--------|-------------|
| `send(to, text)` | Send a message |
| `messages()` | Stream incoming messages (async only) |
| `stream_start(to)` | Open a streaming connection |
| `stream_chunk(id, text)` | Send a stream chunk |
| `stream_end(id)` | End a stream |
| `get_thread(thread_id)` | Get messages in a thread |
| `peers()` | List known peers |
| `block(key)` / `unblock(key)` | Block/unblock by key or address |
| `approvals()` | List pending approvals |
| `approve(id)` / `deny(id)` | Resolve an approval |
| `revoke(id)` | Revoke an approved rule |
| `permissions()` | List all permission rules |
| `ping(address)` | Ping a remote agent |
| `history(limit)` | Query message history |
| `discover(host)` | DNS-based discovery |
| `discover_local()` | mDNS/LAN discovery |
| `connections()` | List active connections |
| `status()` / `health()` | Daemon status |
| `shutdown()` | Stop the daemon |
| `logs()` / `clear_logs()` | Read/clear logs |
| `diagnostics()` | Run diagnostics |
| `check_upgrade()` | Check for updates |
| `rotate_keys()` | Rotate identity keys |
| `export_backup(passphrase)` | Create encrypted backup |
| `import_backup(passphrase, data)` | Restore from backup |
| `config()` / `update_config()` | Read/update config |
| `card()` | Get agent card |
| `handlers()` | List message handlers |
| `add_handler(name, command)` | Register a handler |
| `remove_handler(name)` | Remove a handler |
| `stop_handler(name)` | Stop handler processes |

## Framework Plugins

For LangChain or CrewAI integration, see [toq-plugins](https://github.com/toqprotocol/toq-plugins).

## License

Apache 2.0
