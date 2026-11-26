#!/usr/bin/env bash
# scripts/fork.py builds the fork page from a fragment. A fragment that links a diagram-design
# drawing gets it exported by the export_svg.py of the skill folder passed with
# --diagram-design, its fonts swapped for system stacks, and embedded as an <img> with a data
# URI; without the folder the page is refused. A stub agtermctl stands in for agterm, and a stub
# skill folder stands in for diagram-design.
#
# Before the page opens, fork.py refuses a fragment the shell could not draw: bad roles or flow
# JSON, a flow naming a role the roles do not place, an option id the shell keeps for itself,
# a role script that is not the one inside the data-place root, NaN or Infinity, an edge from a
# role to itself, and a drawing link left unembedded; an attribute value or text that only
# names data-diagram or data-option is not refused. While the page is open, a failed read of its
# state is retried; a lasting one ends the wait with the page id, as a page still open does.
# `result` retries a failed read too, and a lasting one says to read again later.
#
# Every check runs and reports; the script exits non-zero when any failed. FORK_SCRIPT points
# it at another copy of the script.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
fork=${FORK_SCRIPT:-$here/../plugins/planning/skills/brainstorm/scripts/fork.py}

base=$(mktemp -d)
trap 'rm -rf "$base"' EXIT

# The stub opens a page, answers it as submitted and accepts every other call. While the
# number in $STUB_FAILS is above zero, a read of the answer fails and counts it down.
stub=$base/agtermctl
cat >"$stub" <<'EOF'
#!/usr/bin/env bash
case "$3" in
open) echo '{"result":{"pageID":"PAGE-1"}}' ;;
result)
  n=$(cat "$STUB_FAILS" 2>/dev/null || echo 0)
  if [ "$n" -gt 0 ]; then
    echo $((n - 1)) >"$STUB_FAILS"
    echo "agtermctl: the socket did not answer" >&2
    exit 1
  fi
  echo '{"outcome":"submitted","value":"{\"choice\":\"a\"}"}'
  ;;
esac
EOF
chmod +x "$stub"
export STUB_FAILS=$base/fails PYTHONDONTWRITEBYTECODE=1
export AGTERMCTL=$stub AGTERM_SESSION_ID=SESSION-1
unset AGTERM_SOCKET AGTERM_PANE_ID

# The stub exporter records its arguments and writes an SVG that names the diagram-design
# fonts in every spelling: quoted and not, in an attribute, in <style>, in a style attribute,
# in the font shorthand; and a label whose text is those names.
skill=$base/diagram-design
mkdir -p "$skill/scripts"
cat >"$skill/scripts/export_svg.py" <<'EOF'
import sys
from pathlib import Path

Path(sys.argv[0]).with_name("args").write_text("\n".join(sys.argv[1:]) + "\n")
Path(sys.argv[2]).write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 400">
<style>
  :root { --font-mono: 'Geist Mono', ui-monospace, monospace; --font-sans: "Geist", system-ui; }
  .t { font-family: Geist Mono, monospace; }
  .h { font: 600 14px 'Instrument Serif', serif; }
  .s { font: 12px/1.4 Geist, sans-serif; }
  .k { font-family: GeistMono; }
</style>
<text x="10" y="20" font-family="'Geist Mono', monospace">exported-mark</text>
<text x="10" y="40" font-family="Geist">sans</text>
<text x="10" y="60" font-family='"Instrument Serif"'>serif</text>
<text x="10" y="80" font-family="&quot;Geist Mono&quot;">entity</text>
<text x="10" y="100" style="font: 12px 'Geist Mono', monospace">inline</text>
<text x="10" y="120" font-family="Geist">Geist Mono, Geist and Instrument Serif</text>
</svg>
""")
EOF

frag=$base/fork-1.html
cat >"$frag" <<'EOF'
<main data-place="1 из 1" data-title="T" data-layout="columns">
<section data-today>
  <figure data-diagram="today.html"></figure>
  <p>today</p>
</section>
<article data-option="a" data-title="A"><p>a</p></article>
<article data-option="b" data-title="B"><p>b</p></article>
</main>
EOF
echo '<html><body><svg></svg></body></html>' >"$base/today.html"

failed=0
check() {
  local what=$1
  shift
  if "$@" >/dev/null 2>&1; then
    echo "ok   $what"
  else
    echo "FAIL $what"
    failed=$((failed + 1))
  fi
}

page=$base/fork-1.page.html
svg=$base/decoded.svg
# decode <page>: the first data-URI image of the page, decoded into $svg
decode() {
  python3 - "$1" "$svg" <<'EOF'
import base64, re, sys
from pathlib import Path
m = re.search(r'<img src="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)"', Path(sys.argv[1]).read_text())
Path(sys.argv[2]).write_bytes(base64.b64decode(m[1]))
EOF
}
# refused <expected text> <fork.py arguments after show>: exit 1, the reason on stderr, no page
refused() {
  local want=$1 err rc
  shift
  rm -f "$page"
  err=$(python3 "$fork" show "$frag" "$@" 2>&1 >/dev/null)
  rc=$?
  [ "$rc" -eq 1 ] && [[ $err == *"$want"* ]] && [ ! -e "$page" ]
}

check "the fork with a skill folder is answered" \
  test "$(python3 "$fork" show "$frag" --diagram-design "$skill" 2>/dev/null)" = '{"choice":"a"}'
check "the exporter of the passed folder ran on the linked file" \
  grep -qxF "$base/today.html" "$skill/scripts/args"
check "the exporter is asked for no font request" grep -qxF -- --system-fonts "$skill/scripts/args"
check "the page embeds the drawing as a data-URI image" \
  grep -qF '<figure class="diagram"><img src="data:image/svg+xml;base64,' "$page"
check "the link to the drawing is gone from the page" bash -c '! grep -q "data-diagram" "$0"' "$page"
check "the embedded image decodes" decode "$page"
check "the decoded image is the exported drawing" grep -qF exported-mark "$svg"
label='font-family="system-ui, -apple-system, sans-serif">Geist Mono, Geist and Instrument Serif</text>'
check "a label naming the fonts keeps its text, its attribute swapped" grep -qF "$label" "$svg"
check "no Geist, Geist Mono or Instrument Serif is left outside the label" \
  bash -c '! grep -vF "$1" "$0" | grep -Eiq "geist|instrument"' "$svg" "$label"
check "the mono stack replaced Geist Mono" grep -qF "ui-monospace, 'SF Mono', Menlo, monospace" "$svg"
check "the sans stack replaced Geist" grep -qF "system-ui, -apple-system, sans-serif" "$svg"
check "the serif stack replaced Instrument Serif" grep -qF "ui-serif, Georgia, serif" "$svg"
check "the image is still well-formed XML" \
  python3 -c 'import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])' "$svg"

check "without the skill folder the page is refused" refused "--diagram-design"
check "a folder without export_svg.py is refused" refused "no scripts/export_svg.py" \
  --diagram-design "$base/nowhere"
rm "$base/today.html"
check "a missing drawing is refused" refused "today.html is not a file" --diagram-design "$skill"

cat >"$frag" <<'EOF'
<main data-place="1 из 1" data-title="T"><article data-option="a" data-title="A"><p>a</p></article></main>
EOF
check "a fork without a drawing needs no skill folder" \
  test "$(python3 "$fork" show "$frag" 2>/dev/null)" = '{"choice":"a"}'

# Fragments the shell could not draw. Each is refused before a page is built.
roles='<script type="application/json" data-roles>{"a": {"x": 0, "y": 0, "label": "A"}, "b": {"x": 90, "y": 0, "label": "B"}}</script>'
# fragment <roles script> <flow JSON> [option id]: one option drawn as a flow
fragment() {
  cat >"$frag" <<EOF
<main data-place="1 из 1" data-title="T">
$1
<article data-option="${3:-a}" data-title="A">
  <script type="application/json" data-flow>$2</script>
  <p>a</p>
</article>
</main>
EOF
}
fragment "$roles" '{"nodes": {"a": "", "b": "new"}, "edges": [["a", "b", "new", 1]]}'
check "a flow over placed roles is answered" \
  test "$(python3 "$fork" show "$frag" 2>/dev/null)" = '{"choice":"a"}'
fragment '<script type="application/json" data-roles>{"a": {"x": 0, "y": 0, "label": "A"},}</script>' '{"nodes": {"a": ""}}'
check "roles that are not JSON are refused" refused "data-roles is not JSON"
fragment "$roles" '{"nodes": {"a": ""}, "edges": [["a", "b"]'
check "a flow that is not JSON is refused" refused "data-flow is not JSON"
fragment '<script type="application/json" data-roles>{"a": {"x": 0, "label": "A"}}</script>' '{"nodes": {"a": ""}}'
check "a role without its y is refused" refused "role 'a'"
fragment "$roles" '{"nodes": {"a": "", "gw": ""}}'
check "a node data-roles does not place is refused" refused "role 'gw'"
fragment "$roles" '{"nodes": {"a": ""}, "edges": [["a", "reg", "new", 1]]}'
check "an edge to a role data-roles does not place is refused" refused "role 'reg'"
fragment "" '{"nodes": {"a": ""}}'
check "a flow without data-roles is refused" refused "role 'a'"
for id in own explain today general; do
  fragment "$roles" '{"nodes": {"a": ""}}' "$id"
  check "the option id '$id' the page keeps for itself is refused" refused "option id '$id'"
done
fragment "$roles" '{"nodes": {"a": ""}, "edges": [["a", "a", "new", 1]]}'
check "an edge from a role to itself is refused" refused "to itself"
fragment '<script type="application/json" data-roles>{"a": {"x": NaN, "y": 0, "label": "A"}}</script>' '{"nodes": {"a": ""}}'
check "roles with NaN, which JSON.parse refuses, are refused" refused "NaN"
fragment "$roles" '{"nodes": {"a": ""}, "edges": [["a", "b", "new", Infinity]]}'
check "a flow with Infinity is refused" refused "Infinity"
fragment "$roles$roles" '{"nodes": {"a": ""}}'
check "two data-roles scripts are refused" refused "one data-roles"
cat >"$frag" <<EOF
$roles
<main data-place="1 из 1" data-title="T">
<article data-option="a" data-title="A">
  <script type="application/json" data-flow>{"nodes": {"a": ""}}</script>
</article>
</main>
EOF
check "a data-roles script outside the data-place root is refused" refused "inside the data-place root"

# Attribute values and prose that name data-diagram or data-option are not links or option ids.
cat >"$frag" <<'EOF'
<main data-place="1 из 1" data-title="A data-diagram link is a figure">
<article data-option="a" data-title="See data-diagram"><p>The id in data-option="own" is kept by the page.</p></article>
</main>
EOF
check "an attribute value or text naming data-diagram or data-option is answered" \
  test "$(python3 "$fork" show "$frag" 2>/dev/null)" = '{"choice":"a"}'

# Drawing links fork.py cannot embed are refused, not dropped from the picture.
echo '<html><body><svg></svg></body></html>' >"$base/today.html"
cat >"$frag" <<'EOF'
<main data-place="1 из 1" data-title="T">
<section data-today><figure data-diagram=today.html></figure><p>today</p></section>
<article data-option="a" data-title="A"><p>a</p></article>
</main>
EOF
check "an unquoted drawing link is refused" refused "data-diagram" --diagram-design "$skill"
cat >"$frag" <<'EOF'
<main data-place="1 из 1" data-title="T">
<section data-today><figure data-diagram="today.html"><figcaption>c</figcaption></figure><p>today</p></section>
<article data-option="a" data-title="A"><p>a</p></article>
</main>
EOF
check "a drawing link with content inside is refused" refused "data-diagram" --diagram-design "$skill"

# poll: show the plain fragment with no pause between reads of the answer
cat >"$frag" <<'EOF'
<main data-place="1 из 1" data-title="T"><article data-option="a" data-title="A"><p>a</p></article></main>
EOF
poll() {
  python3 - "$fork" "$frag" <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
import fork
fork.POLL_SECONDS = 0
sys.exit(fork.main(["fork.py", "show", sys.argv[2]]))
EOF
}
echo 3 >"$STUB_FAILS"
check "a read of the answer that fails a few times is retried" test "$(poll 2>/dev/null)" = '{"choice":"a"}'
echo 1000 >"$STUB_FAILS"
out=$(poll 2>/dev/null)
rc=$?
check "a read that keeps failing ends with exit 3" test "$rc" -eq 3
check "a read that keeps failing prints the page id" test "$out" = PAGE-1
rm -f "$STUB_FAILS"

# result: read the answer of PAGE-1 once, with no pause between retries
result() {
  python3 - "$fork" <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
import fork
fork.POLL_SECONDS = 0
sys.exit(fork.main(["fork.py", "result", "PAGE-1"]))
EOF
}
echo 3 >"$STUB_FAILS"
check "result retries a read that fails a few times" test "$(result 2>/dev/null)" = '{"choice":"a"}'
echo 1000 >"$STUB_FAILS"
err=$(result 2>&1 >/dev/null)
rc=$?
check "result that keeps failing ends with exit 1" test "$rc" -eq 1
check "result that keeps failing says to read again, not to show" \
  bash -c '[[ $0 == *"fork.py result PAGE-1"* ]]' "$err"
rm -f "$STUB_FAILS"

[ "$failed" -eq 0 ] || { echo "$failed failed"; exit 1; }
echo "all passed"
