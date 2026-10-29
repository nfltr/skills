---
name: setup
description: Install the nfltr CLI, sign in to nfltr.xyz and save an API key, and manage saved keys with nfltr config. Use when nfltr is not installed, when a command says no API key is available or the key was refused, or before any other nfltr skill on a new machine.
license: Apache-2.0
metadata:
  author: nfltr
  version: "0.1"
compatibility: macOS or Linux (amd64, arm64) with curl. Network access to nfltr.xyz.
---

# Set up nfltr

nfltr connects services and machines through the relay at nfltr.xyz. One CLI, `nfltr`, does tunnels and shares; a second binary, `nfltr-orch`, runs the agent commands (`nfltr orch`, `nfltr node`, `nfltr mcp`, `nfltr start`) and is found next to `nfltr`.

## 1. Check what is installed

```bash
nfltr version
```

If the command is missing, install it. If it prints a version, skip to step 3.

## 2. Install

Tunnels and shares only:

```bash
curl -fsSL https://nfltr.xyz/install.sh | sh
```

With the agent commands as well (needed for the `run-agents-on-your-machines` skill):

```bash
curl -fsSL https://nfltr.xyz/install.sh | sh -s -- --with orch
```

- The installer puts the binaries in `~/.local/bin` (`NFLTR_INSTALL_DIR` changes it). If that directory is not on `PATH`, it prints the `export` line to add.
- It verifies the release signature and checksum before installing, and refuses a binary that fails either check.
- Windows and other platforms: https://nfltr.xyz/install

To add `nfltr-orch` later, or to update both binaries:

```bash
nfltr update --apply --with orch
```

## 3. Sign in and save a key

On a machine with a browser:

```bash
nfltr config login
```

This opens a browser sign-in and saves a new API key as the active key in the nfltr config file (mode 0600). The key is never printed.

On a machine without a browser, create a key in the dashboard (https://nfltr.xyz/dashboard, Account → API keys; it is shown once) and save it. The command prompts without echo:

```bash
nfltr config add-api-key
```

Alternatively, set `NFLTR_API_KEY` in the environment. Never put a key on the command line: other users on the machine can read process arguments. Never print a key, and never commit it.

## 4. Check the setup

```bash
nfltr config check
nfltr status
```

`nfltr status` reports whether the relay answers and, with a key, which of the account's agents are online.

## Several keys

```bash
nfltr config add-api-key --name work   # save another key under a label
nfltr config list-api-keys             # labels, never the keys
nfltr config use-api-key work          # switch the active key
nfltr config remove-api-key work
nfltr config path                      # where the config file is
```

Most commands also take `--key-name <label>` to use a saved key for one run.

More: https://nfltr.xyz/docs/guides/00-getting-started
