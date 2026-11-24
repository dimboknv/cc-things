#!/usr/bin/env python3
"""Lists the shell commands of a plan run's subagents that break a rule of the run's prompts.

usage: audit.py <slug>

Claude Code keeps the transcript of every subagent under its config directory, one JSONL file
per agent, and each Bash call is a line of it. A transcript belongs to the run when it names a
checkout of the run: .claude/worktrees/<slug>, or a lane, review or scratch worktree beside it.
The session that leads the run is not read, only its subagents.

A rule here is a pattern over one command, so a finding is a place to look and not a verdict:
a search for the text of a forbidden command matches as the command itself would. A rule that
no pattern over one command can state is not here. The rules about Go apply only to a checkout
that tracks a go.mod, and a `make -C <dir>` counts as a Go build only when a go.mod lies under
<dir>.

Prints one line per finding and a count. Exits 1 when the run has no transcript.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

GO = re.compile(r"\bgo (build|test|vet|run|generate)\b|\bgolangci-lint run\b")
MAKE = re.compile(r"\bmake\b(?:\s+-C\s*(\S+))?")


def go_dirs(main: Path) -> list[str]:
    """go_dirs lists the directories of the checkout that hold a tracked go.mod, "" for the root."""
    listed = subprocess.run(
        ["git", "-C", str(main), "ls-files", "--", "go.mod", "**/go.mod"],
        capture_output=True,
        text=True,
    ).stdout.split()
    return ["" if p == "go.mod" else str(Path(p).parent) for p in listed]


def builds_go(c: str, mods: list[str]) -> bool:
    """builds_go tells a command that builds, tests or lints Go; a make run in a directory with no
    go.mod under it does not."""
    if not mods:
        return False
    if GO.search(c):
        return True
    for m in MAKE.finditer(c):
        target = (m.group(1) or "").strip("'\"").rstrip("/")
        if not target or target == "." or "" in mods:
            return True
        if any(d == target or d.startswith(target + "/") for d in mods):
            return True
    return False


# (name, what the prompts say, the test of one command and the checkout's go.mod directories)
RULES = [
    (
        "shared-cache",
        "Go built, tested or linted without cache.sh in the same call",
        lambda c, mods: builds_go(c, mods)
        and "cache.sh" not in c
        and "commit.sh" not in c,
    ),
    (
        "cache-cleared",
        "a cache every session shares was cleared",
        lambda c, mods: bool(
            re.search(
                r"\bgolangci-lint cache clean\b|\bgo clean\b[^;&|]*-(cache|modcache)\b",
                c,
            )
        ),
    ),
    (
        "own-commit",
        "a commit or a staging made around commit.sh",
        lambda c, mods: bool(
            re.search(
                r"\bgit (commit|stash|rm|mv)\b|\bgit add (-A|-p|--all|--patch)\b", c
            )
        ),
    ),
    (
        "hook-bypassed",
        "a hook was bypassed",
        lambda c, mods: bool(
            re.search(r"--no-verify\b|\bLEFTHOOK(_EXCLUDE)?=|\bHUSKY=0\b", c)
        ),
    ),
    (
        "e2e-run",
        "a Go suite under the e2e build tag was run, which only a task whose Needs: names the stand it uses may do",
        lambda c, mods: (
            bool(re.search(r"\bgo test\b[^;&|]*-tags[ =]\S*e2e", c))
            and not re.search(r"\bgo test\b[^;&|]* -c\b", c)
        ),
    ),
    (
        "journal-written",
        "the journal was written around progress.sh",
        lambda c, mods: bool(re.search(r">>?\s*\S*\.exec-plan/\S*progress\.md", c)),
    ),
]


def main_checkout() -> Path:
    common = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return Path(common).parent


def transcripts(main: Path) -> list[Path]:
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    project = config / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(main))
    return sorted(
        project.glob("*/subagents/agent-*.jsonl"), key=lambda p: p.stat().st_mtime
    )


def commands(path: Path):
    for line in path.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if entry.get("type") != "assistant" or not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") == "Bash"
            ):
                command = (block.get("input") or {}).get("command")
                if isinstance(command, str):
                    yield command


def label(path: Path) -> str:
    meta = path.with_suffix(".meta.json")
    try:
        described = json.loads(meta.read_text()).get("description")
    except (OSError, ValueError):
        described = None
    return f"{described or 'agent'} ({path.parent.parent.name[:8]}/{path.stem})"


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]*", sys.argv[1]
    ):
        print("usage: audit.py <slug>", file=sys.stderr)
        return 2
    slug = sys.argv[1]
    of_run = re.compile(
        r"\.claude/worktrees/"
        + re.escape(slug)
        + r"(-(task|review)-\d+|-tip|-base)?(?![A-Za-z0-9._-])"
    )

    agents = commands_read = findings = 0
    main = main_checkout()
    mods = go_dirs(main)
    for path in transcripts(main):
        if not of_run.search(path.read_text(errors="replace")):
            continue
        agents += 1
        who = label(path)
        for command in commands(path):
            commands_read += 1
            for name, _, broken in RULES:
                if broken(command, mods):
                    findings += 1
                    shown = re.sub(r"^cd \S+ *(&&|;) *", "", " ".join(command.split()))
                    print(f"{name}: {who}: {shown[:200]}")
    if agents == 0:
        print(
            f"audit.py: no subagent transcript names a checkout of '{slug}'",
            file=sys.stderr,
        )
        return 1
    print(f"audit: {findings} findings in {commands_read} commands of {agents} agents")
    for name, meaning, _ in RULES:
        print(f"  {name}: {meaning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
