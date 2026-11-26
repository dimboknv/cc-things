#!/usr/bin/env bash
# Runs the planning eval suite against a temporary layout of the plugins it needs.
#
# `claude plugin eval` loads only the plugins under test, so planning's declared
# dependencies are missing there and the plugin does not load at all. A case's
# `plugins` list replaces the plugin under test rather than adding to it, and it
# may not name a directory that holds the case. So the suite runs from a
# temporary directory that holds a copy of planning with no `dependencies`, a
# copy of the installed diagram-design, and the cases, each listing both
# plugins. The repository's manifest is never touched.
#
# Usage: plugins/planning/evals/run.sh [claude plugin eval flags...]
# Results land in plugins/planning/evals/results/ of this checkout.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
plugin=$(cd "$here/.." && pwd)
cache=${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/cache/diagram-design/diagram-design

dd=$(ls -d "$cache"/*/ 2>/dev/null | sort -V | tail -1 || true)
[ -n "$dd" ] && [ -f "$dd/.claude-plugin/plugin.json" ] \
  || { echo "run.sh: diagram-design is not installed under $cache" >&2; exit 1; }

suite=$(mktemp -d)
trap 'rm -rf "$suite"' EXIT
rsync -a --exclude 'evals/' "$plugin/" "$suite/planning/"
rsync -a --exclude '.git/' "$dd" "$suite/diagram-design/"
rsync -a --exclude 'run.sh' --exclude 'results/' "$here/" "$suite/evals/"

python3 - "$suite" <<'PY'
import json, pathlib, re, sys
suite = pathlib.Path(sys.argv[1])
manifest = suite / "planning" / ".claude-plugin" / "plugin.json"
data = json.loads(manifest.read_text())
data.pop("dependencies", None)
manifest.write_text(json.dumps(data, indent=2) + "\n")
for prompt in (suite / "evals").glob("*/prompt.md"):
    head, sep, body = prompt.read_text().partition("\n---\n")
    head = re.sub(r"^plugins:.*\n?", "", head, flags=re.M)
    head += '\nplugins: ["../../planning", "../../diagram-design"]'
    prompt.write_text(head + sep + body)
PY

status=0
claude plugin eval "$suite" --allow-tools Write --ablation none "$@" || status=$?
if [ -d "$suite/evals/results" ]; then
  mkdir -p "$here/results"
  rsync -a "$suite/evals/results/" "$here/results/"
fi
exit "$status"
