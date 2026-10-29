---
name: private-service-access
description: Reach a private TCP service (database, SSH, gRPC, internal API) on another machine without opening ports, using nfltr up services on the remote side and nfltr tcp-connect, nfltr dial or connect mappings on the local side, optionally end-to-end encrypted with a certificate pin. Use when asked to connect to a database, SSH host or service behind NAT or a firewall, or to wire a program to a remote service through nfltr.
license: Apache-2.0
metadata:
  author: nfltr
  version: "0.1"
compatibility: Requires the nfltr CLI on both machines, each with an API key of the same account (see the setup skill).
---

# Private service access

Two sides, one account:

- **The machine with the service** runs an agent that publishes it: `nfltr up` with `tcp:` services (or `nfltr tcp <port>` for one port). It accepts no inbound connections; it dials out to the relay.
- **The machine that needs the service** opens sessions to it: `nfltr tcp-connect` (a local listener), `nfltr dial` (one session on stdin/stdout), or `connect:` mappings in an `nfltr up` file (local endpoints that stay up).

Nothing is published on the internet: only the account's own keys can open sessions.

## 1. Publish services (remote machine)

```yaml
# home.yaml
agent: home
services:
  db:  { tcp: 5432 }
  ssh: { tcp: 22 }
```

```bash
nfltr up -c home.yaml
```

With `agent:`, every service is reached as `<agent>/<service>` (`home/db`) over one connection, and the agent dials only the targets the file lists. A tcp service may name another host with `forward:` instead of localhost.

`nfltr up` prints the agent's E2EE certificate fingerprint in its banner; keep it for step 3.

For a single port without a file:

```bash
nfltr tcp 5432 --name my-db
```

## 2. Connect (local machine)

A local listener any client can use:

```bash
nfltr tcp-connect home/db --listen :5432
psql -h localhost -p 5432
```

A host-less `:PORT` binds 127.0.0.1. `--listen` also takes `unix:<path>` (a 0600 socket) or, on Windows, `pipe:<name>`. For a single-port agent: `nfltr tcp-connect my-db 5432 --listen :5432`.

One session on stdin/stdout, for scripts and SSH:

```bash
nfltr dial home/db < query.bin > answer.bin
ssh -o ProxyCommand="nfltr dial %h 22" user@my-ssh
```

`nfltr dial` writes one JSON event per line on stderr (`open`, `close`, `error`) and exits with a code that says what happened (see the `troubleshoot-nfltr` skill).

Persistent local endpoints for a program, in an `nfltr up` file:

```yaml
# app.yaml
connect:
  db: { target: home/db, listen: "127.0.0.1:5432" }
status: "127.0.0.1:7801"
```

```bash
nfltr up -c app.yaml
```

Each connection to a mapping is one session to its target. The endpoint stays up while the remote is offline; a connection that cannot open is closed with an error event. A file may hold `services:`, `connect:` or both. When a program starts nfltr as a sidecar, add `--exit-with-parent --log-format json`.

## 3. End-to-end encryption with a pin

Without a pin, sessions are TLS to the relay only (`"e2ee": false` in events and `/status`): the relay could read them unless the application runs its own TLS. With the fingerprint an `nfltr up` agent printed in step 1, the session is TLS with the agent itself and the relay carries only ciphertext:

```bash
nfltr tcp-connect home/db --pin <agent-fingerprint> --listen :5432
nfltr dial home/db --pin <agent-fingerprint> < req.bin > resp.bin
```

In a `connect:` mapping the key is `pin:`. A mismatch, or a service without E2EE, fails the session (`nfltr dial` exits 7). Get the fingerprint from the remote side's own output, never from a third party.

## Keys

`nfltr dial` and `nfltr up` read the key from `--api-key-file` (or `NFLTR_API_KEY_FILE`), else `NFLTR_API_KEY`, else the saved config. Never put a key on the command line.

More: https://nfltr.xyz/docs/guides/ssh-behind-nat and https://nfltr.xyz/docs/features/tcp-ssh-tunneling
