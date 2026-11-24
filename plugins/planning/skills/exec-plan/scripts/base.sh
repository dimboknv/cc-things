#!/usr/bin/env bash
# Records the base commit of one repository of a plan run in the run's journal, the directory
# EXEC_PLAN_JOURNAL names, as base.<repo>. The review range, the history regroup and the revdiff
# of that repository all start at this commit.
#
# usage: EXEC_PLAN_JOURNAL=<journal> base.sh <repo> <trunk>
#   repo    the repository's directory name, as the journal's repos file and a task's Repo: line
#           name it
#   trunk   the branch the run was cut from, as the Trunk section of the project rules names it
#
# Run inside that repository's run worktree. The base is the trunk commit the run's branch was cut
# from. A merge commit between the base and HEAD is refused, because the regroup flattens the
# range, and so is a recorded base the tree no longer matches, because a rebase or a merge by hand
# has moved what the run stands on.
set -euo pipefail

usage() {
  echo "usage: EXEC_PLAN_JOURNAL=<journal> $(basename "$0") <repo> <trunk>" >&2
  exit 2
}
refuse() {
  echo "base.sh: $*" >&2
  exit 1
}

journal="${EXEC_PLAN_JOURNAL:-}"
case "$journal" in
  '') refuse "EXEC_PLAN_JOURNAL is not set" ;;
  /*) ;;
  *) refuse "EXEC_PLAN_JOURNAL is not an absolute path: '$journal'" ;;
esac
[ $# -eq 2 ] || usage
repo="$1"
trunk="$2"
case "$repo" in
  '' | */* | . | ..) refuse "bad repo name '$repo'" ;;
esac
[ -n "$trunk" ] || refuse "empty trunk"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || refuse "not inside a git work tree"
git rev-parse --verify --quiet "$trunk^{commit}" >/dev/null || refuse "no branch '$trunk'"

base="$(git merge-base "$trunk" HEAD)" || refuse "$trunk and HEAD share no commit"

merges="$(git rev-list --merges "$base..HEAD")"
[ -z "$merges" ] || refuse "merge commits between $base and HEAD: $(printf '%s' "$merges" | tr '\n' ' ')"

file="$journal/base.$repo"
if [ -f "$file" ]; then
  recorded="$(cat "$file")"
  [ "$recorded" = "$base" ] || refuse "the recorded base $recorded differs from the computed $base: the branch was rebased or merged by hand since the run started; remove $file to accept the new base"
fi
mkdir -p "$journal"
printf '%s\n' "$base" >"$file"
echo "$base"
