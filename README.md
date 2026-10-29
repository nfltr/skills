<p align="center"><img src="docs/logo.svg" width="96" height="96" alt="nfltr"></p>

# nfltr skills

[Agent Skills](https://agentskills.io/) for [nfltr](https://nfltr.xyz): expose local services, reach private services, receive webhooks, and run Claude Code agents on your own machines. The repository is a standalone skill pack and a Claude Code plugin.

## Install

Any Agent Skills compatible agent:

```bash
npx skills add nfltr/skills
```

Claude Code, as a plugin (adds `/nfltr:*` slash commands):

```text
/plugin marketplace add nfltr/skills
/plugin install nfltr@nfltr
```

or from a shell:

```bash
claude plugin marketplace add nfltr/skills
claude plugin install nfltr@nfltr
```

The skills drive the `nfltr` CLI. Install it with `curl -fsSL https://nfltr.xyz/install.sh | sh` (the `setup` skill covers it).

## Skills

| Skill | Use it to |
| --- | --- |
| [setup](skills/setup/SKILL.md) | install the CLI, sign in, save and switch API keys |
| [expose-localhost](skills/expose-localhost/SKILL.md) | share a local app, folder, file or output as a protected, expiring link |
| [private-service-access](skills/private-service-access/SKILL.md) | reach a database, SSH or gRPC service on another machine, optionally end to end encrypted |
| [receive-webhooks](skills/receive-webhooks/SKILL.md) | receive, inspect, capture and replay webhooks on a local handler |
| [run-agents-on-your-machines](skills/run-agents-on-your-machines/SKILL.md) | run Claude Code agents on joined machines from a Claude Code session, with owner approvals |
| [troubleshoot-nfltr](skills/troubleshoot-nfltr/SKILL.md) | diagnose connectivity, read `nfltr dial` exit codes, find logs, update |

Agents load a skill when a task matches its description. Ask in plain words, for example "share my dev server on port 5173 with a password for two hours" or "connect psql to the database on my home server".

## Checks

```bash
make check
```

Validates every `SKILL.md` frontmatter, the plugin manifests (with `claude plugin validate --strict` when `claude` is installed), and that every `nfltr` command and flag named in a skill exists in a pinned nfltr release, downloaded and verified by the public installer.

## License

[Apache-2.0](LICENSE). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).
