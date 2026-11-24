#!/usr/bin/env bash
# Appends one timestamped line to the run's journal, the directory EXEC_PLAN_JOURNAL names. The
# journal is only ever appended to: a rerun continues the record of the first run.
#
# usage: EXEC_PLAN_JOURNAL=<journal> progress.sh <line>...
#   line   the words of the line; several arguments are joined with spaces
set -euo pipefail

usage() {
  echo "usage: EXEC_PLAN_JOURNAL=<journal> $(basename "$0") <line>..." >&2
  exit 2
}
refuse() {
  echo "progress.sh: $*" >&2
  exit 1
}

journal="${EXEC_PLAN_JOURNAL:-}"
case "$journal" in
  '') refuse "EXEC_PLAN_JOURNAL is not set" ;;
  /*) ;;
  *) refuse "EXEC_PLAN_JOURNAL is not an absolute path: '$journal'" ;;
esac
[ $# -ge 1 ] || usage

mkdir -p "$journal"
printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$journal/progress.md"

# The status page is a view of the journal, so a page that cannot be drawn never fails the write.
# The line that starts or continues a run is the one that opens the page. A report is a dozen
# lines written in a row, and its detail lines, decisions and deviations change nothing the page
# shows but a count, so they wait for the next line that does.
case "$*" in
  'run started'* | 'run continued'*) open=--open ;;
  '- '* | '[decision]'* | '[deviation]'*) exit 0 ;;
  *) open= ;;
esac
python3 "$(dirname "$0")/status.py" ${open:+"$open"} >/dev/null 2>&1 || true
