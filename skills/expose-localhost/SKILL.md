---
name: expose-localhost
description: Give a public HTTPS link to a web app, API or folder on this machine with nfltr http, or share text, a file or command output with nfltr share. Covers protecting the link (password, bearer token, IP allowlist, required header), its lifetime, and revoking it. Use when asked to expose, tunnel or share a local service, preview a dev server, or send someone a file or log as a link.
license: Apache-2.0
metadata:
  author: nfltr
  version: "0.1"
compatibility: Requires the nfltr CLI with a saved API key (see the setup skill).
---

# Expose localhost

`nfltr http` publishes a local HTTP service at a share URL (`https://<id>.nfltr.xyz/`). The link works while the command runs and stops when it stops. Visitors need only a browser or `curl`.

## Prerequisites

`nfltr version` works and a key is saved (`nfltr config login`, or `NFLTR_API_KEY`). Otherwise use the `setup` skill first.

## Share a local web app

```bash
nfltr http 8080
```

- Prints the **Share URL**, its access policy and its expiry. Leave it running; Ctrl+C revokes the link at once.
- The argument is a port, a full URL (`nfltr http https://myapp.local:3000`) or a directory to serve as a static site (`nfltr http ./public`).
- Default mode is end-to-end encrypted (verified): TLS ends on this machine, not on the relay.
- `--name <name>` sets the agent name. The link is tied to it: sharing again under the same name brings the same link back. Use a new name for a link the earlier recipients cannot reuse.
- `--no-share` connects without a public link.

Run it in the background (or a second terminal) when the agent needs to keep working, and tell the user the Share URL.

## Protect the link

Pick one; nfltr checks it before the request reaches the app.

| Flag | Visitors need |
| --- | --- |
| `--share-preset review` | Basic Auth credentials nfltr generates and prints |
| `--share-auth user:password` | your own Basic Auth credentials |
| `--share-bearer <token>` | `Authorization: Bearer <token>` (API clients) |
| `--share-ip-allowlist 203.0.113.0/24` | a source IP in the list (comma-separated) |
| `--share-header X-Api-Key=value` | that header (repeatable) |

Prefer `--share-preset review` when the user just wants a password: no secret is typed on the command line. `--share-auth` also reads `NFLTR_SHARE_AUTH` from the environment.

Lifetime: `--share-ttl 2h` (the relay may cap it). Without it the link expires after 24 hours or when the command stops.

## Dev servers that check the host

The app receives `Host` as the link's host name, plus `X-Forwarded-Host`, `X-Forwarded-Proto: https` and `X-Forwarded-For`. A dev server that rejects unknown hosts (Vite's allowed hosts, "Invalid Host header") either needs the link's host added, or:

```bash
nfltr http 5173 --host-header rewrite
```

## Share a file, text or command output

```bash
nfltr share ./crash.log                     # a file
nfltr share ./dist/                         # a directory listing
nfltr share "error: connection refused"     # text
git diff | nfltr share                      # stdin
nfltr share ./report.html --expire 30m      # ends after 30 minutes
```

`nfltr share` takes the same `--share-*` protection flags. `--json` prints `{share_id, url, expires_at, size_bytes}` for scripts.

## Several apps from one process

```yaml
# nfltr.yaml
services:
  web: { http: 3000 }
  api: { http: 8080, share_auth: "review:${API_PASS}" }
```

```bash
nfltr up -c nfltr.yaml
```

Each service takes its command's flags with `_` for `-`. Write secrets as `${ENV_VAR}`; a literal secret is refused unless the file is mode 600.

## When it fails

| Symptom | Fix |
| --- | --- |
| `502` with `connection refused` | Nothing listens on that port. Start the app or pass the right port. |
| `503` | The `nfltr http` command is not running (or is reconnecting). Start it again; the same link returns. |
| `401` | The link is protected; use the printed credentials. |
| `this session was replaced by a newer one` | Another command took the same name. Use a different `--name`. |
| `health server error: ... :29501 ... in use` | Harmless with two tunnels; `--health-addr :29502` moves it. |

More: https://nfltr.xyz/docs/guides/share-local-app
