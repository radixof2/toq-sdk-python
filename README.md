# toq SDK for Python

Python SDK for [toq protocol](https://github.com/toqprotocol/toq). Thin client to the local toq daemon.

## Install

```
pip install toq
```

## Prerequisites

1. Install the toq binary
2. Run `toq setup`
3. Run `toq up`

## Usage

### Sync (default)

```python
import toq

client = toq.connect()
client.send("toq://peer.example.com/agent", "hello")

status = client.status()
print(status["address"])
```

### Async

```python
import toq

client = toq.connect_async()
await client.send("toq://peer.example.com/agent", "hello")

async for msg in client.messages():
    print(f"From {msg.sender}: {msg.body}")
    await msg.reply("got it")
```

SSE streaming (`messages()`) is async only.

## API

Both `Client` (sync) and `AsyncClient` (async) have the same methods.

| Method | Description |
|--------|-------------|
| `send(to, text)` | Send a message |
| `messages()` | Stream incoming messages (async only) |
| `cancel_message(id)` | Cancel a sent message |
| `send_streaming(to, text)` | Streaming delivery |
| `get_thread(thread_id)` | Get messages in a thread |
| `peers()` | List known peers |
| `block(key)` / `unblock(key)` | Block/unblock an agent |
| `approvals()` | List pending approvals |
| `approve(id)` / `deny(id)` | Resolve an approval |
| `discover(host)` | DNS discovery |
| `discover_local()` | mDNS/LAN discovery |
| `connections()` | List active connections |
| `status()` | Daemon status |
| `health()` | Health check |
| `shutdown()` | Stop the daemon |
| `logs()` / `clear_logs()` | Read/clear logs |
| `logs(follow=True)` | Stream logs in real time (async only) |
| `diagnostics()` | Run diagnostics |
| `check_upgrade()` | Check for updates |
| `rotate_keys()` | Rotate identity keys |
| `export_backup(passphrase)` | Create encrypted backup |
| `import_backup(passphrase, data)` | Restore from backup |
| `config()` / `update_config()` | Read/update config |
| `card()` | Get agent card |

## License

Apache 2.0
