#!/usr/bin/env python3
"""Lists the shell commands of a plan run's subagents that break a rule of the run's prompts.

usage: EXEC_PLAN_JOURNAL=<journal> audit.py

The journal is the run's directory, given as an absolute path; its name is the run's slug.
Claude Code keeps the transcript of every subagent under its config directory, one JSONL file
per agent, and each Bash call is a line of it. The transcripts are looked for in the project
directory of every session the journal's lead file records, and in that of the directory that
holds the journal's .exec-plan. A transcript belongs to the run when it names the journal or a
checkout of the run: .claude/worktrees/<slug>, or a lane, review or scratch worktree beside it,
in any repository of the run. The session that leads the run is not read, only its subagents.

A rule here is a pattern over one command, so a finding is a place to look and not a verdict:
a search for the text of a forbidden command matches as the command itself would. A rule that
no pattern over one command can state is not here. The rules about Go apply only to a checkout
of the run that tracks a go.mod, among the repositories the journal's repos file lists, and a
`make -C <dir>` counts as a Go build only when a go.mod lies under <dir> in one of them.

Prints one line per finding and a count. Exits 1 when the run has no transcript.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

GO = re.compile(r"\bgo (build|test|vet|run|generate)\b|\bgolangci-lint run\b")
# make where a command starts, not the word inside a path such as skills/make-plan/: after an
# operator, a subshell or group, a negation or a shell keyword, behind wrappers and assignments
MAKE = re.compile(
    r"(?:^|[;&|\n({!]|\b(?:if|then|do|else|elif|while|until)\b)\s*"
    r"(?:(?:caffeinate -i|time|timeout(?:\s+-[ks]\s*\S+|\s+-\S+)*\s+\S+|env|nice(?:\s+-n\s*\S+)?|command|exec"
    r"|\w+=\S+)\s+)*make\b(?:\s+-C\s*(\S+))?"
)
# git with its -C <dir>, -c <key=value> or --<option> options before the subcommand
GIT = r"\bgit(?:\s+(?:-[Cc]\s*\S+|--\S+))*\s+"
# the journal's directory as a command names it
JOURNAL = r"(?:\S*\.exec-plan/|\$\{?EXEC_PLAN_JOURNAL\}?/)"


def go_dirs(checkouts: list[Path]) -> list[str]:
    """go_dirs lists the directories of the checkouts that hold a tracked go.mod, "" for a root.

    A command does not say which repository it ran in, so the directories of all of them count."""
    found: list[str] = []
    for checkout in checkouts:
        listed = subprocess.run(
            ["git", "-C", str(checkout), "ls-files", "--", "go.mod", "**/go.mod"],
            capture_output=True,
            text=True,
        ).stdout.split()
        found += ["" if p == "go.mod" else str(Path(p).parent) for p in listed]
    return list(dict.fromkeys(found))


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
                GIT
                + r"(commit|stash|rm|mv)\b|"
                + GIT
                + r"add\s+(-A|-p|--all|--patch)\b",
                c,
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
        lambda c, mods: bool(
            re.search(
                r"(?:>>?|\btee(?:\s+-\S+)*)\s*[\"']?" + JOURNAL + r"\S*progress\.md",
                c,
            )
            or re.search(
                r"\bcd\s+[\"']?(?:\S*\.exec-plan/|\$\{?EXEC_PLAN_JOURNAL\b).*?"
                r"(?:>>?|\btee(?:\s+-\S+)*)\s*[\"']?(?:\./)?progress\.md",
                c,
            )
        ),
    ),
]


def checkouts(journal: Path) -> list[Path]:
    """checkouts are the main checkouts the journal's repos file lists, one per repository: a run
    worktree may be gone by the time the run is read back."""
    try:
        text = (journal / "repos").read_text(encoding="utf-8")
    except OSError:
        return []
    return [Path(parts[1]) for raw in text.splitlines() if len(parts := raw.split()) == 4]


def transcripts(journal: Path) -> list[Path]:
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    projects = config / "projects"
    record = journal / "lead"
    leads = record.read_text().split() if record.is_file() else []
    dirs = [p.parent for i in leads for p in projects.glob(f"*/{i}.jsonl")]
    dirs.append(projects / re.sub(r"[^A-Za-z0-9]", "-", str(journal.parent.parent)))
    return sorted(
        (p for d in dict.fromkeys(dirs) for p in d.glob("*/subagents/agent-*.jsonl")),
        key=lambda p: p.stat().st_mtime,
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
    given = os.environ.get("EXEC_PLAN_JOURNAL", "")
    if not given:
        print("audit.py: EXEC_PLAN_JOURNAL is not set", file=sys.stderr)
        return 1
    if not os.path.isabs(given):
        print(f"audit.py: EXEC_PLAN_JOURNAL is not an absolute path: '{given}'", file=sys.stderr)
        return 1
    if len(sys.argv) != 1:
        print("usage: EXEC_PLAN_JOURNAL=<journal> audit.py", file=sys.stderr)
        return 2
    journal = Path(given)
    slug = journal.name
    of_run = re.compile(
        r"(?:"
        + re.escape(str(journal))
        + r"|\.claude/worktrees/"
        + re.escape(slug)
        + r"(-(task|review)-\d+|-tip|-base)?)(?![A-Za-z0-9._-])"
    )

    agents = commands_read = findings = 0
    mods = go_dirs(checkouts(journal))
    for path in transcripts(journal):
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
            f"audit.py: no subagent transcript names {journal} or a checkout of '{slug}'",
            file=sys.stderr,
        )
        return 1
    print(f"audit: {findings} findings in {commands_read} commands of {agents} agents")
    for name, meaning, _ in RULES:
        print(f"  {name}: {meaning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
