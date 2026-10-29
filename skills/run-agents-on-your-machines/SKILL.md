---
name: run-agents-on-your-machines
description: Run Claude Code agents on the user's own laptops, VMs and servers from this Claude Code session through the nfltr hub tools. Covers adding the hub MCP server, joining machines as nodes, spawning, steering and collecting agents, and owner approvals for changes. Use when asked to run work on another machine, fan work out to several machines, set up nfltr orchestration or nodes, or approve an agent's change.
license: Apache-2.0
metadata:
  author: nfltr
  version: "0.1"
compatibility: Requires the nfltr CLI installed with --with orch and a saved API key on every machine, and Claude Code (claude) on every machine that runs agents.
---

# Run agents on your machines

With the nfltr hub tools, this Claude Code session is the hub: it starts Claude Code agents on machines joined to the user's account (nodes), messages them, stops them and collects their results. The relay at nfltr.xyz carries the messages and runs no model; every decision is the hub's.

## Prerequisites

- `nfltr` and `nfltr-orch` on every machine: `curl -fsSL https://nfltr.xyz/install.sh | sh -s -- --with orch` (`setup` skill).
- A saved key on every machine (`nfltr config login`), all of the same account.
- On each machine that runs agents: `claude` installed, and `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) or `ANTHROPIC_API_KEY` in the environment the node runs in. Agents run with a clean Claude config, so a keychain-only login is not used.

## The fastest start: one command per machine

```bash
nfltr start
```

It checks the machine (each problem is one line with its fix; nothing changes until all pass), joins it as a node whose agents read freely but run commands or change files only in a turn the owner approved, runs a first read-only task, and prints the line to run on the next machine. It writes the owner's approval key and the node policy once, in the nfltr config directory.

## Manual setup

### 1. Join each machine as a node

```bash
nfltr node join --max-agents 2 --allow-all-tools \
  --allow-repo 'github.com/your-org/*' \
  --machine-description "build box with the nightly dataset in /data"
```

- A long-running process; keep it under a service manager, tmux or screen.
- `--allow-all-tools` lets agents run shell commands. Without it they may only edit files, and other calls end as `tools_not_allowed`.
- `--allow-repo <glob>` names repositories a spawn may name here (needs `--allow-all-tools`). The agent clones and pushes itself.
- `--machine-description` and `--labels key=value` tell the hub what only this machine has, so a goal can say "on the machine with the dataset".

```bash
nfltr orch nodes list    # nodes of the account
nfltr orch nodes stop    # stop this machine's node
```

### 2. Add the hub tools to Claude Code

In the project directory:

```bash
claude mcp add nfltr -- nfltr mcp --toolset hub
nfltr orch hub install-hook --prefer-agents
nfltr orch doctor
```

- The hub id is one per project directory; reopening the project reattaches the hub and delivers every completion it missed, exactly once. A second session in the same project needs its own `--hub-id`.
- `install-hook` adds hooks to `.claude/settings.local.json` that wake the session when an agent completes. `--prefer-agents` records that code work should go to agents on the nodes rather than this session's own tools.
- Spend caps are opt-in: add `--hub-max-tokens N` (and `--hub-max-usd X`, which needs it) to the `nfltr mcp` command.
- `nfltr orch doctor` prints one line with the fix for each problem (account, relay, `claude`, nodes).
- No account: `claude mcp add nfltr -- nfltr orch hub --max-agents 2` runs a local hub and node on this machine only.

Allow the tools once with `/permissions` (add `mcp__nfltr`) or start with `claude --allowedTools mcp__nfltr`.

## Using the hub tools

1. `list_nodes`: which machines are joined, their labels, descriptions, load and free agent slots.
2. `spawn_agent` with a complete brief (`prompt`; the agent sees only the brief and its own checkout) and optional `constraints`:
   - `machine` (with `pin` `hard` or `soft`) or `labels` to choose where it runs;
   - `workspace: {repo, ref}` for a repository the node allows; `mutates_workspace: true` when it should edit;
   - `timeout_ms` to bound the turn; `budget` to cap its tokens;
   - `output_validation` when the next step depends on fields of its result (for example `branch_ref` and `sha`).
   `spawn_agents` starts several at once.
3. `wait_for_agents` returns completions (each exactly once); `list_agents` shows what runs where.
4. `send_message` steers a running agent or continues a finished one; `stop_agent` cancels a turn.

An agent that edits a repository commits and pushes a branch; the branch and commit in its result are what to review. Work it did not push is removed with its task directory.

## Approvals

On a node joined by `nfltr start`, or with `--approval-public-key` and a tool policy whose rules are marked `unless_approved`, an agent's command or edit is refused until the owner approves that exact prompt on that node. The hub asks with `request_approval` and shows the node, the prompt and its SHA-256. The owner signs it in the same project directory:

```bash
nfltr orch hub approve --key-file ~/.config/nfltr/approval.key --ttl 15m
```

The printed grant goes back to the hub (paste it into the session), which spawns the same prompt with `constraints.approval`. The node checks the grant: valid once, for that prompt on that node, until it expires. The approval key must stay with the owner; never copy it to a node, and never print it.

To make an approval key pair for a manual setup: `nfltr orch hub approval-key --out <file>`.

## Watching from a terminal

```bash
nfltr orch hub runs                       # this machine's hubs and their agents
nfltr orch hub show --hub-id HUB_ID AGENT_ID
nfltr orch task list --active
```

More: https://nfltr.xyz/docs/guides/claude-code, https://nfltr.xyz/docs/guides/nodes and https://nfltr.xyz/docs/hub-tools
