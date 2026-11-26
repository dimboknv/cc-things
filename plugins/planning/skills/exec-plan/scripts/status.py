#!/usr/bin/env python3
"""Draws the state of a plan run as one HTML page and shows it under the run's agterm session.

usage: EXEC_PLAN_JOURNAL=<journal> status.py [--open | --watch]

The journal is the run's directory, given as an absolute path; its name is the run's slug. The
page is a view of what the run already keeps there and of the checkboxes of the plan: progress.md,
the log; plan, the plan's path at the start of the run; repos, one line per repository of the
plan, `<repo> <main checkout> <run worktree> <branch>`; base.<repo>; and lanes/task-<N>.md, the
section of a task its lane ticks. A task of a running wave is read from its lane's file, so a
lane's ticks show before its wave is integrated; any other task, and every task of a light run,
which has no lane files, is read from the plan: the path in plan, which for a tracked plan is its
copy in the home repository's run worktree, then the path the finalize line names once the plan is
closed. The whole-tree checks, the review rounds and the finalize name the repository they ran in,
and the page shows them per repository. The page holds no state of its own and nothing reads it
back.

Every call writes status.html into the journal and, beside it, status.js with the same content
as data. An open page pulls status.js every five seconds and replaces its content in place, so it
is never reloaded and keeps its scroll position. In an agterm session --open shows the page as a
page companion of that session and records the companion's id in the journal's status-page.
Outside agterm only the files are written.

A journal line comes minutes apart, and the tokens and the checkboxes of a working lane move in
between. So --open also starts one watcher per run, this script with --watch, which redraws every
ten seconds. The watcher lives as long as somebody can look: it ends when the run stops or closes,
and when the page it draws for is gone.

The model, the context, the turns and the tokens of a lane, input with its cached part and output, come from the transcript Claude Code keeps of
every subagent: a transcript belongs to the run when its prompt names the run's journal or one of
its worktrees. The transcripts are looked for in the project directory of every session recorded
as the lead, and in that of the directory that holds the journal's .exec-plan. The
session that leads the run and the peer of a run that has one are sessions of their own: the lead
is known by the id --open records in the journal's lead and is counted over the time of the run;
the peer is known by its brief and is counted whole, from the council before the go. Both come with
the mail they sent each other.

A task no wave has started yet stands in the wave its After chain allows at the earliest, marked
planned: the lead decides the real wave when it starts one.
"""

from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

STAMP = "%Y-%m-%d %H:%M:%S"
WATCH = 10
LINE = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] (.*)$")
TASK_HEAD = re.compile(r"^### Task (\d+): (.*)$")
BOX = re.compile(r"^\s*- \[([ xX])\]\s*(.*)$")
WAVE_START = re.compile(r"^wave (\d+): started, tasks (.*)$")
WAVE_DONE = re.compile(r"^wave (\d+): integrated, (.*)$")
# a lane's report, not the line it logs before a long command
LANE_DONE = re.compile(r"^task (\d+): (?!running .*, about \S+ min$)")
PLAN_CLOSED = re.compile(r"^finalize: plan closed, (\S+)")
# the end of a whole-tree check; its other lines, the one before a long command among them, are not
CHECK_DONE = re.compile(r"^whole tree: (\S+): ((?:green|red)\b.*)$")
CHECK_START = re.compile(r"^whole tree: (\S+): started")
FINALIZE_IN = re.compile(r"^finalize: ([^\s:,]+): (.*)$")
REPO = re.compile(r"^Repo:[ \t]*(.*)$")
SPAN = re.compile(r"`([^`]+)`")


def journal_dir() -> Path:
    """journal_dir is the run's journal as EXEC_PLAN_JOURNAL names it; nothing else names it."""
    given = os.environ.get("EXEC_PLAN_JOURNAL", "")
    if not given:
        raise SystemExit("status.py: EXEC_PLAN_JOURNAL is not set")
    if not os.path.isabs(given):
        raise SystemExit(f"status.py: EXEC_PLAN_JOURNAL is not an absolute path: '{given}'")
    return Path(given)


def read_repos(journal: Path) -> list[dict]:
    """read_repos lists the repositories of the run: name, main checkout, run worktree, branch."""
    try:
        text = (journal / "repos").read_text(encoding="utf-8")
    except OSError:
        return []
    repos = []
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) == 4:
            repos.append(dict(zip(("name", "main", "worktree", "branch"), parts)))
    return repos


def read_journal(path: Path) -> list[tuple[datetime, str]]:
    lines = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE.match(raw)
        if m:
            lines.append((datetime.strptime(m.group(1), STAMP), m.group(2)))
    return lines


def read_tasks(plan: Path) -> dict[int, dict]:
    """read_tasks returns each task section of a plan: its title, checkboxes, stop mark, After
    text and the repository its Repo line names, "" without one."""
    tasks: dict[int, dict] = {}
    cur = None
    in_after = False
    for raw in plan.read_text(encoding="utf-8", errors="replace").splitlines():
        head = TASK_HEAD.match(raw)
        if head:
            cur = {
                "title": head.group(2).strip(),
                "done": 0,
                "total": 0,
                "stopped": False,
                "after": "",
                "repo": "",
                "items": [],
            }
            tasks[int(head.group(1))] = cur
            in_after = False
            continue
        if raw.startswith("## ") or raw.startswith("### "):
            cur = None
            continue
        if cur is None:
            continue
        box = BOX.match(raw)
        if box:
            in_after = False
            cur["total"] += 1
            cur["done"] += box.group(1) != " "
            cur["stopped"] = cur["stopped"] or "⚠️" in raw
            # an item runs on over the lines below its box; its first line names it
            cur["items"].append(
                {
                    "done": box.group(1) != " ",
                    "stopped": "⚠️" in raw,
                    "text": box.group(2).strip(),
                }
            )
            continue
        if repo := REPO.match(raw):
            # ``Repo: `<dir>`.``: the first code span, or else the bare word without its period
            span = SPAN.search(repo.group(1))
            given = span.group(1) if span else repo.group(1).strip().rstrip(".")
            cur["repo"] = given.strip().rstrip("/")
        if raw.startswith("After:"):
            in_after = True
        elif not raw.strip():
            in_after = False
        if in_after:
            cur["after"] += " " + raw.strip()
    return tasks


def find_plan(plan: str, closed: str) -> Path | None:
    """find_plan follows the plan from its path at the start of the run to the path the close
    moved it to, which the finalize's journal line names."""
    for path in [Path(closed)] * bool(closed) + [Path(plan)]:
        if path.is_file():
            return path
    return None


def home_repo(plan: str, repos: list[dict]) -> str:
    """home_repo names the repository a task without a Repo line belongs to: the only one, or the
    one whose checkout holds the plan; a plan outside git has none."""
    if len(repos) == 1:
        return repos[0]["name"]
    for repo in repos:
        for root in (repo["main"], repo["worktree"]):
            try:
                Path(plan).relative_to(root)
            except ValueError:
                continue
            return repo["name"]
    return ""


def after_of(tasks: dict[int, dict], n: int) -> list[int]:
    """after_of lists the tasks whose title the After text of task n names."""
    return [d for d, t in tasks.items() if d != n and t["title"] in tasks[n]["after"]]


def waves_left(tasks: dict[int, dict]) -> int:
    """waves_left is the longest After chain among open tasks; a shared Needs can only add to it."""
    is_open = {n: t["done"] < t["total"] for n, t in tasks.items()}
    depth: dict[int, int] = {}

    def of(n: int, seen: frozenset) -> int:
        if not is_open[n]:
            return 0
        if n not in depth:
            deps = [d for d in after_of(tasks, n) if d not in seen and is_open[d]]
            depth[n] = 1 + max((of(d, seen | {n}) for d in deps), default=0)
        return depth[n]

    return max((of(n, frozenset()) for n in tasks), default=0)


def wave_tasks(listed: str) -> list[int]:
    """wave_tasks reads the task numbers of a wave line, `1, 2, 3`; a repository or a title after
    each number, `1 (lib), 2 (app)` or `1: title`, is passed over.

    A list with no repository and no title is read for every number, whatever separates them. A
    number inside a title is not a task: a task number opens the list or follows a comma, and a
    colon, a comma or the end comes after it."""
    if ":" not in listed and "(" not in listed:
        return [int(n) for n in re.findall(r"\d+", listed)]
    bare = re.sub(r"\([^)]*\)", "", listed)
    return [int(n) for n in re.findall(r"(?:^|,)\s*(\d+)(?=\s*(?:[:,]|$))", bare)]


KINDS = [
    ("lane", re.compile(r"You are executing ONE task of a plan")),
    (
        "integrate",
        re.compile(
            r"Every lane of wave (\d+)?\w*(?: review)? ?of a plan run has ended"
        ),
    ),
    ("check", re.compile(r"Every task of a plan is done")),
    (
        "fixer",
        re.compile(
            r"You are sorting and fixing what review round "
            r"((?:[\w.-]+/)?\d+-[a-z-]+|wave \d+, peer(?:, [\w.-]+)?)?"
        ),
    ),
    ("finalize", re.compile(r"You are closing a plan run")),
]
HEAD = 30
INPUT = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


MAIL = "<summary>chat received</summary>"
SAY = re.compile(r"(?:^|[;&|\n])\s*mailbox-chat\.py say\b")
PEER_BRIEF = "exec-plan/references/peer.md"
PEER_MAIL = "[peer chat]"
STAMPED = re.compile(r'"timestamp":\s*"([^"]+)"')
# a gate the command runs, not one it names inside a quoted journal line or a search pattern
GATE = re.compile(
    r"(?:^|&&|;|\|\||\n)\s*(?:caffeinate -i\s+)?(?:\w+=\S+\s+)*"
    r"(?:make|go (?:build|test|vet)|npm (?:run|test|ci)|npx|pytest|golangci-lint|uv run)\b"
)


def local(stamp: str | None) -> datetime | None:
    """local turns a transcript's UTC stamp into the journal's local time."""
    if not stamp:
        return None
    return (
        datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        .astimezone()
        .replace(tzinfo=None)
    )


def label_of(name: str, given: dict) -> str:
    """label_of names a tool call the way its agent described it."""
    if name == "Bash":
        return str(given.get("description") or given.get("command") or name)[:80]
    target = given.get("file_path") or given.get("pattern") or given.get("skill") or ""
    return f"{name} {Path(str(target)).name}".strip()[:80]


def read_transcript(
    lines, since: datetime | None = None, until: datetime | None = None
) -> dict:
    """read_transcript adds up one agent's transcript: model, tokens, turns, tool calls, mail.

    One reply is written as several lines that repeat its usage, so the last per id counts. A
    session that lives longer than the run, the lead or the peer, is counted between `since`
    and `until`.
    """
    usage: dict[str, dict] = {}
    calls: dict[str, dict] = {}
    model = ""
    sent = received = 0
    for line in lines:
        if (
            '"usage"' not in line
            and '"tool_result"' not in line
            and "chat received" not in line
        ):
            continue
        try:
            said = json.loads(line)
        except ValueError:
            # the last line of a transcript still being written can be half a line
            continue
        at = local(said.get("timestamp"))
        if at and ((since and at < since) or (until and at > until)):
            continue
        message = said.get("message") or {}
        if isinstance(message.get("usage"), dict):
            usage[message.get("id", "")] = message["usage"]
            model = message.get("model") or model
        content = message.get("content")
        if said.get("type") == "user" and MAIL in (
            content if isinstance(content, str) else json.dumps(content)
        ):
            received += 1
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                given = block.get("input") or {}
                command = (
                    str(given.get("command", "")) if block.get("name") == "Bash" else ""
                )
                sent += bool(SAY.search(command))
                calls[block.get("id", "")] = {
                    "label": label_of(block.get("name", ""), given),
                    # a call that writes the journal quotes the gates it reports on
                    "gate": "progress.sh" not in command and bool(GATE.search(command)),
                    "began": at,
                    "ended": None,
                    "failed": False,
                }
            elif block.get("type") == "tool_result":
                call = calls.get(block.get("tool_use_id", ""))
                if call:
                    call["ended"] = at
                    call["failed"] = bool(block.get("is_error"))
    replies = list(usage.values())
    timed = [c for c in calls.values() if c["began"]]
    pending = [c for c in timed if c["ended"] is None]
    return {
        "model": model.replace("claude-", ""),
        "context": sum(replies[-1].get(k, 0) for k in INPUT) if replies else 0,
        "turns": len(replies),
        "out": sum(r.get("output_tokens", 0) for r in replies),
        "in": sum(r.get(k, 0) for r in replies for k in INPUT),
        "steps": [c for c in timed if c["gate"]],
        "now": pending[-1] if pending else None,
        "sent": sent,
        "received": received,
    }


def leads_of(journal: Path) -> list[str]:
    record = journal / "lead"
    return record.read_text().split() if record.is_file() else []


def project_dirs(journal: Path) -> list[Path]:
    """project_dirs are the directories Claude Code keeps the run's transcripts in: the one of
    every session recorded as the lead, which a run across repositories starts from the directory
    that holds them all, and the one of the directory that holds the journal's .exec-plan."""
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    projects = config / "projects"
    found = [
        path.parent
        for i in leads_of(journal)
        for path in projects.glob(f"*/{i}.jsonl")
    ]
    found.append(projects / re.sub(r"[^A-Za-z0-9]", "-", str(journal.parent.parent)))
    return list(dict.fromkeys(found))


def agents(journal: Path, since: datetime) -> list[dict]:
    """agents reads the run's subagents out of their transcripts: kind, task or wave, model, tokens.

    The transcript also holds every tool call with its time and its result, so an agent's gate
    commands are its steps, and a call with no result yet is what the agent is doing now.
    """
    # A lead that hands the prompt over as the template file leaves its placeholders in the
    # transcript and gives the values in its message, so the run is also known by its checkouts.
    # Another run's slug can begin with this one.
    slug = journal.name
    named = re.compile(
        rf"(?:{re.escape(str(journal))}(?:/lanes/task-(\d+)\.md)?|\.claude/worktrees/{re.escape(slug)}"
        rf"(?:-task-(\d+))?)(?![A-Za-z0-9._-])"
    )
    found = []
    for path in (
        p for d in project_dirs(journal) for p in d.glob("*/subagents/agent-*.jsonl")
    ):
        try:
            if path.stat().st_mtime < since.timestamp():
                continue
            with path.open(encoding="utf-8", errors="replace") as lines:
                # The prompt is the first line, or a file the agent reads in its first calls when
                # the lead handed the prompt over as a file. The text is matched as the transcript
                # holds it, JSON-escaped, which the patterns below do not mind.
                head = [line for _, line in zip(range(HEAD), lines)]
                prompt = "".join(head)
                if not named.search(prompt):
                    continue
                started = local(json.loads(head[0]).get("timestamp"))
                if started is None:
                    continue
                kind, hit = next(
                    ((k, m) for k, rx in KINDS if (m := rx.search(prompt))),
                    ("other", None),
                )
                if hit is None:
                    continue
                checkout = re.search(r"- checkout: \S*-task-(\d+) ", prompt)
                lane = (
                    int(checkout.group(1))
                    if checkout
                    else next(
                        (
                            int(m.group(1) or m.group(2))
                            for m in named.finditer(prompt)
                            if m.group(1) or m.group(2)
                        ),
                        None,
                    )
                )
                named_round = hit.group(1) if kind == "fixer" else None
                if kind == "fixer" and not named_round:
                    in_text = re.search(
                        r"((?:[\w.-]+/)?\d\d-(?:initial|after-fix|final))\b", prompt
                    )
                    named_round = in_text.group(1) if in_text else None
                read = read_transcript((*head, *lines))
        except (OSError, ValueError, KeyError, IndexError, AttributeError, TypeError):
            continue
        found.append(
            {
                "kind": kind,
                "task": lane if kind == "lane" else None,
                "wave": int(hit.group(1))
                if kind == "integrate" and hit.group(1)
                else None,
                "round": named_round,
                "started": started,
                **read,
            }
        )
    return sorted(found, key=lambda a: a["started"])


def first_stamp(path: Path) -> datetime | None:
    """first_stamp is the time of the first line of a transcript that carries one."""
    try:
        with path.open(encoding="utf-8", errors="replace") as lines:
            for line in lines:
                if m := STAMPED.search(line):
                    return local(m.group(1))
    except OSError:
        pass
    return None


def sessions(journal: Path, plan: str, since: datetime, until: datetime) -> list[dict]:
    """sessions reads the two agents that are sessions of their own: the lead and its peer.

    The lead is the session that wrote the run's first line; --open records its id. It lives
    longer than the run and is counted between `since` and `until`. The peer was started on the
    peer brief and names the run's journal somewhere in its transcript, or the run's plan in mail
    it received: every session's opening snapshot of `git status` lists an uncommitted plan, so
    the plan's path anywhere else names nothing. It is started
    for the run, in the council before the go and so before the run's first line, and is counted
    whole up to `until`.
    """
    projects = project_dirs(journal)
    found = []
    leads = leads_of(journal)
    lead_paths = [p for d in projects for i in leads if (p := d / f"{i}.jsonl").is_file()]
    # The lead starts the peer, so a transcript last written before the lead began is not it.
    born = min((s for p in lead_paths if (s := first_stamp(p))), default=since)
    named = f".exec-plan/{journal.name}/"

    def names_run(line: str) -> bool:
        return named in line or bool(plan and plan in line and PEER_MAIL in line)

    peers = []
    for path in (p for d in projects for p in d.glob("*.jsonl")):
        try:
            if path.stem in leads or path.stat().st_mtime < born.timestamp():
                continue
            with path.open(encoding="utf-8", errors="replace") as lines:
                head = [line for _, line in zip(range(HEAD), lines)]
                if PEER_BRIEF not in "".join(head):
                    continue
                if any(names_run(line) for line in head) or any(
                    names_run(line) for line in lines
                ):
                    peers.append(path)
        except OSError:
            continue
    for who, paths, start in (
        ("lead", lead_paths, since),
        ("peer", peers, None),
    ):
        for path in paths:
            try:
                with path.open(encoding="utf-8", errors="replace") as lines:
                    read = read_transcript(lines, start, until)
            except OSError:
                continue
            if read["turns"]:
                found.append({"who": who, **read})
    return found


# a round is named <repo>/<run>: revmux runs once per repository
ROUND = re.compile(r"^review round ([^/\s]+/\d+-[a-z-]+?)(?: fixer)?: (.*)$")
SORTED = re.compile(r"^review ([^/\s]+/\d+-[a-z-]+)(?:, profile [\w-]+)?: (.*)$")
# what the fixer of a wave the peer reviewed did, per repository in a run of several
PEER_SORTED = re.compile(r"^review wave (\d+), peer(?:, ([^:\s]+))?: (.*)$")
# a review lane the integrator merged; a lane recut after a merge logs again with its own tip
PEER_MERGED = re.compile(r"^review wave (\d+): merged(?:, ([^,\s]+)(?:, \S+)?)?\s*$")
FOUND = re.compile(r"(\d+) critical, (\d+) major, (\d+) minor(?:, degraded none)?,? ?")


def sorted_out(text: str) -> dict | None:
    """sorted_out reads what a fixer did with a round's findings, in either order the journal spells it."""
    counts = {}
    for key in ("fixed", "open", "dropped", "forks"):
        if m := re.search(rf"\b{key} (\d+)|(\d+) {key}\b", text):
            counts[key] = int(m.group(1) or m.group(2))
    return counts if "fixed" in counts else None


def stages(journal: list[tuple[datetime, str]], spent: list[dict]) -> dict:
    """stages reads what follows the waves: the whole-tree checks, the review rounds, the finalize.

    The journal names a round when it ends, so a round began where the stage before it ended.
    """
    checks: list[dict] = []
    rounds: dict[str, dict] = {}
    finalize = []
    mark = journal[0][0]

    def round_of(name: str) -> dict:
        blank = {
            "began": mark,
            "found": None,
            "done": None,
            "profile": "",
            "counts": None,
        }
        return rounds.setdefault(
            name, {**blank, "outcome": "", "sorted": None, "fixers": []}
        )

    for at, text in journal:
        if m := CHECK_START.match(text):
            checks.append({"repo": m.group(1), "began": at, "ended": None, "result": ""})
        elif m := CHECK_DONE.match(text):
            open_ = [
                c for c in checks if c["repo"] == m.group(1) and c["ended"] is None
            ]
            if not open_:
                open_ = [{"repo": m.group(1), "began": at}]
                checks.append(open_[0])
            open_[-1].update(ended=at, result=m.group(2))
            mark = at
        elif m := ROUND.match(text):
            rnd, rest = round_of(m.group(1)), m.group(2)
            if counts := sorted_out(rest):
                rnd.update(sorted=counts, done=at)
                mark = at
            elif found := FOUND.search(rest):
                rnd.update(found=at, counts=found.groups(), outcome=rest[found.end() :])
                rnd["profile"] = rest.split(",")[0]
                mark = at
            elif "started" in rest:
                rnd["began"] = at
                rnd["profile"] = rest.replace("started", "").strip(", ").split(" (")[0]
            else:
                rnd.update(found=at, outcome=rest)
        elif (m := SORTED.match(text)) and (counts := sorted_out(m.group(2))):
            round_of(m.group(1)).update(sorted=counts, done=at)
            mark = at
        elif text.startswith("run continued"):
            mark = at
        elif m := FINALIZE_IN.match(text):
            finalize.append((at, m.group(1), m.group(2)))
        elif text.startswith("finalize: "):
            finalize.append((at, "", text[len("finalize: ") :]))

    for a in spent:
        if a["kind"] != "fixer" or not a["round"]:
            continue
        # a fixer whose prompt names the run without the repository fits only an unshared name
        fits = [n for n in rounds if n == a["round"] or n.split("/", 1)[1] == a["round"]]
        if len(fits) == 1:
            rounds[fits[0]]["fixers"].append(a)
    for check, a in zip(checks, [a for a in spent if a["kind"] == "check"]):
        check["agent"] = a
    return {
        "checks": checks,
        "rounds": rounds,
        "finalize": finalize,
        "closers": [a for a in spent if a["kind"] == "finalize"],
    }


def short(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n / 1000:.0f}k" if n >= 1000 else str(n)


def span(start: datetime, end: datetime) -> str:
    return spell((end - start).total_seconds())


def clock(seconds: float) -> str:
    """clock spells a time that is still running, to the second, as the page's own timer does."""
    s = int(seconds)
    head = f"{s // 3600}h {s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m"
    return f"{head} {s % 60:02d}s"


def spell(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds // 60)
    return f"{minutes // 60}h {minutes % 60:02d}m" if minutes >= 60 else f"{minutes}m"


def collect(jdir: Path, now: datetime) -> dict:
    slug = jdir.name
    journal = read_journal(jdir / "progress.md")
    if not journal:
        raise SystemExit(f"status.py: no journal lines in {jdir / 'progress.md'}")

    try:
        plan_path = (jdir / "plan").read_text(encoding="utf-8").strip()
    except OSError:
        plan_path = ""
    plan_closed = next(
        (m.group(1) for _, text in journal if (m := PLAN_CLOSED.match(text))), ""
    )
    repos = read_repos(jdir)
    plan = find_plan(plan_path, plan_closed) if plan_path else None
    tasks = read_tasks(plan) if plan else {}
    home = home_repo(plan_path, repos)

    waves: dict[int, dict] = {}
    reported: dict[int, datetime] = {}
    reports: dict[int, list[datetime]] = {}
    phase = "started"
    verdict: dict[str, bool] = {}
    checked: set[str] = set()
    stop_line = ""
    resumed = datetime.min

    def cut(at: datetime) -> None:
        # a wave the run left without integrating it ends where the run stopped or went on
        for wave in waves.values():
            if wave["ended"] is None:
                wave["ended"], wave["note"] = at, "not integrated"

    for at, text in journal:
        if m := WAVE_START.match(text):
            cut(at)
            if stop_line:
                stop_line, resumed = "", at
            waves[int(m.group(1))] = {
                "tasks": wave_tasks(m.group(2)),
                "started": at,
                "ended": None,
                "note": "",
                "integrated": False,
            }
            phase = f"wave {m.group(1)}"
        elif m := WAVE_DONE.match(text):
            wave = waves.setdefault(
                int(m.group(1)), {"tasks": [], "started": at, "note": ""}
            )
            wave["ended"], wave["integrated"] = at, True
            wave["note"] = ", ".join(
                p for p in m.group(2).split(", ") if "conflict" in p or "fix" in p
            )
            phase = f"wave {m.group(1)} integrated"
        elif m := LANE_DONE.match(text):
            reported[int(m.group(1))] = at
            reports.setdefault(int(m.group(1)), []).append(at)
        elif text.startswith("run stopped"):
            cut(at)
            phase, stop_line = "stopped", text
        elif text.startswith("run continued"):
            phase, stop_line, resumed = "continued", "", at
            # a continuation checks every repository again before the review
            verdict.clear()
            checked.clear()
        elif m := CHECK_START.match(text):
            checked.add(m.group(1))
            phase = f"whole-tree check, {m.group(1)}"
        elif m := CHECK_DONE.match(text):
            verdict[m.group(1)] = m.group(2).startswith("green")
            # The review follows once the last check of every repository of the run is green. A
            # repository no wave ran a task of holds only the plan's commits and is never checked.
            worked = {
                tasks[t]["repo"] or home
                for w in waves.values()
                for t in w["tasks"]
                if t in tasks
            }
            names = [
                r["name"] for r in repos if r["name"] in worked or r["name"] in checked
            ] or list(verdict)
            if all(verdict.get(n) for n in names):
                phase = "whole tree green, review next"
            elif verdict[m.group(1)]:
                phase = f"whole tree: {m.group(1)} green"
        elif text.startswith("review round "):
            phase = "review " + text[len("review round ") :].split(":")[0]
        elif text.startswith("finalize: plan closed"):
            phase = "closed"
        elif text.startswith("finalize:"):
            phase = "finalize"

    running = next(
        (n for n in sorted(waves, reverse=True) if waves[n]["ended"] is None), None
    )
    in_lane = set(waves[running]["tasks"]) if running is not None else set()
    # a light run has one executor and no integrator
    light = any(text.startswith("light run:") for _, text in journal)
    if running is not None and phase == f"wave {running}" and not light:
        back = sum(
            1
            for n in in_lane
            if reported.get(n, datetime.min) >= waves[running]["started"]
        )
        phase += (
            ": integrating"
            if back == len(in_lane)
            else f": {back} of {len(in_lane)} lanes back"
        )

    # A lane works from the start of its wave to its report, or to the end of a wave it never
    # reported in. A lane of the running wave with no report yet is live: its time is still going.
    for wave in waves.values():
        end = wave["ended"] or now
        wave["lanes"], wave["live"] = {}, set()
        for n in wave["tasks"]:
            back = [at for at in reports.get(n, []) if wave["started"] <= at <= end]
            if not back and wave["ended"] is None:
                wave["live"].add(n)
                wave["lanes"][n] = 0.0
            else:
                wave["lanes"][n] = (
                    (back[0] if back else end) - wave["started"]
                ).total_seconds()

    spent = agents(jdir, journal[0][0])
    order = sorted(waves)
    for a in spent:
        if a["kind"] in ("lane", "integrate") and a["wave"] is None:
            a["wave"] = next(
                (w for w in reversed(order) if waves[w]["started"] <= a["started"]),
                None,
            )
    # The integrator starts when the last lane of its wave is back and ends with the wave.
    for n, wave in waves.items():
        mine = [a for a in spent if a["wave"] == n]
        wave["agents"] = mine
        wave["in"], wave["out"] = (
            sum(a["in"] for a in mine),
            sum(a["out"] for a in mine),
        )
        end = wave["ended"] or now
        back = [
            at
            for t in wave["tasks"]
            for at in reports.get(t, [])
            if wave["started"] <= at <= end
        ]
        wave["merging"] = max(back) if back and not wave["live"] and not light else None

    # A run with a peer keeps the peer's findings on a wave beside the journal.
    review = jdir / "review"
    for n, wave in waves.items():
        wave["peer"] = None
        try:
            found = json.loads((review / f"wave-{n}.json").read_text()).get("findings")
            wave["peer"] = f"{len(found)} findings"
        except (OSError, ValueError, AttributeError, TypeError):
            if any(text.startswith(f"review wave {n}: sent") for _, text in journal):
                wave["peer"] = "asked, no answer yet"
        # a fixer run again after the owner's answer logs again: its last line counts
        fixed = {
            m.group(2) or "": counts
            for _, text in journal
            if (m := PEER_SORTED.match(text))
            and int(m.group(1)) == n
            and (counts := sorted_out(m.group(3)))
        }
        done = [
            (f"{repo}: " if repo else "") + ", ".join(f"{k} {v}" for k, v in c.items())
            for repo, c in fixed.items()
        ]
        merged = [
            m.group(2) or ""
            for _, text in journal
            if (m := PEER_MERGED.match(text)) and int(m.group(1)) == n
        ]
        if merged:
            into = ", ".join(dict.fromkeys(r for r in merged if r))
            done.append("merged" + (f" in {into}" if into else ""))
        if done:
            wave["peer"] = "; ".join([wave["peer"] or "", *done]).lstrip("; ")
        wave["peer_fixers"] = [
            a
            for a in spent
            if a["kind"] == "fixer"
            and re.match(rf"wave {n}, peer\b", a["round"] or "")
        ]

    over = journal[-1][0] if phase in ("closed", "stopped") else now
    own = sessions(jdir, Path(plan_path).name, journal[0][0], over)

    rows = []
    for n in sorted(tasks):
        task = tasks[n]
        repo = task["repo"] or home
        state = "waiting"
        if n in in_lane:
            lane = jdir / "lanes" / f"task-{n}.md"
            if lane.is_file():
                task = read_tasks(lane).get(n, task)
            back = reported.get(n, datetime.min) >= waves[running]["started"]
            state = "lane back" if back else "lane running"
        if phase == "closed":
            # The finalize runs only when no checkbox is open, and the plan it closed may be
            # out of reach by now: on a branch whose worktree is gone.
            task = {**task, "done": task["total"], "stopped": False}
        if task["stopped"]:
            state = "stopped"
        elif task["total"] and task["done"] == task["total"] and n not in in_lane:
            state = "closed"
        rows.append(
            {
                "n": n,
                "title": task["title"],
                "repo": repo,
                "done": task["done"],
                "total": task["total"],
                "state": state,
                "seconds": sum(w["lanes"].get(n, 0) for w in waves.values()),
                "since": next(
                    (w["started"] for w in waves.values() if n in w["live"]), None
                ),
                "waves": [w for w in sorted(waves) if n in waves[w]["tasks"]],
                "lanes": [a for a in spent if a["kind"] == "lane" and a["task"] == n],
                "items": task["items"],
            }
        )

    # A task no wave has started waits for the open tasks its After names: those still ahead push
    # it one wave further each, those in the running wave only to the wave after it.
    ahead = {r["n"] for r in rows if not r["waves"] and r["state"] != "closed"}
    level: dict[int, int] = {}

    def of(n: int, seen: frozenset) -> int:
        if n not in level:
            level[n] = 1 + max(
                (
                    of(d, seen | {n})
                    for d in after_of(tasks, n)
                    if d in ahead and d not in seen
                ),
                default=0,
            )
        return level[n]

    last_wave = max(waves, default=0)
    for r in rows:
        r["planned"] = last_wave + of(r["n"], frozenset()) if r["n"] in ahead else None

    return {
        "slug": slug,
        "plan": plan_path,
        "repos": [
            {**r, "base": (jdir / f"base.{r['name']}").read_text().strip()[:12]}
            if (jdir / f"base.{r['name']}").is_file()
            else {**r, "base": ""}
            for r in repos
        ],
        "phase": phase,
        "stop_line": stop_line,
        "started": journal[0][0],
        "last": journal[-1],
        "rows": rows,
        "waves": waves,
        "waves_left": waves_left(tasks),
        "stops": [
            (at, text)
            for at, text in journal
            if text.startswith(("[owner]", "[blocker]"))
            and at >= resumed
            and phase != "closed"
        ],
        "in": sum(a["in"] for a in (*spent, *own)),
        "out": sum(a["out"] for a in (*spent, *own)),
        "agents": len(spent) + len(own),
        "sessions": own,
        **stages(journal, spent),
        "decisions": sum(1 for _, text in journal if text.startswith("[decision]")),
        "deviations": sum(1 for _, text in journal if text.startswith("[deviation]")),
    }


CSS = """
:root { --bg: var(--agterm-background, #1d1f21); --fg: var(--agterm-foreground, #c5c8c6);
  --dim: var(--agterm-color-8, #7c7f7c); --red: var(--agterm-color-1, #cc6666);
  --green: var(--agterm-color-2, #9ab86c); --yellow: var(--agterm-color-3, #e0c070);
  --blue: var(--agterm-color-4, #81a2be); }
body { background: var(--bg); color: var(--fg); margin: 0; padding: 20px 24px 40px;
  font: 13px/1.5 ui-monospace, "SF Mono", Menlo, monospace; }
h1 { font-size: 15px; margin: 0 0 2px; font-weight: 600; }
h2 { font-size: 11px; margin: 26px 0 8px; font-weight: 600; color: var(--dim);
  text-transform: uppercase; letter-spacing: .08em; }
.sub, .dim, td.at { color: var(--dim); }
.tiles { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
.tile { border: 1px solid color-mix(in srgb, var(--fg) 18%, transparent); border-radius: 6px;
  padding: 8px 12px; min-width: 110px; }
.tile b { display: block; font-size: 16px; font-weight: 600; }
.tile > span { color: var(--dim); font-size: 11px; }
table { border-collapse: collapse; width: 100%; }
td { padding: 4px 12px 4px 0; vertical-align: top;
  border-top: 1px solid color-mix(in srgb, var(--fg) 10%, transparent); }
td.n, td.at, td.state, td.dim { white-space: nowrap; }
td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.closed { color: var(--green); } .stopped { color: var(--red); }
.lane-running { color: var(--yellow); } .lane-back { color: var(--blue); } .waiting { color: var(--dim); }
.stop { border-left: 3px solid var(--red); padding: 4px 0 4px 10px; margin: 6px 0; overflow-wrap: anywhere; }
th { text-align: left; font-weight: 400; color: var(--dim); font-size: 11px; padding: 0 12px 4px 0; }
th.num { text-align: right; }
tr.wave td { font-weight: 600; }
tr.part td { border-top: 0; padding-top: 0; }
tr.part td:nth-child(2) { padding-left: 18px; }
/* a title or an item stays on one line, cut with an ellipsis, and the row under the pointer
   shows it whole, its wrapped part hanging under the first line */
table.waves tr.part td:nth-child(2) { max-width: 0; width: 100%; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
table.waves tr.part:hover td:nth-child(2) { white-space: normal; overflow-wrap: anywhere; }
table.waves tr.part:not(.now):not(.item) td {
  border-top: 1px solid color-mix(in srgb, var(--fg) 5%, transparent); }
table.waves tr.part:not(.now):not(.item) td:nth-child(2) { padding-left: calc(18px + 4ch);
  text-indent: -4ch; }
table.waves tr.item td:nth-child(2) { padding-left: calc(36px + 4ch); text-indent: -4ch; }
tr.now td:nth-child(2) { padding-left: 36px; color: var(--dim); }
.halt { margin-top: 12px; color: var(--red); overflow-wrap: anywhere; }
"""


# The page loads status.js as a script because a file page cannot fetch a file, and a reload
# would drop the reader's scroll position.
PULL = """
var shown = null;
window.draw = function (body) {
  if (body === shown) return;
  shown = body;
  document.getElementById("run").innerHTML = body;
};
function pull() {
  var s = document.createElement("script");
  s.src = "status.js?t=" + Date.now();
  s.onload = s.onerror = function () { s.remove(); };
  document.head.appendChild(s);
}
setInterval(pull, 5000);
function two(n) { return (n < 10 ? "0" : "") + n; }
setInterval(function () {
  document.querySelectorAll(".tick").forEach(function (el) {
    var s = Math.max(0, Math.floor(+el.dataset.base + Date.now() / 1000 - el.dataset.from));
    var head = s >= 3600 ? Math.floor(s / 3600) + "h " + two(Math.floor(s % 3600 / 60)) + "m"
                         : Math.floor(s / 60) + "m";
    el.textContent = head + " " + two(s % 60) + "s";
  });
}, 1000);
"""


def page_of(slug: str, body: str) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(slug)}</title><style>{CSS}</style></head>"
        f"<body><main id='run'>{body}</main><script>{PULL}</script></body></html>\n"
    )


def render(run: dict, now: datetime) -> str:
    esc = html.escape
    rows = run["rows"]
    closed = sum(1 for r in rows if r["state"] == "closed")
    boxes_done = sum(r["done"] for r in rows)
    boxes = sum(r["total"] for r in rows)
    integrated = sum(1 for w in run["waves"].values() if w["integrated"])
    last_at, last_text = run["last"]

    def took(seconds: float, since: datetime | None = None) -> str:
        # a time still running is redrawn by the page every second from where it started
        if since is None:
            return spell(seconds)
        going = seconds + (now - since).total_seconds()
        return (
            f"<span class='tick' data-from='{int(since.timestamp())}' "
            f"data-base='{int(seconds)}'>{clock(going)}</span>"
        )

    def count(n: int) -> str:
        return short(n) if n else ""

    whole = (
        span(run["started"], last_at)
        if run["phase"] in ("closed", "stopped")
        else took(0, run["started"])
    )
    out = [
        f"<h1>{esc(run['slug'])}</h1>",
        f"<div class='sub'>{esc(run['plan'])}</div>",
        "<div class='tiles'>",
        f"<div class='tile'><b>{esc(run['phase'])}</b><span>phase</span></div>",
        f"<div class='tile'><b>{closed} / {len(rows)}</b><span>tasks closed</span></div>",
        f"<div class='tile'><b>{boxes_done} / {boxes}</b><span>checkboxes</span></div>",
        f"<div class='tile'><b>{integrated} + {run['waves_left']}</b><span>waves integrated + at least left</span></div>",
        f"<div class='tile'><b>{whole}</b><span>since {run['started']:%m-%d %H:%M}</span></div>",
        f"<div class='tile'><b>{short(run['in'])} / {short(run['out'])}</b>"
        f"<span>tokens in / out, {run['agents']} agents</span></div>"
        if run["agents"]
        else "",
        "</div>",
        f"<div class='halt'>{esc(run['stop_line'])}</div>" if run["stop_line"] else "",
    ]
    out += [
        f"<div class='stop'><span class='dim'>{at:%m-%d %H:%M}</span> {esc(text)}</div>"
        for at, text in run["stops"]
    ]

    def agent_cells(agents: list[dict]) -> str:
        models = ", ".join(dict.fromkeys(a["model"] for a in agents if a["model"]))
        return (
            f"<td class='dim'>{esc(models)}</td>"
            f"<td class='num'>{count(agents[-1]['context']) if agents else ''}</td>"
            f"<td class='num'>{sum(a['turns'] for a in agents) or ''}</td>"
            f"<td class='num'>{count(sum(a['in'] for a in agents))}</td>"
            f"<td class='num'>{count(sum(a['out'] for a in agents))}</td>"
        )

    def doing(agents: list[dict], width: int) -> str:
        """doing is one more row under a live agent: the call it is waiting on, and since when."""
        call = agents[-1]["now"] if agents else None
        if not call:
            return ""
        return (
            f"<tr class='part now'><td></td><td colspan='{width - 1}'>"
            f"{took(0, call['began'])} · {esc(call['label'])}</td></tr>"
        )

    def boxes_cell(r: dict) -> str:
        return f"<td class='num'>{r['done']}/{r['total']}</td>"

    several = len(run["repos"]) > 1

    def named(n: int, r: dict | None) -> str:
        where = f" ({r['repo']})" if r and several and r["repo"] else ""
        text = f"task {n}{where}: {r['title']}" if r else f"task {n}"
        return f"<td title='{esc(text)}'>{esc(text)}</td>"

    def state_cell(r: dict) -> str:
        return f"<td class='state {r['state'].replace(' ', '-')}'>{r['state']}</td>"

    if run["repos"]:
        out.append(
            "<h2>Repositories</h2><table><tr><th>repo</th><th>branch</th><th>base</th>"
            "<th>run worktree</th></tr>"
        )
        out += [
            f"<tr><td>{esc(r['name'])}</td><td>{esc(r['branch'])}</td>"
            f"<td class='dim'>{esc(r['base'])}</td><td class='dim'>{esc(r['worktree'])}</td></tr>"
            for r in run["repos"]
        ]
        out.append("</table>")

    if run["sessions"]:
        out.append(
            "<h2>Lead and peer</h2><table><tr><th></th><th>model</th><th class='num'>context</th>"
            "<th class='num'>turns</th><th class='num'>in</th><th class='num'>out</th>"
            "<th class='num'>mail sent</th><th class='num'>mail received</th></tr>"
        )
        out += [
            f"<tr><td>{a['who']}</td><td class='dim'>{esc(a['model'])}</td>"
            f"<td class='num'>{count(a['context'])}</td><td class='num'>{a['turns']}</td>"
            f"<td class='num'>{count(a['in'])}</td><td class='num'>{count(a['out'])}</td>"
            f"<td class='num'>{a['sent'] or ''}</td><td class='num'>{a['received'] or ''}</td></tr>"
            for a in run["sessions"]
        ]
        out.append("</table>")

    # One table: a wave, under it the tasks it ran and its integrator. A task that ran in several
    # waves is a row in each, and its checkboxes and state stand on the row of the last one.
    by_task = {r["n"]: r for r in rows}
    out.append(
        "<h2>Waves and tasks</h2><table class='waves'><tr><th></th><th></th><th class='num'>checkboxes</th>"
        "<th>start</th><th class='num'>time</th><th>model</th><th class='num'>context</th>"
        "<th class='num'>turns</th><th class='num'>in</th><th class='num'>out</th><th></th></tr>"
    )
    for n in sorted(run["waves"]):
        wave = run["waves"][n]
        time = (
            span(wave["started"], wave["ended"])
            if wave["ended"]
            else took(0, wave["started"])
        )
        out.append(
            f"<tr class='wave'><td class='n dim'>{n}</td><td>wave {n}</td><td></td>"
            f"<td class='at'>{wave['started']:%H:%M}</td><td class='num'>{time}</td>"
            f"<td></td><td></td>"
            f"<td class='num'>{sum(a['turns'] for a in wave['agents']) or ''}</td>"
            f"<td class='num'>{count(wave['in'])}</td><td class='num'>{count(wave['out'])}</td>"
            f"<td class='dim'>{esc(wave['note'] or ('' if wave['ended'] else 'running'))}</td></tr>"
        )
        for t, sec in wave["lanes"].items():
            lanes = [
                a for a in wave["agents"] if a["kind"] == "lane" and a["task"] == t
            ]
            live = t in wave["live"]
            r = by_task.get(t)
            last = bool(r) and r["waves"][-1] == n
            out.append(
                f"<tr class='part'><td></td>{named(t, r)}"
                f"{boxes_cell(r) if last else '<td></td>'}<td></td>"
                f"<td class='num'>{took(0, wave['started']) if live else spell(sec)}</td>"
                f"{agent_cells(lanes)}{state_cell(r) if last else '<td></td>'}</tr>"
            )
            if live:
                out.append(doing(lanes, 11))
                if r:
                    out += [
                        f"<tr class='part item'><td></td><td colspan='10' class='"
                        f"{'stopped' if i['stopped'] else 'closed' if i['done'] else 'dim'}' "
                        f"title='{esc(i['text'])}'>"
                        f"[{'x' if i['done'] else ' '}] {esc(i['text'])}</td></tr>"
                        for i in r["items"]
                    ]
        merging = wave["merging"]
        mergers = [a for a in wave["agents"] if a["kind"] == "integrate"]
        if merging and (wave["integrated"] or not wave["ended"]):
            done = wave["ended"]
            out.append(
                f"<tr class='part'><td></td><td>integrator</td><td></td>"
                f"<td class='at'>{merging:%H:%M}</td>"
                f"<td class='num'>{span(merging, done) if done else took(0, merging)}</td>"
                f"{agent_cells(mergers)}<td class='dim'>{'' if done else 'running'}</td></tr>"
            )
            if not done:
                out.append(doing(mergers, 11))
        solo = [a for a in wave["agents"] if a["kind"] == "lane" and a["task"] is None]
        if solo:
            # the one executor of a light run works in the run worktree, a checkout of no lane
            live = not wave["ended"]
            out.append(
                f"<tr class='part'><td></td><td>executor</td><td></td><td></td>"
                f"<td class='num'>{took(0, wave['started']) if live else span(wave['started'], wave['ended'])}</td>"
                f"{agent_cells(solo)}<td class='dim'>{'running' if live else ''}</td></tr>"
            )
            if live:
                out.append(doing(solo, 11))
        if wave["peer"] or wave["peer_fixers"]:
            out.append(
                "<tr class='part'><td></td><td>peer</td>"
                + "<td></td>" * 3
                + agent_cells(wave["peer_fixers"])
                + f"<td class='dim'>{esc(wave['peer'] or '')}</td></tr>"
            )
    for n in sorted({r["planned"] for r in rows if r["planned"]}):
        out.append(
            f"<tr class='wave'><td class='n dim'>{n}</td><td>wave {n}</td>"
            + "<td></td>" * 8
            + "<td class='dim'>planned</td></tr>"
        )
        out += [
            f"<tr class='part'><td></td>{named(r['n'], r)}{boxes_cell(r)}"
            + "<td></td>" * 7
            + f"{state_cell(r)}</tr>"
            for r in rows
            if r["planned"] == n
        ]
    ahead = [r for r in rows if not r["waves"] and not r["planned"]]
    if ahead:
        out.append(
            "<tr class='wave'><td></td><td>closed before the run</td>"
            + "<td></td>" * 9
            + "</tr>"
        )
        out += [
            f"<tr class='part'><td></td>{named(r['n'], r)}{boxes_cell(r)}"
            + "<td></td>" * 7
            + f"{state_cell(r)}</tr>"
            for r in ahead
        ]
    out.append("</table>")
    if not rows:
        out.append(
            "<div class='dim'>the plan the journal's plan file names was not found</div>"
        )

    def tokens(agents: list[dict]) -> str:
        return (
            f"<td class='num'>{sum(a['turns'] for a in agents) or ''}</td>"
            f"<td class='num'>{count(sum(a['in'] for a in agents))}</td>"
            f"<td class='num'>{count(sum(a['out'] for a in agents))}</td>"
        )

    going = run["phase"] not in ("closed", "stopped")
    if run["checks"]:
        out.append(
            "<h2>Whole tree</h2><table><tr><th>repo</th><th>start</th><th class='num'>time</th>"
            "<th>result</th><th class='num'>turns</th><th class='num'>in</th><th class='num'>out</th></tr>"
        )
        for check in run["checks"]:
            last = check is [c for c in run["checks"] if c["repo"] == check["repo"]][-1]
            time = (
                span(check["began"], check["ended"])
                if check["ended"]
                else (took(0, check["began"]) if going and last else "")
            )
            out.append(
                f"<tr><td>{esc(check['repo'])}</td>"
                f"<td class='at'>{check['began']:%H:%M}</td><td class='num'>{time}</td>"
                f"<td>{esc(check.get('result') or 'running')}</td>"
                f"{tokens([check['agent']] if 'agent' in check else [])}</tr>"
            )
            for step in check["agent"]["steps"] if "agent" in check else []:
                if step["ended"]:
                    time, result = (
                        span(step["began"], step["ended"]),
                        "failed" if step["failed"] else "ok",
                    )
                elif going and last:
                    time, result = took(0, step["began"]), "running"
                else:
                    continue
                out.append(
                    f"<tr class='part'><td></td><td></td><td class='num'>{time}</td>"
                    f"<td>{esc(step['label'])}</td>"
                    f"<td class='state {'stopped' if result == 'failed' else 'dim'}'>{result}</td><td></td></tr>"
                )
        out.append("</table>")

    names = list(run["rounds"])
    waiting = going and run["phase"].startswith("whole tree green")
    if names or waiting:
        out.append(
            "<h2>Review rounds</h2><table><tr><th>repo</th><th>round</th><th>profile</th>"
            "<th class='num'>critical</th><th class='num'>major</th><th class='num'>minor</th>"
            "<th>outcome</th><th class='num'>review</th><th class='num'>fixer</th><th>sorted</th>"
            "<th class='num'>turns</th><th class='num'>in</th><th class='num'>out</th></tr>"
        )
        for name in names:
            rnd = run["rounds"][name]
            repo, run_name = name.split("/", 1)
            last = going and name == [n for n in names if n.startswith(repo + "/")][-1]
            review = (
                span(rnd["began"], rnd["found"])
                if rnd["found"]
                else (took(0, rnd["began"]) if last else "")
            )
            fixer = ""
            if rnd["found"] and rnd["done"]:
                fixer = span(rnd["found"], rnd["done"])
            elif (
                rnd["found"] and last and re.search(r"fixer|minor pass", rnd["outcome"])
            ):
                fixer = took(0, rnd["found"])
            counts = rnd["counts"] or ("", "", "")
            done = rnd["sorted"]
            out.append(
                f"<tr><td>{esc(repo)}</td><td class='n'>{esc(run_name)}</td>"
                f"<td class='dim'>{esc(rnd['profile'])}</td>"
                + "".join(f"<td class='num'>{c}</td>" for c in counts)
                + f"<td>{esc(rnd['outcome'] or ('' if rnd['found'] else 'running'))}</td>"
                f"<td class='num'>{review}</td><td class='num'>{fixer}</td>"
                f"<td class='dim'>{esc(', '.join(f'{k} {v}' for k, v in done.items()) if done else '')}</td>"
                f"{tokens(rnd['fixers'])}</tr>"
            )
        if waiting:
            since = run["checks"][-1]["ended"] if run["checks"] else run["last"][0]
            out.append(
                f"<tr><td></td><td class='n dim'>next</td><td></td><td></td><td></td><td></td><td>running</td>"
                f"<td class='num'>{took(0, since)}</td><td></td><td></td><td></td><td></td><td></td></tr>"
            )
        out.append("</table>")

    if run["finalize"]:
        out.append("<h2>Finalize</h2><table>")
        out += [
            f"<tr><td class='at'>{at:%H:%M}</td><td>{esc(repo)}</td><td>{esc(text)}</td></tr>"
            for at, repo, text in run["finalize"]
        ]
        closers = run["closers"]
        if closers:
            out.append(
                f"<tr><td class='at'></td><td></td><td class='dim'>tokens in {count(sum(a['in'] for a in closers))}, "
                f"out {count(sum(a['out'] for a in closers))}</td></tr>"
            )
        out.append("</table>")

    out += [
        "<h2>Journal</h2>",
        f"<div>{run['decisions']} decisions, {run['deviations']} deviations</div>",
        f"<div class='dim'>last line {last_at:%m-%d %H:%M:%S}: {esc(last_text[:300])}</div>",
        f"<div class='dim'>drawn {now:%m-%d %H:%M:%S}</div>",
    ]
    return "\n".join(out)


def agterm(*args: str) -> subprocess.CompletedProcess | None:
    tool = os.environ.get("AGTERMCTL", "agtermctl")
    try:
        return subprocess.run(
            [tool, *args], capture_output=True, text=True, check=False, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def show(page: Path, slug: str) -> None:
    """show opens the page under the agterm session, or reuses the one already there, and starts the watcher."""
    session = os.environ.get("AGTERM_SESSION_ID", "")
    if not session:
        return
    record = page.with_name("status-page")
    # the reload asks whether the recorded page is still there, and gives it the page as now written
    shown = record.read_text().strip() if record.is_file() else ""
    res = agterm("session", "overlay", "reload", "--target", shown) if shown else None
    if res is None or res.returncode != 0:
        res = agterm(
            "session",
            "overlay",
            "open",
            "--html",
            str(page),
            "--cwd",
            str(page.parent),
            "--js",
            "--companion",
            "--chromeless",
            "--target",
            session,
            "--json",
        )
        if res is None or res.returncode != 0:
            return
        try:
            shown = json.loads(res.stdout)["result"]["id"]
        except (ValueError, KeyError, TypeError):
            return
        record.write_text(shown + "\n")
        agterm("session", "rename", f"run: {slug}"[:40], "--target", shown)
    if not watcher(page):
        subprocess.Popen(
            [sys.executable, __file__, "--watch"],
            cwd=page.parent,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def watcher(page: Path) -> int:
    """watcher returns the pid of the run's live watcher, or 0."""
    try:
        pid = int(page.with_name("status-watch").read_text())
        os.kill(pid, 0)
    except (OSError, ValueError):
        return 0
    return pid


def draw(jdir: Path) -> str:
    """draw writes the page and its data and returns the phase the run is in."""
    now = datetime.now()
    slug = jdir.name
    page = jdir / "status.html"
    run = collect(jdir, now)
    body = render(run, now)
    data = "window.draw(" + json.dumps(body).replace("</", "<\\/") + ");\n"
    # lanes of one wave write the journal at the same moment, and a reader must never see half a file
    for path, text in (
        (page, page_of(slug, body)),
        (page.with_name("status.js"), data),
    ):
        scratch = path.with_name(f"{path.name}.{os.getpid()}")
        scratch.write_text(text, encoding="utf-8")
        scratch.replace(path)
    return run["phase"]


def watch(jdir: Path) -> None:
    """watch redraws the page while the run goes on and its page is open."""
    page = jdir / "status.html"
    mark = page.with_name("status-watch")
    if watcher(page):
        return
    mark.write_text(f"{os.getpid()}\n")
    silent = 0
    try:
        while silent < 3:
            time.sleep(WATCH)
            shown = page.with_name("status-page").read_text().strip()
            tree = agterm("tree", "--json")
            if tree is None or tree.returncode != 0:
                # agterm restarting is not the page closing
                silent += 1
                continue
            silent = 0
            if shown not in tree.stdout:
                break
            if draw(jdir) in ("closed", "stopped"):
                break
    except (OSError, SystemExit):
        pass
    finally:
        if watcher(page) == os.getpid():
            mark.unlink()


def main() -> int:
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args or not flags <= {"--open", "--watch"} or len(flags) > 1:
        print(
            "usage: EXEC_PLAN_JOURNAL=<journal> status.py [--open | --watch]",
            file=sys.stderr,
        )
        return 2
    jdir = journal_dir()
    if "--watch" in flags:
        watch(jdir)
        return 0
    if "--open" in flags and (lead := os.environ.get("CLAUDE_CODE_SESSION_ID")):
        known = leads_of(jdir)
        if lead not in known:
            (jdir / "lead").write_text("\n".join([*known, lead]) + "\n")
    draw(jdir)
    if "--open" in flags:
        show(jdir / "status.html", jdir.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
