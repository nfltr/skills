#!/usr/bin/env python3
"""Check the skills and plugin manifests. Standard library only.

    python3 scripts/check.py --nfltr PATH [--claude PATH]

1. Every skills/<dir>/SKILL.md has Agent Skills frontmatter (agentskills.io):
   name (equal to <dir>, lowercase letters, digits and single hyphens, <= 64),
   description (1-1024), and only known optional fields.
2. .claude-plugin/plugin.json and marketplace.json parse, carry their required
   fields, and agree on the plugin name. With --claude, `claude plugin
   validate --strict` checks both against Claude Code's own schema.
3. Every `nfltr ...` command in a skill names subcommands and flags that the
   given nfltr binary has (each command's --help is read; nothing else runs).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def fail(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


# --- 1. frontmatter ---------------------------------------------------------

KNOWN = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> dict | None:
    """The YAML subset skills use: `key: value` plus one level of nested map."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    out: dict = {}
    parent = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        nested = line.startswith("  ")
        key, sep, val = line.strip().partition(":")
        if not sep:
            raise ValueError(f"not a key: value line: {line!r}")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if nested:
            if parent is None:
                raise ValueError(f"indented line without a parent: {line!r}")
            out[parent][key] = val
        elif val == "":
            parent = key
            out[key] = {}
        else:
            parent = None
            out[key] = val
    return out


def check_skills() -> list[Path]:
    files = []
    for d in sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        where = str(f.relative_to(ROOT))
        if not f.is_file():
            fail(str(d.relative_to(ROOT)), "missing SKILL.md")
            continue
        files.append(f)
        try:
            fm = parse_frontmatter(f.read_text())
        except ValueError as e:
            fail(where, f"frontmatter: {e}")
            continue
        if fm is None:
            fail(where, "missing --- frontmatter ---")
            continue
        for k in sorted(set(fm) - KNOWN):
            fail(where, f"unknown frontmatter field {k!r}")
        name = fm.get("name", "")
        if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
            fail(where, f"name {name!r}: 1-64 lowercase letters, digits, single hyphens")
        if name != d.name:
            fail(where, f"name {name!r} differs from its directory {d.name!r}")
        desc = fm.get("description", "")
        if not isinstance(desc, str) or not 1 <= len(desc) <= 1024:
            fail(where, "description: required, 1-1024 characters")
        comp = fm.get("compatibility")
        if comp is not None and (not isinstance(comp, str) or not 1 <= len(comp) <= 500):
            fail(where, "compatibility: 1-500 characters")
        if "metadata" in fm and not isinstance(fm["metadata"], dict):
            fail(where, "metadata: a map of string keys to string values")
    if not files:
        fail("skills", "no skills found")
    return files


# --- 2. manifests -----------------------------------------------------------

def load_json(rel: str) -> dict:
    try:
        return json.loads((ROOT / rel).read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(rel, f"does not parse: {e}")
        return {}


def check_manifests(claude: str | None) -> None:
    plugin = load_json(".claude-plugin/plugin.json")
    market = load_json(".claude-plugin/marketplace.json")
    if not plugin.get("name"):
        fail("plugin.json", "name is required")
    if not market.get("name") or not market.get("owner", {}).get("name"):
        fail("marketplace.json", "name and owner.name are required")
    entries = market.get("plugins") or []
    if not entries:
        fail("marketplace.json", "plugins must list the plugin")
    for i, e in enumerate(entries):
        if not e.get("name") or not e.get("source"):
            fail("marketplace.json", f"plugins[{i}]: name and source are required")
        if e.get("source") == "./" and e.get("name") != plugin.get("name"):
            fail("marketplace.json", f"plugins[{i}].name differs from plugin.json name")
    if claude:
        env = dict(os.environ, CLAUDE_CONFIG_DIR=tempfile.mkdtemp(prefix="skills-claude-"))
        r = subprocess.run([claude, "plugin", "validate", "--strict", str(ROOT)],
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            fail("claude plugin validate", (r.stdout + r.stderr).strip())


# --- 3. nfltr commands ------------------------------------------------------

WORD = re.compile(r"^[a-z][a-z0-9-]*$")
# Commands whose next bare word must be one of their subcommands.
GROUPS = {("orch",), ("orch", "hub"), ("orch", "nodes"), ("orch", "task"),
          ("config",), ("node",), ("wg",)}
help_cache: dict[tuple, str | None] = {}
SANDBOX: dict[str, str] = {}


def help_text(nfltr: str, path: tuple) -> str | None:
    """The command's --help output, or None when nfltr does not know the path.

    Runs in a throwaway HOME with no key and an unreachable relay, so a word
    that turns out to be an argument cannot touch a real config or account.
    """
    if path not in help_cache:
        r = subprocess.run([nfltr, *path, "--help"], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=30, env=SANDBOX)
        out = r.stdout + r.stderr
        head = "\n".join(out.splitlines()[:4]).lower()
        ok = r.returncode == 0 and "usage" in out.lower() and "unknown" not in head
        help_cache[path] = out if ok else None
    return help_cache[path]


def commands_in(text: str) -> list[str]:
    """Every `nfltr ...` command in code blocks and inline code."""
    code = re.findall(r"```[a-z]*\n(.*?)```", text, re.S)
    code = [c.replace("\\\n", " ") for c in code]
    lines = [ln for c in code for ln in c.splitlines()]
    lines += re.findall(r"`([^`\n]+)`", re.sub(r"```.*?```", "", text, flags=re.S))
    cmds = []
    for ln in lines:
        ln = ln.split(" #")[0]
        for seg in re.split(r"\s(?:--|\||&&|;)\s|[|<>]", ln):
            for m in re.finditer(r"(?:^|[\s\"'(])nfltr\s+(.*)", seg):
                cmds.append(m.group(1).strip().strip("\"'"))
    return cmds


def check_command(nfltr: str, where: str, cmd: str) -> None:
    try:
        toks = shlex.split(cmd)
    except ValueError:
        toks = cmd.split()
    path: tuple = ()
    for t in toks:
        if not WORD.match(t):
            break
        if help_text(nfltr, path + (t,)) is None:
            if not path or path in GROUPS:
                fail(where, f"`nfltr {cmd}`: no command `nfltr {' '.join(path + (t,))}`")
                return
            break  # a positional argument of a leaf command
        path += (t,)
    if not path:
        fail(where, f"`nfltr {cmd}`: no subcommand")
        return
    usage = help_text(nfltr, path) or ""
    for t in toks:
        m = re.match(r"^--?([a-z][a-z0-9-]*)(=.*)?$", t)
        if m and not re.search(rf"(^|[\s,\[])--?{re.escape(m.group(1))}\b", usage, re.M):
            fail(where, f"`nfltr {cmd}`: `nfltr {' '.join(path)}` has no flag --{m.group(1)}")


def check_commands(nfltr: str, files: list[Path]) -> int:
    n = 0
    for f in files + [ROOT / "README.md"]:
        for cmd in commands_in(f.read_text()):
            check_command(nfltr, str(f.relative_to(ROOT)), cmd)
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nfltr", required=True, help="nfltr binary (nfltr-orch beside it)")
    ap.add_argument("--claude", help="claude binary for `claude plugin validate`")
    a = ap.parse_args()
    home = tempfile.mkdtemp(prefix="skills-check-")
    SANDBOX.update(PATH=os.environ.get("PATH", ""), HOME=home, XDG_CONFIG_HOME=home,
                   XDG_STATE_HOME=home, NFLTR_CONFIG=f"{home}/nfltr.json",
                   NFLTR_STATE_DIR=home, NFLTR_SERVER="127.0.0.1:1")
    files = check_skills()
    check_manifests(a.claude)
    n = check_commands(a.nfltr, files)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    print(f"{len(files)} skills, {n} nfltr commands checked, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
