#!/usr/bin/env bash
# Records the base commit of a plan run in the run's journal, in the main checkout. The review
# range, the history regroup and the revdiff of the run all start at this commit.
#
# usage: base.sh <slug> [trunk]
#   trunk   the branch the run was cut from, as the Trunk section of the project rules names it;
#           without it, the branch origin/HEAD points at, else main, else master
#
# The base is the trunk commit the run's branch was cut from. A merge commit between the base
# and HEAD is refused, because the regroup flattens the range, and so is a recorded base the
# tree no longer matches, because a rebase or a merge by hand has moved what the run stands on.
set -euo pipefail

usage() {
  echo "usage: $(basename "$0") <slug> [trunk]" >&2
  exit 2
}
refuse() {
  echo "base.sh: $*" >&2
  exit 1
}

[ $# -eq 1 ] || [ $# -eq 2 ] || usage
slug="$1"
trunk="${2:-}"
case "$slug" in
  '' | */* | . | ..) refuse "bad slug '$slug'" ;;
esac
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || refuse "not inside a git work tree"

if [ -z "$trunk" ]; then
  trunk="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  trunk="${trunk#origin/}"
  if [ -z "$trunk" ]; then
    for candidate in main master; do
      if git show-ref --verify --quiet "refs/heads/$candidate"; then
        trunk="$candidate"
        break
      fi
    done
  fi
  [ -n "$trunk" ] || refuse "no trunk given, origin/HEAD is not set, and neither main nor master exists"
fi
git rev-parse --verify --quiet "$trunk^{commit}" >/dev/null || refuse "no branch '$trunk'"

base="$(git merge-base "$trunk" HEAD)" || refuse "$trunk and HEAD share no commit"

merges="$(git rev-list --merges "$base..HEAD")"
[ -z "$merges" ] || refuse "merge commits between $base and HEAD: $(printf '%s' "$merges" | tr '\n' ' ')"

common="$(git rev-parse --git-common-dir)"
main="$(cd "$common/.." && pwd -P)"
dir="$main/.exec-plan/$slug"
file="$dir/base"
if [ -f "$file" ]; then
  recorded="$(cat "$file")"
  [ "$recorded" = "$base" ] || refuse "the recorded base $recorded differs from the computed $base: the branch was rebased or merged by hand since the run started; remove $file to accept the new base"
fi
mkdir -p "$dir"
printf '%s\n' "$base" >"$file"
echo "$base"
