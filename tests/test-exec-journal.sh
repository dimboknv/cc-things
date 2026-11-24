#!/usr/bin/env bash
# The exec-plan scripts take the run's journal from EXEC_PLAN_JOURNAL and refuse without it; a run
# over two repositories with its plan outside git keeps one journal beside the plan, a base per
# repository, and a status page that shows a running lane's ticks from its lanes/task-<N>.md and
# finds the plan again after the close moved it.
#
# Every check runs and reports; the script exits non-zero when any failed. EXEC_SCRIPTS points it
# at another copy of the scripts.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
scripts=${EXEC_SCRIPTS:-$here/../plugins/planning/skills/exec-plan/scripts}
scripts=$(cd "$scripts" && pwd)

base=$(mktemp -d)
base=$(cd "$base" && pwd -P)
trap 'rm -rf "$base"' EXIT

# Nothing here may reach the owner's agterm, Claude Code transcripts or git configuration.
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
# refuses <command>...: non-zero, and the reason names EXEC_PLAN_JOURNAL
refuses() {
  local err
  if err=$("$@" 2>&1 >/dev/null); then
    return 1
  fi
  grep -q EXEC_PLAN_JOURNAL <<<"$err"
}

ws=$base/ws
slug=multi
for repo in lib app; do
  git init -q "$ws/$repo"
  echo "$repo" >"$ws/$repo/README"
  [ "$repo" = app ] && printf 'module example.com/app\n\ngo 1.22\n' >"$ws/app/go.mod"
  git -C "$ws/$repo" add -A
  git -C "$ws/$repo" commit -qm init
  git -C "$ws/$repo" worktree add -q -b "feat/$slug" ".claude/worktrees/$slug" main
done
git -C "$ws/lib" worktree add -q -b "feat/$slug-task-1" ".claude/worktrees/$slug-task-1" "feat/$slug"
git -C "$ws/app" worktree add -q -b "feat/$slug-task-2" ".claude/worktrees/$slug-task-2" "feat/$slug"

plans=$base/plans
plan=$plans/2026-11-24-$slug.md
journal=$plans/.exec-plan/$slug
mkdir -p "$plans" "$journal/lanes"
cat >"$plan" <<'EOF'
# Two repositories

## Implementation Steps

### Task 1: change the library

Where: `src/`.

Repo: `lib`.

- [ ] one
- [ ] two
- [ ] three

### Task 2: use the library

Where: `cmd/`.

Repo: `app`.

- [ ] alpha
- [ ] beta
EOF
echo "$plan" >"$journal/plan"
for repo in lib app; do
  echo "$repo $ws/$repo $ws/$repo/.claude/worktrees/$slug feat/$slug"
done >"$journal/repos"
cat >"$journal/lanes/task-1.md" <<'EOF'
### Task 1: change the library

Where: `src/`.

Repo: `lib`.

- [x] one
- [x] two
- [ ] three
EOF
cat >"$journal/lanes/task-2.md" <<'EOF'
### Task 2: use the library

Where: `cmd/`.

Repo: `app`.

- [x] alpha
- [ ] beta
EOF

export EXEC_PLAN_JOURNAL=$journal
run_lib=$ws/lib/.claude/worktrees/$slug
run_app=$ws/app/.claude/worktrees/$slug

# --- refusals: unset, then relative -----------------------------------------------------------
in_lib() { (cd "$run_lib" && "$@"); }
for how in unset relative; do
  if [ "$how" = unset ]; then
    env=(env -u EXEC_PLAN_JOURNAL)
  else
    env=(env EXEC_PLAN_JOURNAL=plans/.exec-plan/$slug)
  fi
  check "progress.sh refuses a journal $how" refuses in_lib "${env[@]}" "$scripts/progress.sh" "a line"
  check "base.sh refuses a journal $how" refuses in_lib "${env[@]}" "$scripts/base.sh" lib main
  check "status.py refuses a journal $how" refuses in_lib "${env[@]}" python3 "$scripts/status.py"
  check "audit.py refuses a journal $how" refuses in_lib "${env[@]}" python3 "$scripts/audit.py"
  check "cache.sh refuses a journal $how" refuses in_lib "${env[@]}" bash -c '. "$1"' _ "$scripts/cache.sh"
done

# --- progress.sh ------------------------------------------------------------------------------
in_lib "$scripts/progress.sh" "run started: $plan, $run_lib, base x" >/dev/null 2>&1
check "progress.sh appends a timestamped line to progress.md" \
  grep -Eq '^\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:]{8}\] run started: ' "$journal/progress.md"
check "the run-started line draws the page" test -f "$journal/status.html"

# --- base.sh ----------------------------------------------------------------------------------
(cd "$run_lib" && "$scripts/base.sh" lib main) >/dev/null 2>&1
(cd "$run_app" && "$scripts/base.sh" app main) >/dev/null 2>&1
check "base.sh records base.lib at the lib trunk commit" \
  test "$(cat "$journal/base.lib" 2>/dev/null)" = "$(git -C "$ws/lib" rev-parse main)"
check "base.sh records base.app at the app trunk commit" \
  test "$(cat "$journal/base.app" 2>/dev/null)" = "$(git -C "$ws/app" rev-parse main)"
check "base.sh accepts its own recorded base again" in_lib "$scripts/base.sh" lib main
check "base.sh refuses a trunk that does not exist" bash -c '! (cd "$1" && "$2" lib nosuch)' _ "$run_lib" "$scripts/base.sh"
echo more >>"$ws/lib/README"
git -C "$ws/lib" commit -qam "trunk moves on"
git -C "$run_lib" rebase -q main
check "base.sh refuses a base a rebase moved" bash -c '! (cd "$1" && "$2" lib main)' _ "$run_lib" "$scripts/base.sh"
check "the refused base stays recorded" \
  test "$(cat "$journal/base.lib" 2>/dev/null)" = "$(git -C "$ws/lib" rev-parse main~1)"

# --- cache.sh ---------------------------------------------------------------------------------
lane_lib=$ws/lib/.claude/worktrees/$slug-task-1
caches=$(cd "$lane_lib" && bash -c '. "$1" && echo "$GOCACHE $GOLANGCI_LINT_CACHE"' _ "$scripts/cache.sh" 2>/dev/null)
check "cache.sh puts the Go cache and the lane's lint cache under the journal" \
  test "$caches" = "$journal/cache/go-build $journal/cache/lint/lib/$slug-task-1"
lint_app=$(cd "$run_app" && bash -c '. "$1" && echo "$GOLANGCI_LINT_CACHE"' _ "$scripts/cache.sh" 2>/dev/null)
check "cache.sh keys the lint cache by repository, so run worktrees of one name do not share it" \
  test "$lint_app" = "$journal/cache/lint/app/$slug"

# --- status.py: a running lane's ticks come from its lanes file -------------------------------
# The lead session started in the directory that holds both repositories, not beside the plan.
lead=lead-1
project=$CLAUDE_CONFIG_DIR/projects/$(printf '%s' "$ws" | sed 's/[^A-Za-z0-9]/-/g')
mkdir -p "$project/$lead/subagents"
echo "$lead" >"$journal/lead"
in_lib "$scripts/progress.sh" "wave 1: started, tasks 1, 2" >/dev/null 2>&1
now=$(date -u +%Y-%m-%dT%H:%M:%S.999Z)
cat >"$project/$lead.jsonl" <<EOF
{"type":"assistant","timestamp":"$now","message":{"id":"l1","model":"claude-test-lead","usage":{"input_tokens":10,"output_tokens":1},"content":[]}}
EOF
cat >"$project/$lead/subagents/agent-a1.jsonl" <<EOF
{"type":"user","timestamp":"$now","message":{"role":"user","content":"You are executing ONE task of a plan. Your progress file: $journal/lanes/task-1.md"}}
{"type":"assistant","timestamp":"$now","message":{"id":"m1","model":"claude-test-lane","usage":{"input_tokens":1000,"output_tokens":50},"content":[{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"go build ./...","description":"build"}}]}}
EOF
(cd "$run_app" && python3 "$scripts/status.py") >/dev/null 2>&1
page=$journal/status.html
check "the page shows task 1 at 2/3 from lanes/task-1.md, the plan says 0/3" grep -q ">2/3<" "$page"
check "the page shows task 2 at 1/2 from lanes/task-2.md, the plan says 0/2" grep -q ">1/2<" "$page"
check "the page names each task's repository" grep -q "task 1 (lib): change the library" "$page"
check "the page lists the repositories with their branch" grep -q "<td>app</td><td>feat/$slug</td>" "$page"
check "the page counts the lane found through the lead's project directory" grep -q "test-lane" "$page"

# --- status.py: the whole-tree checks, review rounds and finalize per repository --------------
cat >"$project/$lead/subagents/agent-f1.jsonl" <<EOF
{"type":"user","timestamp":"$now","message":{"role":"user","content":"You are sorting and fixing what review round app/01-initial found. Journal: $journal"}}
{"type":"assistant","timestamp":"$now","message":{"id":"f1","model":"claude-test-fixer","usage":{"input_tokens":333000,"output_tokens":5},"content":[]}}
EOF
progress() { in_lib "$scripts/progress.sh" "$1" >/dev/null 2>&1; }
progress "wave 1: integrated, clean"
progress "whole tree: lib: started"
progress "whole tree: lib: green, make test"
check "one repository green is not the whole run green" grep -q "<b>whole tree: lib green</b>" "$page"
progress "whole tree: app: started"
progress "whole tree: app: red, go vet"
check "the whole-tree check shows a row per repository" \
  grep -q "<tr><td>lib</td><td class='at'>[0-9:]*</td><td class='num'>[^<]*</td><td>green, make test</td>" "$page"
progress "whole tree: app: started"
progress "whole tree: app: green, go vet"
check "every repository green sends the run to review" grep -q "<b>whole tree green, review next</b>" "$page"
progress "review round app/01-initial: comprehensive, 0 critical, 1 major, 2 minor, fixer"
progress "review app/01-initial, profile comprehensive: fixed 1, open 0, dropped 0"
check "a review round shows its repository and run" grep -q "<td>app</td><td class='n'>01-initial</td>" "$page"
check "the round's fixer is matched by repository and run" grep -q ">333k<" "$page"
progress "finalize: lib: regrouped into 2 commits"
check "a finalize line shows its repository" grep -q "<td>lib</td><td>regrouped into 2 commits</td>" "$page"

# --- status.py: the plan outside git, closed with a plain mv ----------------------------------
mkdir -p "$plans/completed"
closed=$plans/completed/$(basename "$plan")
mv "$plan" "$closed"
in_lib "$scripts/progress.sh" "finalize: plan closed, $closed" >/dev/null 2>&1
check "the page follows the plan to where the close moved it" grep -q "task 2 (app): use the library" "$page"
check "the page shows the run closed" grep -q "<b>closed</b>" "$page"

# --- audit.py ---------------------------------------------------------------------------------
audit=$(cd "$base" && python3 "$scripts/audit.py" 2>&1)
check "audit.py reads the run's lane and applies the Go rule of a repository with a go.mod" \
  grep -q "^shared-cache: " <<<"$audit"

# --- no watcher left behind -------------------------------------------------------------------
check "no status watcher was started" test ! -e "$journal/status-watch"

if [ "$failed" -ne 0 ]; then
  echo "$failed checks failed"
  exit 1
fi
echo "all checks passed"
