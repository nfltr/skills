---
name: receive-webhooks
description: Receive webhooks from a third-party service (payments, Git hosting, chat, CI) on a local development server through an nfltr share URL, limited to the webhook path, with optional generated credentials, a short lifetime, a live request inspector, and capture and replay of the delivered requests. Use when asked to test, debug or receive webhooks or callbacks locally.
license: Apache-2.0
metadata:
  author: nfltr
  version: "0.1"
compatibility: Requires the nfltr CLI with a saved API key (see the setup skill).
---

# Receive webhooks

A webhook sender needs a public HTTPS URL. `nfltr http` gives the local handler one, for as long as the command runs.

## Prerequisites

The local handler runs (for example on port 8000 at `/github`), and nfltr is set up (`setup` skill).

## 1. Expose only the webhook path

```bash
nfltr http 8000 --allow-path /github --share-ttl 2h
```

- `--allow-path /github` forwards only requests under `/github` (repeatable); any other path gets `404` without reaching the handler. It turns off end-to-end TLS, because the agent must read each request's path.
- `--share-ttl 2h` ends the link after two hours (the relay may cap it); Ctrl+C ends it at once.
- Register `<Share URL>/github` (the printed Share URL plus the path) as the webhook URL with the sender.

Keep the command running (background or second terminal) while the sender delivers.

## 2. Gate the link (optional)

The handler should verify the sender's own signature in any case. To also keep everyone else off the link:

- `--share-preset webhook` makes a header-gated share with generated credentials, printed when the command starts. Use it when the sender can add a custom header to its deliveries.
- `--share-bearer <token>` or `--share-header Name=Value` when the sender can send that token or header.
- `--share-ip-allowlist <CIDRs>` when the sender publishes its source ranges.

Without one of these the link is public; `--allow-path` still limits it to the webhook path.

## 3. See what arrives

The inspector and capture need the relay-visible mode:

```bash
nfltr http 8000 --mode inspectable --allow-path /github --intercept
```

`--intercept` prints a summary of each request and response on stderr. `--record` writes every request and response to a capture file (`--record-file <file>` names it) for replay:

```bash
nfltr http 8000 --mode inspectable --allow-path /github --record --record-file hooks.json
nfltr replay hooks.json --target http://localhost:8000
nfltr replay hooks.json --target http://localhost:8000 --method POST --path /github --verbose
```

Replay re-sends the captured requests to the local handler, so a fix can be tested without asking the sender to deliver again. `--dry-run` lists them without sending.

## 4. Route a path to another local port (optional)

```bash
nfltr http 8080 --mode inspectable --route /hook=http://localhost:9000/github
```

The prefix is stripped and the rest appended: `/hook/x` goes to `/github/x` on port 9000.

## In a services file

```yaml
services:
  hook: { http: 9000, share_preset: webhook, allow_path: [/github] }
```

```bash
nfltr up -c nfltr.yaml
```

## When it fails

| Symptom | Fix |
| --- | --- |
| Sender reports `404` | The path is outside `--allow-path`; check the registered URL includes the path. |
| Sender reports `401` | The share is gated and the sender does not send the credential; use a gate the sender supports. |
| Sender reports `502` | The handler is not listening on that port. |
| Sender reports `503` | The `nfltr http` command is not running. |
| `Error: --intercept read requests, which end-to-end TLS hides` | Add `--mode inspectable` (the relay then sees the traffic). `--record` needs it too. |

More: https://nfltr.xyz/docs/features/http-tunnels
