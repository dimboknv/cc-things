#!/usr/bin/env bash
# A light run of a plan tracked in its repository: the journal's plan file names the plan's copy
# in the run worktree, the single executor ticks it there, and no lanes/ file exists, so status.py
# reads a running task's ticks from the plan.
#
# EXEC_SCRIPTS points it at another copy of the scripts.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
scripts=${EXEC_SCRIPTS:-$here/../plugins/planning/skills/exec-plan/scripts}
scripts=$(cd "$scripts" && pwd)

base=$(mktemp -d)
base=$(cd "$base" && pwd -P)
trap 'rm -rf "$base"' EXIT

unset AGTERM_SESSION_ID CLAUDE_CODE_SESSION_ID EXEC_PLAN_JOURNAL
export AGTERMCTL=/usr/bin/false
export CLAUDE_CONFIG_DIR="$base/claude"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL="$base/gitconfig"
git config --file "$GIT_CONFIG_GLOBAL" user.name t
git config --file "$GIT_CONFIG_GLOBAL" user.email t@t
git config --file "$GIT_CONFIG_GLOBAL" init.defaultBranch main

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

slug=solo
main=$base/svc
rel=docs/plans/2026-11-24-$slug.md
git init -q "$main"
mkdir -p "$main/docs/plans"
cat >"$main/$rel" <<'EOF'
## Implementation Steps

### Task 1: first

Where: `a/`.

- [ ] one
- [ ] two
EOF
git -C "$main" add -A
git -C "$main" commit -qm plan
run=$main/.claude/worktrees/$slug
git -C "$main" worktree add -q -b "feat/$slug" "$run" main
sed -i.bak 's/- \[ \] one/- [x] one/' "$run/$rel" && rm "$run/$rel.bak"
git -C "$run" commit -qam "tick one"

journal=$main/.exec-plan/$slug
mkdir -p "$journal"
echo "$run/$rel" >"$journal/plan"
echo "svc $main $run feat/$slug" >"$journal/repos"
export EXEC_PLAN_JOURNAL=$journal

(cd "$run" && "$scripts/progress.sh" "run started: $run/$rel, $run, base x") >/dev/null 2>&1
(cd "$run" && "$scripts/progress.sh" "wave 1: started, tasks 1") >/dev/null 2>&1
page=$journal/status.html
check "a light run's running task shows the plan's ticks" grep -q ">1/2<" "$page"
check "the task is shown running" grep -q "lane running" "$page"
check "one repository: a task's name carries no repository" grep -q "task 1: first" "$page"

if [ "$failed" -ne 0 ]; then
  echo "$failed checks failed"
  exit 1
fi
echo "all checks passed"
