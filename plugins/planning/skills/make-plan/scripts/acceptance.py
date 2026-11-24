#!/usr/bin/env python3
"""Run the search commands of a plan's `acceptance:` items and show what each one hits.

Usage: acceptance.py <plan.md> [<checkout>]   (checkout defaults to the git top level of the cwd)

For every `### Task N:` section, every backtick span inside an `acceptance` item whose
command is a read-only search is run from the checkout root. The output is grouped by file,
and a file outside every path the task's `Where:` line names is marked `outside Where:`.
That mark is where an inventory term matches something the task does not own: a kept name,
another task's file, a foreign meaning. Gates (`make`, `go`, `npm`) are not run.

Exit 0 always: the report is read, not gated on.
"""

import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

READ_ONLY = {
    "rg",
    "grep",
    "awk",
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
FILE_PREFIX = re.compile(r"^([^\s:][^:]*?):(\d+:)?")
MAX_FILES = 25
TIMEOUT = 60


def segments(cmd: str) -> list[list[str]] | str:
    """Split cmd into its pipeline's commands, quotes respected; a str is the reason it cannot."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError:
        return "unparsable"
    segs, cur = [], []
    for t in tokens:
        if t == "|":
            segs.append(cur)
            cur = []
        elif t and set(t) <= set("();<>|&"):
            return "compound command"
        else:
            cur.append(t)
    segs.append(cur)
    return segs


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
            w in ("-delete", "-exec", "-execdir", "-ok") for w in words
        ):
            return "find with an action"
    return None


def tasks(text: str):
    """Yield (title, where_paths, acceptance_items) per task section."""
    parts = re.split(r"(?m)^### (Task \d+:.*)$", text)
    for i in range(1, len(parts), 2):
        title, body = parts[i].strip(), parts[i + 1]
        body = re.split(r"(?m)^## ", body)[0]
        where = []
        m = re.search(r"(?m)^Where:(.*(?:\n(?!\n).*)*)", body)
        if m:
            where = [
                w.rstrip("/")
                for w in re.findall(r"`([^`]+)`", m.group(1))
                if "/" in w or "." in w
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
        yield title, where, items


def inside(path: str, where: list[str]) -> bool:
    p = path.lstrip("./")
    return any(p == w or p.startswith(w + "/") or p.startswith(w) for w in where)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = Path(sys.argv[1]).resolve()
    root = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else Path(
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
            ).stdout.strip()
        )
    )
    for title, where, items in tasks(plan.read_text()):
        if not items:
            continue
        print(f"\n## {title}")
        print(f"   Where: {', '.join(where) or '—'}")
        for item in items:
            for cmd in re.findall(r"`([^`]+)`", item):
                if not re.match(r"^(rg|grep|awk|git|ls|test|find)\b", cmd):
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
                    mark = (
                        "" if not where or inside(f, where) else "   <- outside Where:"
                    )
                    print(f"     {n:4}  {f}{mark}")
                if len(files) > MAX_FILES:
                    print(f"     … {len(files) - MAX_FILES} more file(s)")


if __name__ == "__main__":
    main()
