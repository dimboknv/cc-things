#!/usr/bin/env python3
"""Run the search commands of a plan's `acceptance:` items and show what each one hits.

Usage: acceptance.py <plan.md> [<base>]   (base defaults to the cwd)

For every `### Task N:` section, every backtick span inside an `acceptance` item whose
command is a read-only search is run from the root of the task's repository. A task's
`Repo:` line names that repository as a directory relative to <base>, the directory the
session started in, which holds every repository of the plan. A task with no `Repo:` runs
in the plan's home repository, the work tree the plan lies in when git does not ignore it;
in a plan with no home repository such a task is skipped and says so. The output is grouped
by file, and a file outside every path the task's `Where:` line names, relative to the
task's repository, is marked `outside Where:`; a hit in the plan file itself is marked
`the plan itself`.
That mark is where an inventory term matches something the task does not own: a kept name,
another task's file, a foreign meaning. Gates (`make`, `go`, `npm`) are not run.

Exit 0 always: the report is read, not gated on.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

READ_ONLY = {
    "rg",
    "grep",
    "ls",
    "test",
    "find",
    "wc",
    "head",
    "sort",
    "uniq",
    "cut",
}
READ_ONLY_GIT = {"grep", "check-ignore", "ls-files"}
SEARCH_HEAD = re.compile(r"^(rg|grep|awk|git|ls|test|find)\b")
SEARCH_WORD = re.compile(r"(^|[\s;&|(!])(rg|grep|awk|git|find)\b")
FILE_PREFIX = re.compile(r"^([^\s:][^:]*?):(\d+:)?")
MAX_FILES = 25
TIMEOUT = 60


def segments(cmd: str) -> list[list[str]] | str:
    """Split cmd into its pipeline's commands, quotes respected; a str is the reason it cannot."""
    parts, start, quote, i = [], 0, None, 0
    while i < len(cmd):
        c = cmd[i]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"':
                i += 1
        elif c in "'\"":
            quote = c
        elif c == "\\":
            i += 1
        elif c == "$" and cmd[i + 1 : i + 2] == "'":
            # $'...' lets \' escape a quote, which this scan does not follow
            return "unparsable"
        elif c == "|" and cmd[i + 1 : i + 2] != "|":
            parts.append(cmd[start:i])
            start = i + 1
        elif c in "();<>|&":
            return "compound command"
        i += 1
    if quote:
        return "unparsable"
    parts.append(cmd[start:])
    try:
        return [shlex.split(p) for p in parts]
    except ValueError:
        return "unparsable"


def runnable(cmd: str) -> str | None:
    """Return None when cmd may run, else the reason it is skipped."""
    if "$(" in cmd or "`" in cmd:
        return "command substitution"
    segs = segments(cmd)
    if isinstance(segs, str):
        return segs
    for words in segs:
        if not words:
            return "empty segment"
        head = words[0]
        if head == "git":
            if len(words) < 2 or words[1] not in READ_ONLY_GIT:
                return f"git {words[1] if len(words) > 1 else ''} is not a search"
        elif head not in READ_ONLY:
            return f"`{head}` is not a search"
        if head == "find" and any(
            w in ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fls")
            or w.startswith("-fprint")
            for w in words
        ):
            return "find with an action"
        if writes(head, words):
            return f"`{head}` here writes a file or runs a program"
    if segs[0][0] == "grep" and grep_reads_stdin(segs[0]):
        return "grep with no file reads stdin"
    return None


GREP_ARG_SHORT = set("efmABCdD")
GREP_ARG_LONG = {
    "--regexp",
    "--file",
    "--max-count",
    "--after-context",
    "--before-context",
    "--context",
    "--directories",
    "--devices",
    "--include",
    "--exclude",
    "--exclude-dir",
    "--exclude-from",
    "--label",
    "--binary-files",
    "--group-separator",
}


def grep_reads_stdin(words: list[str]) -> bool:
    """Whether grep, given words, has no file operand and no recursion, so reads stdin."""
    operands, pattern_given, recursive = [], False, False

    def after(i: int) -> str:
        return words[i + 1] if i + 1 < len(words) else ""

    i = 1
    while i < len(words):
        w = words[i]
        if w == "--":
            operands += words[i + 1 :]
            break
        if w.startswith("--"):
            name, eq, value = w.partition("=")
            if name in ("--regexp", "--file"):
                pattern_given = True
            if name in ("--recursive", "--dereference-recursive"):
                recursive = True
            if name == "--directories":
                recursive = recursive or (value if eq else after(i)) == "recurse"
            if name in GREP_ARG_LONG and not eq:
                i += 1
        elif w.startswith("-") and w != "-":
            for j, ch in enumerate(w[1:], 1):
                if ch in "rR":
                    recursive = True
                if ch in GREP_ARG_SHORT:
                    pattern_given = pattern_given or ch in "ef"
                    if ch == "d" and (w[j + 1 :] or after(i)) == "recurse":
                        recursive = True
                    if not w[j + 1 :]:
                        i += 1
                    break
        else:
            operands.append(w)
        i += 1
    files = operands if pattern_given else operands[1:]
    return not recursive and not [f for f in files if f != "-"]


def short_flags(words: list[str]) -> str:
    """The letters of every short-option cluster in words."""
    return "".join(
        w[1:] for w in words if w.startswith("-") and not w.startswith("--")
    )


def long_option(words: list[str], *names: str) -> bool:
    """Whether words hold one of names as a long option, in full or as a getopt prefix."""
    for w in words:
        name = w.split("=", 1)[0]
        if len(name) > 2 and name.startswith("--") and any(
            n.startswith(name) for n in names
        ):
            return True
    return False


def writes(head: str, words: list[str]) -> bool:
    """Whether an allowed tool is given an option that writes a file or runs a program."""
    if head == "sort":
        return "o" in short_flags(words[1:]) or long_option(
            words, "--output", "--compress-program"
        )
    if head == "rg":
        return any(w == "--pre" or w.startswith("--pre=") for w in words)
    if head == "git" and words[1] == "grep":
        return "O" in short_flags(words[2:]) or long_option(
            words, "--open-files-in-pager"
        )
    if head == "uniq":
        # uniq's second operand is its output file
        operands = [
            w
            for w in words[1:]
            if not (w.startswith("-") and w != "-") and not w.isdigit()
        ]
        return len(operands) > 1
    return False


def tasks(text: str):
    """Yield (title, where_paths, repo_or_None, acceptance_items) per task section."""
    parts = re.split(r"(?m)^### (Task \d+:.*)$", text)
    for i in range(1, len(parts), 2):
        title, body = parts[i].strip(), parts[i + 1]
        body = re.split(r"(?m)^## ", body)[0]
        repo = None
        m = re.search(r"(?m)^Repo:[ \t]*(.*)$", body)
        if m:
            span = re.search(r"`([^`]+)`", m.group(1))
            repo = (span.group(1) if span else m.group(1)).strip().rstrip(".") or None
        where = []
        m = re.search(r"(?m)^Where:(.*(?:\n(?!\n)(?![A-Z][A-Za-z]*:).*)*)", body)
        if m:
            where = [
                norm(w).rstrip("/") for w in re.findall(r"`([^`]+)`", m.group(1))
            ]
        items, cur = [], None
        for line in body.splitlines():
            if re.match(r"^- \[[ x]\]", line):
                cur = line if "acceptance" in line else None
                if cur is not None:
                    items.append(cur)
            elif cur is not None and line.startswith("  ") and line.strip():
                items[-1] += " " + line.strip()
            else:
                cur = None
        yield title, where, repo, items


def home_repo(plan: Path) -> Path | None:
    """The work tree the plan lies in when git does not ignore it, else None."""
    top = subprocess.run(
        ["git", "-C", str(plan.parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if top.returncode != 0:
        return None
    ignored = subprocess.run(
        ["git", "-C", str(plan.parent), "check-ignore", "-q", str(plan)],
        capture_output=True,
    )
    return None if ignored.returncode == 0 else Path(top.stdout.strip())


def norm(path: str) -> str:
    return path[2:] if path.startswith("./") else path


def inside(path: str, where: list[str]) -> bool:
    p = norm(path)
    return any(p == w or p.startswith(w + "/") for w in where)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = Path(sys.argv[1]).resolve()
    base = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
    home = home_repo(plan)
    for title, where, repo, items in tasks(plan.read_text()):
        if not items:
            continue
        print(f"\n## {title}")
        print(f"   Where: {', '.join(where) or '—'}")
        if repo:
            root = base / repo
            if not root.is_dir():
                print(f"   skipped: Repo: {repo} is not a directory under {base}")
                continue
        elif home:
            root = home
        else:
            print("   skipped: no Repo: line, and the plan has no home repository")
            continue
        print(f"   Repo: {root}")
        for item in items:
            for cmd in re.findall(r"`([^`]+)`", item):
                if not SEARCH_HEAD.match(cmd):
                    if SEARCH_WORD.search(cmd):
                        print(f"\n   skipped (not a search): {cmd}")
                    continue
                why = runnable(cmd)
                if why:
                    print(f"\n   skipped ({why}): {cmd}")
                    continue
                try:
                    r = subprocess.run(
                        cmd,
                        shell=True,
                        cwd=root,
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        text=True,
                        timeout=TIMEOUT,
                    )
                except subprocess.TimeoutExpired:
                    print(f"\n   timeout: {cmd}")
                    continue
                lines = [line for line in r.stdout.splitlines() if line.strip()]
                print(f"\n   $ {cmd}")
                print(
                    f"     exit {r.returncode}, {len(lines)} line(s)"
                    + (
                        f"; stderr: {r.stderr.strip()[:200]}"
                        if r.stderr.strip()
                        else ""
                    )
                )
                files = Counter()
                for line in lines:
                    m = FILE_PREFIX.match(line)
                    if m and (root / m.group(1)).exists():
                        files[m.group(1)] += 1
                    elif (root / line.strip()).is_file():
                        files[line.strip()] += 1
                if not files:
                    for line in lines[:5]:
                        print(f"     | {line[:160]}")
                    continue
                for f, n in files.most_common(MAX_FILES):
                    if (root / f).resolve() == plan:
                        mark = "   <- the plan itself"
                    elif not where or inside(f, where):
                        mark = ""
                    else:
                        mark = "   <- outside Where:"
                    print(f"     {n:4}  {f}{mark}")
                if len(files) > MAX_FILES:
                    print(f"     … {len(files) - MAX_FILES} more file(s)")


if __name__ == "__main__":
    main()
