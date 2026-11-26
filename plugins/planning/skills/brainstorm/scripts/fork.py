#!/usr/bin/env python3
"""Show a brainstorm fork as a page in the agterm overlay and print the owner's answer.

  fork.py show FRAGMENT [--diagram-design SKILL_DIR]
                           build the page from the fragment, open it, wait for the answer
  fork.py result PAGE_ID   read the answer of a page a show call stopped waiting for

SKILL_DIR is the folder of the loaded diagram-design skill; a fragment that links a
diagram-design drawing needs it.

Exit 0: stdout is the answer as JSON. Exit 2: the owner cancelled. Exit 3: still open, or its
state could not be read for a while; stdout is the page id. Exit 1: an error, on stderr; show
opened no page, or result could not read a page that may still be open.
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
# agtermctl can fail for a moment while the page stays open; only this many failed reads in a row
# end the wait
POLL_ERRORS = 30
# show runs in the background; the cap only stops a page left open from polling for ever
WAIT_SECONDS = 3 * 3600

# an empty <figure data-diagram="..."> names a diagram-design HTML file
DIAGRAM_RE = re.compile(
    r"""<figure\b[^>]*?\bdata-diagram=(["'])(.*?)\1[^>]*>\s*</figure\s*>""",
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL)
# a start or end tag with its attributes, so a quoted value that names an attribute stays a value
TAG_RE = re.compile(
    r"""<(/?)([a-z][\w-]*)((?:\s+[^\s"'>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?)*)\s*/?>""",
    re.IGNORECASE,
)
ATTR_RE = re.compile(
    r"""([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?"""
)
# the shell keys its own choices and comment fields by these
RESERVED_IDS = ("own", "explain", "today", "general")
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


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def attrs(text: str) -> dict[str, str]:
    return {
        a[1].lower(): next((v for v in a.groups()[1:] if v is not None), "")
        for a in ATTR_RE.finditer(text)
    }


def tags(body: str) -> list[tuple[re.Match[str], dict[str, str]]]:
    return [(t, attrs(t[3])) for t in TAG_RE.finditer(body)]


def root_span(body: str) -> tuple[int, int] | None:
    """Where the first data-place element starts and ends: the root the shell draws from."""
    found = tags(body)
    for n, (tag, attr) in enumerate(found):
        if tag[1] or "data-place" not in attr:
            continue
        name, depth = tag[2].lower(), 0
        for other, _ in found[n:]:
            if other[2].lower() != name:
                continue
            depth += -1 if other[1] else 1
            if depth == 0:
                return tag.start(), other.end()
        return tag.start(), len(body)
    return None


def parse_json(text: str, attr: str) -> object:
    def constant(name: str) -> object:
        # Python reads NaN and Infinity; the shell's JSON.parse throws on them
        raise ValueError(f"{attr} is not JSON: {name} is not a JSON value")

    try:
        return json.loads(text, parse_constant=constant)
    except json.JSONDecodeError as err:
        raise ValueError(f"{attr} is not JSON: {err}") from None


def check_fragment(body: str) -> None:
    """Refuse what the shell's script cannot draw: it would stop before Send and Cancel work."""
    for tag, attr in tags(body):
        if not tag[1] and attr.get("data-option") in RESERVED_IDS:
            raise ValueError(
                f"the option id '{attr['data-option']}' is kept by the page; ids {', '.join(RESERVED_IDS)} are reserved"
            )
    roles: object = {}
    flows: list[object] = []
    roles_seen = 0
    root = root_span(body)
    for m in SCRIPT_RE.finditer(body):
        script = attrs(m[1])
        if "data-roles" in script:
            roles_seen += 1
            if roles_seen > 1:
                raise ValueError("the fragment has more than one data-roles script")
            if root is None or not root[0] <= m.start() < root[1]:
                raise ValueError("the data-roles script must stand inside the data-place root")
            roles = parse_json(m[2], "data-roles")
        elif "data-flow" in script:
            flows.append(parse_json(m[2], "data-flow"))
    if not isinstance(roles, dict):
        raise ValueError("data-roles is not a JSON object of roles")
    for rid, role in roles.items():
        if not (
            isinstance(role, dict)
            and is_number(role.get("x"))
            and is_number(role.get("y"))
            and isinstance(role.get("label"), str)
            and ("w" not in role or is_number(role["w"]))
        ):
            raise ValueError(
                f"data-roles: role '{rid}' needs a number x and y, a string label and, if given, a number w"
            )
    for flow in flows:
        nodes = flow.get("nodes", {}) if isinstance(flow, dict) else None
        edges = flow.get("edges", []) if isinstance(flow, dict) else None
        if not isinstance(nodes, dict) or not isinstance(edges, list):
            raise ValueError(
                "a data-flow is a JSON object with a nodes object and an edges list"
            )
        named = list(nodes)
        for edge in edges:
            if not isinstance(edge, list) or len(edge) < 2:
                raise ValueError(
                    f"a data-flow edge is [from, to, kind, step]: {edge!r}"
                )
            if str(edge[0]) == str(edge[1]):
                raise ValueError(f"a data-flow edge goes from role '{edge[0]}' to itself")
            named += [str(edge[0]), str(edge[1])]
        for rid in named:
            if rid not in roles:
                raise ValueError(
                    f"a data-flow names role '{rid}', which data-roles does not place"
                )


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


def read_retried(page_id: str) -> tuple[str, str]:
    """read_outcome, a failed read retried as show's wait retries it."""
    errors = 0
    while True:
        state, text = read_outcome(page_id)
        errors = errors + 1 if state == "error" else 0
        if state != "error" or errors >= POLL_ERRORS:
            return state, text
        time.sleep(POLL_SECONDS)


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
    # the page may still be open: a second show would put another page over it
    print(
        f"fork: cannot read the page: {text}; read it again later with: fork.py result {page_id}",
        file=sys.stderr,
    )
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
        check_fragment(body)
        body = embed_diagrams(body, fragment, skill_dir)
        if any(
            tag[2].lower() == "figure" and "data-diagram" in attr for tag, attr in tags(body)
        ):
            raise ValueError(
                "a data-diagram link was not embedded: its <figure> must be empty and the value quoted"
            )
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
        errors = 0
        while True:
            state, text = read_outcome(page_id)
            errors = errors + 1 if state == "error" else 0
            if (
                state not in ("pending", "error")
                or errors >= POLL_ERRORS
                or time.monotonic() >= deadline
            ):
                break
            time.sleep(POLL_SECONDS)
    finally:
        agtermctl("session", "status", "idle", *target)
    if state == "error":
        # the page may still be open: a second show would put another page over it
        print(f"fork: cannot read the page: {text}", file=sys.stderr)
        state = "pending"
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
        return finish(*read_retried(argv[2]), argv[2])
    print(__doc__, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
