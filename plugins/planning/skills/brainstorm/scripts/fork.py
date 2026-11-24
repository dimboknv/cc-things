#!/usr/bin/env python3
"""Show a brainstorm fork as a page in the agterm overlay and print the owner's answer.

  fork.py show FRAGMENT    build the page from the fragment, open it, wait for the answer
  fork.py result PAGE_ID   read the answer of a page a show call stopped waiting for

Exit 0: stdout is the answer as JSON. Exit 2: the owner cancelled. Exit 3: still open, stdout is the
page id. Exit 1: an error, on stderr.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

MARKER = "<!--FORK-->"
POLL_SECONDS = 1.0
# show runs in the background; the cap only stops a page left open from polling for ever
WAIT_SECONDS = 3 * 3600


def agtermctl(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [os.environ.get("AGTERMCTL") or "agtermctl", *args]
    # agtermctl never reads AGTERM_SOCKET, so a session on a custom socket is passed one
    if sock := os.environ.get("AGTERM_SOCKET"):
        cmd += ["--socket", sock]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def read_outcome(page_id: str) -> tuple[str, str]:
    res = agtermctl("session", "overlay", "result", "--page", page_id)
    try:
        outcome = json.loads(res.stdout)
    except json.JSONDecodeError:
        return "error", (
            res.stderr or res.stdout
        ).strip() or f"agtermctl exited {res.returncode}"
    state = outcome.get("outcome", "")
    if state not in ("submitted", "dismissed", "pending"):
        return "error", f"unexpected outcome: {res.stdout.strip()}"
    return state, outcome.get("value", "")


def finish(state: str, text: str, page_id: str) -> int:
    if state == "submitted":
        print(text)
        return 0
    if state == "dismissed":
        print("fork: the owner cancelled the page", file=sys.stderr)
        return 2
    if state == "pending":
        print(page_id)
        print(
            f"fork: the page is still open; read it later with: fork.py result {page_id}",
            file=sys.stderr,
        )
        return 3
    print(f"fork: {text}", file=sys.stderr)
    return 1


def show(fragment: Path) -> int:
    session = os.environ.get("AGTERM_SESSION_ID")
    if not session:
        print(
            "fork: AGTERM_SESSION_ID is not set, the page needs agterm; give the fork as text",
            file=sys.stderr,
        )
        return 1
    body = fragment.read_text(encoding="utf-8")
    if "data-place" not in body or "data-option" not in body:
        print(
            "fork: the fragment has no data-place root or no data-option block",
            file=sys.stderr,
        )
        return 1
    shell = (Path(__file__).resolve().parent.parent / "assets" / "fork.html").read_text(
        encoding="utf-8"
    )
    page = fragment.with_suffix(".page.html")
    page.write_text(shell.replace(MARKER, body), encoding="utf-8")

    res = agtermctl(
        "session",
        "overlay",
        "open",
        "--html",
        str(page),
        "--chromeless",
        "--js",
        "--size-percent",
        "95",
        "--target",
        session,
        "--json",
    )
    if res.returncode != 0:
        print(
            f"fork: overlay open failed: {(res.stderr or res.stdout).strip()}",
            file=sys.stderr,
        )
        return 1
    page_id = json.loads(res.stdout)["result"]["pageID"]
    print(f"fork: page {page_id}", file=sys.stderr, flush=True)

    target = ["--target", session]
    if pane_id := os.environ.get("AGTERM_PANE_ID"):
        target += ["--pane-id", pane_id]
    agtermctl("session", "status", "blocked", "--blink", *target)
    try:
        deadline = time.monotonic() + WAIT_SECONDS
        state, text = read_outcome(page_id)
        while state == "pending" and time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
            state, text = read_outcome(page_id)
    finally:
        agtermctl("session", "status", "idle", *target)
    return finish(state, text, page_id)


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "show" and Path(argv[2]).is_file():
        return show(Path(argv[2]))
    if len(argv) == 3 and argv[1] == "result":
        return finish(*read_outcome(argv[2]), argv[2])
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
