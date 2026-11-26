#!/usr/bin/env bash
# Stages the named paths and commits the index as it stands. The commit takes no pathspec, so the
# hooks run against the real index and a file a pre-commit hook stages lands in the commit; a
# path-scoped commit runs them on a temporary index and what they stage never reaches the real one.
# Before staging, the index must hold nothing but the named paths: another session's staged work
# never rides along, and a refusal stages nothing.
#
# usage: commit.sh <message> <path>...
#   message   the whole commit message as one argument, subject first, trailers last
#   path      relative to the current directory; a tracked path gone from the tree, after rm or
#             mv, stages its removal. Not after git rm or git mv: those take the path out of the
#             index first, and git add of it then matches nothing
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") <message> <path>..." >&2
  exit 2
}
refuse() {
  echo "commit.sh: $*" >&2
  exit 1
}

[ $# -ge 2 ] || usage
message="$1"
shift
[ -n "$message" ] || refuse "empty message"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || refuse "not inside a git work tree"

# An empty pathspec matches the whole tree, and a glob character in a name would match other names.
literal=()
for path in "$@"; do
  [ -n "$path" ] || refuse "empty path argument"
  literal+=(":(literal)$path")
done

staged="$(git diff --cached --name-only --no-renames | sort)"
named="$(git diff --cached --name-only --no-renames -- "${literal[@]}" | sort)"
if [ "$staged" != "$named" ]; then
  echo "commit.sh: the index holds paths this commit does not name:" >&2
  comm -23 <(printf '%s\n' "$staged") <(printf '%s\n' "$named") | sed 's/^/  /' >&2
  echo "unstage them with 'git restore --staged -- <path>' or name them, then run again" >&2
  exit 1
fi

git add -- "${literal[@]}"

# The pre-commit hooks build and lint. Under EXEC_PLAN_JOURNAL they use the run's caches; without
# it cache.sh sets nothing and the environment stays as it was.
# shellcheck source=/dev/null
. "$(dirname "$0")/cache.sh" 2>/dev/null || true

git commit -m "$message"
