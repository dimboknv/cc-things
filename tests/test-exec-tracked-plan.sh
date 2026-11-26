#!/usr/bin/env bash
# A light run of a plan tracked in its repository: the journal's plan file names the plan's copy
# in the run worktree, the single executor ticks it there, and no lanes/ file exists, so status.py
# reads a running task's ticks from the plan and shows the executor on a row of its own. A stop
# line ends the run on the page.
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
(cd "$run" && "$scripts/progress.sh" "light run: one executor, one small task") >/dev/null 2>&1
(cd "$run" && "$scripts/progress.sh" "wave 1: started, tasks 1") >/dev/null 2>&1
project=$CLAUDE_CONFIG_DIR/projects/$(printf '%s' "$main" | sed 's/[^A-Za-z0-9]/-/g')
mkdir -p "$project/lead-1/subagents"
now=$(date -u +%Y-%m-%dT%H:%M:%S.999Z)
cat >"$project/lead-1/subagents/agent-x1.jsonl" <<EOF
{"type":"user","timestamp":"$now","message":{"role":"user","content":"You are executing ONE task of a plan as one lane of a wave.\n- checkout: $run (run every command from here)"}}
{"type":"assistant","timestamp":"$now","message":{"id":"x1","model":"claude-test-light","usage":{"input_tokens":777000,"output_tokens":1},"content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"go test ./a/...","description":"test the package"}}]}}
EOF
(cd "$run" && python3 "$scripts/status.py") >/dev/null 2>&1
page=$journal/status.html
check "a light run's running task shows the plan's ticks" grep -q ">1/2<" "$page"
check "the task is shown running" grep -q "lane running" "$page"
check "one repository: a task's name carries no repository" grep -q "task 1: first" "$page"
check "the executor has a row with its tokens" grep -q "<td>executor</td>.*>777k<" "$page"
check "the executor's call in progress shows" grep -q "test the package" "$page"
check "a running run has live timers" grep -q "class='tick'" "$page"

(cd "$run" && "$scripts/progress.sh" "run stopped: wave 1: 1") >/dev/null 2>&1
check "a run-stopped line puts the run in phase stopped" grep -q "<b>stopped</b>" "$page"
check "a stopped run has no live timer" bash -c '! grep -q "class=.tick" "$1"' _ "$page"

if [ "$failed" -ne 0 ]; then
  echo "$failed checks failed"
  exit 1
fi
echo "all checks passed"
