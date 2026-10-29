---
name: troubleshoot-nfltr
description: Diagnose nfltr problems in order (network path, service and online agents, orchestration readiness), read nfltr dial exit codes and error events, find nfltr logs, and update the CLI. Use when an nfltr command fails, a share link answers an error, a remote service or machine cannot be reached, or the user asks why nfltr is not working.
license: Apache-2.0
metadata:
  author: nfltr
  version: "0.1"
compatibility: Requires the nfltr CLI. Network access to nfltr.xyz.
---

# Troubleshoot nfltr

Run the checks in this order and stop at the first that fails. None of them changes anything.

## 1. Version

```bash
nfltr version
nfltr update --check
```

If an update exists, `nfltr update --apply` installs it (and updates `nfltr-orch` when it is installed next to `nfltr`; add `--with orch` to install it). Updates are verified against the signed release checksums; a binary that fails is left in place.

## 2. Can this machine reach nfltr.xyz?

```bash
nfltr diagnose
```

Checks DNS, TCP, TLS and the relay channel, and shows the effective keepalive setting. A failure here is the machine's network, proxy or firewall, not nfltr.

## 3. Is the service up, and which machines are online?

```bash
nfltr status
nfltr status --json
```

With a key it lists the account's agents online right now (nodes, shares, tunnels, listeners). If an expected machine is missing, the problem is on that machine: is its `nfltr` command still running, and does it use a key of the same account? `--require-api-key` makes it exit 1 when no key is available.

Key problems: `nfltr config check`, `nfltr config list` (never prints keys). Sign in again with `nfltr config login`.

## 4. Orchestration

```bash
nfltr orch doctor
nfltr orch nodes list
```

`nfltr orch doctor` prints one line with the fix for each problem: account, relay and key, `claude` installed and signed in, nodes. Common agent completions:

| Error | Meaning |
| --- | --- |
| `tools_not_allowed` | The node joined without `--allow-all-tools`; rejoin with it. |
| `no connected worker satisfies constraints` | No node matches the spawn's machine, labels or repository; check `nfltr orch nodes list`. |
| `node_lost` | The node stopped or lost its connection while the agent ran. |
| `budget_exceeded` | The hub's `--hub-max-tokens` / `--hub-max-usd` or the agent's budget was reached. |
| `clean Claude config not established` | Export `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` where the node runs. |
| `API key rejected by relay (HTTP 403)` | Save a valid key: `nfltr config add-api-key`, or set `NFLTR_API_KEY`. |

## nfltr dial exit codes

`nfltr dial` (and `connect:` mappings in `nfltr up`) report one JSON event per line on stderr; an `error` event's `code` matches the exit status:

| Exit | Code | Meaning |
| --- | --- | --- |
| 0 | | Session ended, both directions closed. |
| 1 | `usage` | Bad flags, target or config. |
| 2 | `auth` | No key, or the key was refused. |
| 3 | `not_found` | Agent offline or unknown for the whole `--open-timeout`, or the service is not declared. |
| 4 | `refused` | The agent or relay refused the session (target refused the connection, an E2EE policy, the service mode). |
| 5 | `unreachable` | Relay not reachable within `--open-timeout`, or the agent could not reach its target. |
| 6 | `reset` | Session reset after it opened; reason `drain_deadline` means a leaving relay's drain cut it. |
| 7 | `e2ee_pin_mismatch` | The agent's certificate is not the `--pin`, end-to-end TLS failed, or the service has no E2EE. |
| 8 | `parent_gone` | `--exit-with-parent` saw the parent exit. |

For 3, check the remote agent is running and the `<agent>/<service>` name matches its file; `--open-timeout 30s` waits longer for an agent that is restarting. For 7, take the fingerprint again from the remote `nfltr up` banner.

## Share link errors

| Answer | Meaning |
| --- | --- |
| `502` ... `connection refused` | Nothing listens on the local port. |
| `503` | The `nfltr http` command is not running or is reconnecting. |
| `401` | The share is protected; use its credentials. |
| `413` | Request bodies are limited to 1 GiB. |

## Logs

- Tunnel, share, dial and `nfltr up` commands log to their own stderr; `--verbose` on `nfltr http` and `nfltr tcp-connect` adds per-request or per-connection lines, and `nfltr up --log-format json` writes `connect:` events as JSON.
- A node logs to its stderr (`--log-level debug` for more) and keeps agent logs in its state directory: `--state-dir`, by default `nodes/<node id>/` under `$NFLTR_STATE_DIR`, else `$XDG_STATE_HOME/nfltr`, else `~/.local/state/nfltr`.
- An agent's turns and results: `nfltr orch hub runs`, then `nfltr orch hub show --hub-id HUB_ID AGENT_ID`.

When a connection drops slowly after a network change, a keepalive preset helps: `--keepalive fast|default|nat|datacenter|mobile` (or `NFLTR_KEEPALIVE`).

More: https://nfltr.xyz/docs/guides/diagnostics and https://nfltr.xyz/docs/guides/05-troubleshooting
