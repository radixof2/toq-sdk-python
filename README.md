# toq SDK for Python

Python SDK for [toq protocol](https://github.com/toqprotocol/toq). Thin async client to the local toq daemon.

## Install

```
pip install toq
```

## Prerequisites

1. Install the toq binary
2. Run `toq setup`
3. Run `toq up`

## Usage

```python
import toq

client = toq.connect()

# Send a message
response = await client.send("toq://peer.example.com/agent", "hello")

# Receive messages
async for msg in client.messages():
    print(f"From {msg.sender}: {msg.body}")
    await msg.reply("got it")

# Check status
status = await client.status()
print(status["address"])
```

## API

All methods are async. See `toq.Client` for the full list.

| Method | Description |
|--------|-------------|
| `send(to, text)` | Send a message |
| `messages()` | Stream incoming messages (SSE) |
| `peers()` | List known peers |
| `block(key)` / `unblock(key)` | Block/unblock an agent |
| `approvals()` | List pending approvals |
| `approve(id)` / `deny(id)` | Resolve an approval |
| `discover(host)` | DNS discovery |
| `status()` | Daemon status |
| `config()` / `update_config()` | Read/update config |
| `card()` | Get agent card |
| `rotate_keys()` | Rotate identity keys |
| `export_backup(passphrase)` | Create encrypted backup |
| `import_backup(passphrase, data)` | Restore from backup |

## License

Apache 2.0
