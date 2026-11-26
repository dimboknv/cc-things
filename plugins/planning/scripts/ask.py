#!/usr/bin/env python3
"""Asks the owner one closed question in an agterm dialog bound to this session.

usage: ask.py <title> [--message TEXT] [--default ID] [--other PLACEHOLDER] [--timeout SECONDS]
              --item ID LABEL SUBTITLE [--item ID LABEL SUBTITLE ...]

On an answer it prints `choice <id>` for a picked item, or `text <line>` for what the owner typed
into the --other line, and exits 0. Without an answer it prints nothing, gives the reason on
stderr and exits 1: no AGTERM_SESSION_ID, agtermctl missing or failing, the owner pressed Esc,
the dialog timed out. The caller then asks the same question with AskUserQuestion.

The dialog is bound to AGTERM_SESSION_ID, not to the selected session: the owner may be looking
at another one, and the dialog waits in this session until they come back. AGTERMCTL names
another agtermctl.
"""
import argparse
import json
import os
import subprocess
import sys


def fail(reason: str) -> None:
    print(f"ask.py: {reason}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(prog="ask.py")
    p.add_argument("title")
    p.add_argument("--message")
    p.add_argument("--default")
    p.add_argument("--other")
    p.add_argument("--timeout", type=int, default=540)
    p.add_argument("--item", nargs=3, action="append", required=True,
                   metavar=("ID", "LABEL", "SUBTITLE"))
    a = p.parse_args()

    ids = [i for i, _, _ in a.item]
    if len(ids) < 2 or len(set(ids)) != len(ids):
        p.error("--item needs two or more distinct ids")
    if a.default is not None and a.default not in ids:
        p.error(f"--default {a.default} names no --item")
    if not 1 <= a.timeout <= 86400:
        p.error("--timeout is 1..86400 seconds")

    session = os.environ.get("AGTERM_SESSION_ID")
    if not session:
        fail("not in agterm: AGTERM_SESSION_ID is not set")

    cmd = [os.environ.get("AGTERMCTL") or "agtermctl", "ask", "open", a.title,
           "--target", session, "--timeout", str(a.timeout), "--json"]
    # In agterm's radio list the arrows only move the highlight; Space picks, Return answers.
    keys = "↑↓ move · Space picks · Return answers"
    cmd += ["--message", f"{a.message} · {keys}" if a.message else keys]
    for item_id, label, subtitle in a.item:
        cmd += ["--choice", f"{item_id}={label}"]
        if subtitle:
            cmd += ["--choice-subtitle", f"{item_id}={subtitle}"]
    if a.default is not None:
        cmd += ["--checked", a.default]
    if a.other:
        cmd += ["--other", a.other]

    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout + 30)
    except FileNotFoundError:
        fail(f"{cmd[0]} is not on PATH")
    except subprocess.TimeoutExpired:
        fail("agtermctl did not return")

    try:
        reply = json.loads(run.stdout)
    except ValueError:
        fail(f"agtermctl exited {run.returncode}: {(run.stderr or run.stdout).strip()}")
    result = reply.get("result")
    if result != "answered" or reply.get("id") != "ok":
        fail(f"no answer: {result or reply.get('error') or run.returncode}")

    selected = reply.get("selected") or []
    if selected:
        print(f"choice {selected[0]}")
    elif reply.get("text", "").strip():
        print(f"text {reply['text']}")
    else:
        fail("answered with nothing picked")


if __name__ == "__main__":
    main()
