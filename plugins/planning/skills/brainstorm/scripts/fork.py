#!/usr/bin/env python3
"""Show a brainstorm fork as a page in the agterm overlay and print the owner's answer.

  fork.py show FRAGMENT [--diagram-design SKILL_DIR]
                           build the page from the fragment, open it, wait for the answer
  fork.py result PAGE_ID   read the answer of a page a show call stopped waiting for

SKILL_DIR is the folder of the loaded diagram-design skill; a fragment that links a
diagram-design drawing needs it.

Exit 0: stdout is the answer as JSON. Exit 2: the owner cancelled. Exit 3: still open, stdout is the
page id. Exit 1: an error, on stderr.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

MARKER = "<!--FORK-->"
POLL_SECONDS = 1.0
# show runs in the background; the cap only stops a page left open from polling for ever
WAIT_SECONDS = 3 * 3600

# an empty <figure data-diagram="..."> names a diagram-design HTML file
DIAGRAM_RE = re.compile(
    r"""<figure\b[^>]*?\bdata-diagram=(["'])(.*?)\1[^>]*>\s*</figure\s*>""",
    re.IGNORECASE | re.DOTALL,
)
# Inside an <img> an SVG loads no web font, and a bare `monospace` there is a serif Courier in
# WebKit. The names are swapped only where a font is declared, so a label that says "Geist"
# keeps its text. A family name may be quoted with a quote or an XML entity, or not at all.
FONT_CONTEXT_RE = re.compile(
    r"""<style\b[^>]*>.*?</style\s*>|(?<=\s)(?:font-family|style)\s*=\s*(?:"[^"]*"|'[^']*')""",
    re.IGNORECASE | re.DOTALL,
)
FONT_RE = re.compile(
    r"(?<![\w-])(?P<q>&quot;|&apos;|&#3[49];|[\"']|)"
    r"(?P<name>geist\s*mono|instrument\s*serif|geist)(?P=q)(?![\w-])",
    re.IGNORECASE,
)


def system_font(match: re.Match[str]) -> str:
    q = match["q"]
    # quotes right after `=` delimit an attribute (font-family="Geist"), not a family name
    delimiter = q in ("'", '"') and match.string[: match.start()].rstrip().endswith("=")
    inner = "" if delimiter else q
    name = re.sub(r"\s+", "", match["name"]).lower()
    if name == "geistmono":
        # the quote that stood around the name is safe here; an unquoted name stays unquoted
        stack = f"ui-monospace, {inner}SF Mono{inner}, Menlo, monospace"
    elif name == "instrumentserif":
        stack = "ui-serif, Georgia, serif"
    else:
        stack = "system-ui, -apple-system, sans-serif"
    return f"{q}{stack}{q}" if delimiter else stack


def diagram_img(html: Path, skill_dir: Path, out: Path) -> str:
    """Export a diagram-design HTML file to SVG with the skill's own exporter, as an <img>."""
    res = subprocess.run(
        [
            sys.executable,
            str(skill_dir / "scripts" / "export_svg.py"),
            str(html),
            str(out),
            "--system-fonts",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0 or not out.is_file():
        raise ValueError(
            f"export_svg.py failed on {html}: {(res.stderr or res.stdout).strip()}"
        )
    svg = FONT_CONTEXT_RE.sub(
        lambda ctx: FONT_RE.sub(system_font, ctx[0]), out.read_text(encoding="utf-8")
    )
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<figure class="diagram"><img src="data:image/svg+xml;base64,{data}" alt=""></figure>'


def embed_diagrams(body: str, fragment: Path, skill_dir: Path | None) -> str:
    links = list(DIAGRAM_RE.finditer(body))
    if not links:
        return body
    if skill_dir is None:
        raise ValueError(
            "the fragment links a diagram-design drawing; pass the folder of the loaded "
            "diagram-design skill with --diagram-design"
        )
    if not (skill_dir / "scripts" / "export_svg.py").is_file():
        raise ValueError(
            f"no scripts/export_svg.py in {skill_dir}; pass the folder the diagram-design "
            "skill printed when it loaded"
        )
    parts, pos = [], 0
    for n, link in enumerate(links, 1):
        html = fragment.parent / link[2]
        if not html.is_file():
            raise ValueError(
                f"the diagram {link[2]} is not a file; a relative path starts at the fragment's folder"
            )
        out = fragment.with_suffix(f".diagram-{n}.svg")
        parts += [body[pos : link.start()], diagram_img(html, skill_dir, out)]
        pos = link.end()
    return "".join(parts) + body[pos:]


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


def show(fragment: Path, skill_dir: Path | None) -> int:
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
    try:
        body = embed_diagrams(body, fragment, skill_dir)
    except ValueError as err:
        print(f"fork: {err}", file=sys.stderr)
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
        return show(Path(argv[2]), None)
    if (
        len(argv) == 5
        and argv[1] == "show"
        and argv[3] == "--diagram-design"
        and Path(argv[2]).is_file()
    ):
        return show(Path(argv[2]), Path(argv[4]))
    if len(argv) == 3 and argv[1] == "result":
        return finish(*read_outcome(argv[2]), argv[2])
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
