#!/usr/bin/env bash
# Appends one timestamped line to the run's journal in the main checkout. The journal is only ever
# appended to: a rerun continues the record of the first run.
#
# usage: progress.sh <slug> <line>...
#   line   the words of the line; several arguments are joined with spaces
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") <slug> <line>..." >&2
  exit 2
}
refuse() {
  echo "progress.sh: $*" >&2
  exit 1
}

[ $# -ge 2 ] || usage
slug="$1"
shift
case "$slug" in
  '' | */* | . | ..) refuse "bad slug '$slug'" ;;
esac
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || refuse "not inside a git work tree"

common="$(git rev-parse --git-common-dir)"
main="$(cd "$common/.." && pwd -P)"
dir="$main/.exec-plan/$slug"
mkdir -p "$dir"
printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$dir/progress.md"

# The status page is a view of the journal, so a page that cannot be drawn never fails the write.
# The line that starts or continues a run is the one that opens the page. A report is a dozen
# lines written in a row, and its detail lines, decisions and deviations change nothing the page
# shows but a count, so they wait for the next line that does.
case "$*" in
  'run started'* | 'run continued'*) open=--open ;;
  '- '* | '[decision]'* | '[deviation]'*) exit 0 ;;
  *) open= ;;
esac
python3 "$(dirname "$0")/status.py" "$slug" ${open:+"$open"} >/dev/null 2>&1 || true
