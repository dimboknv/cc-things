#!/usr/bin/env bash
# The exec-plan scripts take the run's journal from EXEC_PLAN_JOURNAL and refuse without it; a run
# over two repositories with tasks and a third with none, its plan outside git, keeps one journal
# beside the plan, a base per repository, and a status page that shows a running lane's ticks from
# its lanes/task-<N>.md and finds the plan again after the close moved it.
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
for repo in lib app notes; do
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
for repo in lib app notes; do
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
check "base.sh refuses a repository name that is not the checkout's" \
  bash -c '! (cd "$1" && "$2" app main)' _ "$run_lib" "$scripts/base.sh"
check "the refused name gets no base" test ! -e "$journal/base.app"
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

# A submodule keeps its git directory under the superproject's .git/modules, so the repository is
# named by its main checkout, the first entry of git worktree list.
git init -q "$base/super"
git -C "$base/super" -c protocol.file.allow=always submodule -q add "$ws/notes" notes 2>/dev/null
git -C "$base/super/notes" worktree add -q -b "feat/$slug" ".claude/worktrees/$slug" main
sub_run=$base/super/notes/.claude/worktrees/$slug
check "base.sh takes a submodule by its checkout's name" \
  env EXEC_PLAN_JOURNAL="$base/sub-journal" bash -c 'cd "$1" && "$2" notes main' _ "$sub_run" "$scripts/base.sh"
check "base.sh still refuses another repository's name in a submodule" \
  env EXEC_PLAN_JOURNAL="$base/sub-journal" bash -c '! (cd "$1" && "$2" lib main)' _ "$sub_run" "$scripts/base.sh"

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

# A transcript whose first line carries no time is left out, and the page is still drawn.
cat >"$project/$lead/subagents/agent-a0.jsonl" <<EOF
{"type":"user","message":{"role":"user","content":"You are executing ONE task of a plan. Your progress file: $journal/lanes/task-2.md"}}
EOF
check "a transcript with no time on its first line does not stop the page" \
  bash -c 'cd "$1" && python3 "$2"' _ "$run_app" "$scripts/status.py"
rm "$project/$lead/subagents/agent-a0.jsonl"

# The wave line names its tasks by number; one that adds a repository or a title reads the same.
other=$plans/.exec-plan/listed
# journal_of <line>...: a journal beside the run's, with its plan and repos, that holds the lines
journal_of() {
  rm -rf "$other"
  mkdir -p "$other"
  cp -R "$journal/plan" "$journal/repos" "$other/"
  local stamp line
  stamp=$(date '+%Y-%m-%d %H:%M:%S')
  for line in "run started: $plan" "$@"; do
    printf '[%s] %s\n' "$stamp" "$line"
  done >"$other/progress.md"
}
for listed in "1 (lib), 2 (app)" "1: change the library, 2: use the library" "1 2" "1 and 2"; do
  journal_of "wave 1: started, tasks $listed"
  cp -R "$journal/lanes" "$other/"
  EXEC_PLAN_JOURNAL=$other python3 "$scripts/status.py" >/dev/null 2>&1
  check "the wave line 'tasks $listed' runs both lanes" \
    test "$(grep -o 'lane running' "$other/status.html" | wc -l | tr -d ' ')" = 2
done
check "a number inside a task's title is not a task" \
  test "$(python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import status; print(status.wave_tasks(sys.argv[2]))' \
    "$scripts" "1: try 3 times, 2 retries, 4: use it")" = "[1, 4]"

# A light run has one executor and no integrator, before and after its one wave ends.
journal_of "light run: one executor, small" "wave 1: started, tasks 1, 2" "task 1: done" "task 2: done"
EXEC_PLAN_JOURNAL=$other python3 "$scripts/status.py" >/dev/null 2>&1
check "a light run with every task back is not integrating" \
  bash -c '! grep -Eq "integrating|<td>integrator</td>" "$1"' _ "$other/status.html"
printf '[%s] wave 1: integrated, light run, no integrator\n' "$(date '+%Y-%m-%d %H:%M:%S')" >>"$other/progress.md"
EXEC_PLAN_JOURNAL=$other python3 "$scripts/status.py" >/dev/null 2>&1
check "a light run's integrated wave has no integrator row" \
  bash -c '! grep -q "<td>integrator</td>" "$1"' _ "$other/status.html"

# A continuation checks every repository again: an old green does not count.
journal_of "wave 1: started, tasks 1, 2" "wave 1: integrated, clean" \
  "whole tree: lib: green, make test" "whole tree: app: green, go vet" "run stopped: review" \
  "run continued" "whole tree: lib: started" "whole tree: lib: green, make test"
EXEC_PLAN_JOURNAL=$other python3 "$scripts/status.py" >/dev/null 2>&1
check "after a continuation one repository green is not the whole run green" \
  grep -q "<b>whole tree: lib green</b>" "$other/status.html"
rm -rf "$other"

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
# notes holds only the plan's commits, so it is skipped and never logs a check
check "every repository with a task green sends the run to review" \
  grep -q "<b>whole tree green, review next</b>" "$page"
progress "review round app/01-initial: comprehensive, 0 critical, 1 major, 2 minor, fixer"
progress "review app/01-initial, profile comprehensive: fixed 1, open 0, dropped 0"
check "a review round shows its repository and run" grep -q "<td>app</td><td class='n'>01-initial</td>" "$page"
check "the round's fixer is matched by repository and run" grep -q ">333k<" "$page"
progress "review round lib/01-initial: claude-only, 0 critical, 1 major, 0 minor, fixer"
progress "review lib/01-initial, profile claude-only: fixed 1, open 0, dropped 0"
check "a fixer's line under a profile with a dash in its name is read" \
  grep -q "<td>lib</td><td class='n'>01-initial</td>.*<td class='dim'>fixed 1, open 0, dropped 0</td>" "$page"

# --- status.py: a run with a peer -------------------------------------------------------------
mkdir -p "$journal/review"
echo '{"findings": [{"id": 1}, {"id": 2}, {"id": 3}]}' >"$journal/review/wave-1.json"
cat >"$project/$lead/subagents/agent-p1.jsonl" <<EOF
{"type":"user","timestamp":"$now","message":{"role":"user","content":"You are sorting and fixing what review round wave 1, peer, app of a plan run found. Journal: $journal"}}
{"type":"assistant","timestamp":"$now","message":{"id":"p1","model":"claude-test-fixer","usage":{"input_tokens":444000,"output_tokens":5},"content":[]}}
EOF
cat >"$project/$lead/subagents/agent-r1.jsonl" <<EOF
{"type":"user","timestamp":"$now","message":{"role":"user","content":"Every lane of wave 1 review of a plan run has ended. Journal: $journal"}}
{"type":"assistant","timestamp":"$now","message":{"id":"r1","model":"claude-test-integrator","usage":{"input_tokens":555000,"output_tokens":5},"content":[]}}
EOF
progress "review wave 1, peer, app: fixed 2, open 0, dropped 1"
check "the peer fixer's line shows on its wave" grep -q "3 findings; app: fixed 2, open 0, dropped 1" "$page"
check "the peer fixer's tokens show on its wave" grep -q ">444k<" "$page"
check "the integrator of the peer's review lanes counts in the last wave" \
  grep -q "<td class='num'>556k</td>" "$page"
progress "review wave 1: merged"
check "a merged review lane shows on its wave" grep -q "dropped 1; merged</td>" "$page"
progress "review wave 1: merged, app, 0123abc"
check "a merged review lane with its repository and tip shows on its wave" \
  grep -q "dropped 1; merged in app</td>" "$page"
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
cat >"$project/$lead/subagents/agent-a2.jsonl" <<EOF
{"type":"user","timestamp":"$now","message":{"role":"user","content":"Look around $journal"}}
{"type":"assistant","timestamp":"$now","message":{"id":"a2","content":[{"type":"tool_use","id":"c1","name":"Bash","input":{"command":"cat skills/make-plan/SKILL.md"}},{"type":"tool_use","id":"c2","name":"Bash","input":{"command":"cd /w && make test"}},{"type":"tool_use","id":"c3","name":"Bash","input":{"command":"git -C /w commit -m wip"}},{"type":"tool_use","id":"c4","name":"Bash","input":{"command":"echo done >> \$EXEC_PLAN_JOURNAL/progress.md"}}]}}
EOF
audit=$(cd "$base" && python3 "$scripts/audit.py" 2>&1)
check "audit.py reads the run's lane and applies the Go rule of a repository with a go.mod" \
  grep -q "^shared-cache: .*: go build" <<<"$audit"
check "audit.py takes make for a build only where a command starts" \
  bash -c '! grep -q "make-plan" <<<"$1" && grep -q "^shared-cache: .*: make test$" <<<"$1"' _ "$audit"
check "audit.py sees a commit made with git -C" grep -q "^own-commit: .*: git -C /w commit" <<<"$audit"
check "audit.py sees a redirect into \$EXEC_PLAN_JOURNAL" grep -q "^journal-written: " <<<"$audit"

# make behind a wrapper, git with a long option before its subcommand, the journal written by tee
# or from inside it
wrapped=("timeout 600 make test" "time make lint" "(make vet)" "if make build; then echo ok; fi"
  "env X=1 make gen" "! make check" "command make all")
written=("git --no-pager commit -m a" "git --git-dir=/w/repo commit -m b"
  "echo a | tee -a \"\$EXEC_PLAN_JOURNAL/progress.md\"" "cd \$EXEC_PLAN_JOURNAL && echo b >> progress.md")
python3 - "$journal" "$now" "${wrapped[@]}" "${written[@]}" >"$project/$lead/subagents/agent-a3.jsonl" <<'PY'
import json, sys
journal, now, *cmds = sys.argv[1:]
print(json.dumps({"type": "user", "timestamp": now, "message": {"role": "user", "content": f"Look around {journal}"}}))
uses = [{"type": "tool_use", "id": f"w{i}", "name": "Bash", "input": {"command": c}} for i, c in enumerate(cmds)]
print(json.dumps({"type": "assistant", "timestamp": now, "message": {"id": "a3", "content": uses}}))
PY
audit=$(cd "$base" && python3 "$scripts/audit.py" 2>&1)
for c in "${wrapped[@]}"; do
  check "audit.py takes '$c' for a build" grep -qF -- "/agent-a3): $c" <<<"$(grep "^shared-cache: " <<<"$audit")"
done
for c in "git --no-pager commit" "git --git-dir=/w/repo commit"; do
  check "audit.py sees '$c'" grep -qF -- "/agent-a3): $c" <<<"$(grep "^own-commit: " <<<"$audit")"
done
check "audit.py sees tee into the journal" grep -qF -- "/agent-a3): echo a | tee -a" <<<"$(grep "^journal-written: " <<<"$audit")"
check "audit.py sees a redirect from inside the journal" \
  grep -qF -- "/agent-a3): echo b >> progress.md" <<<"$(grep "^journal-written: " <<<"$audit")"
check "audit.py still passes over make inside a path" bash -c '! grep -q "make-plan" <<<"$1"' _ "$audit"

# --- no watcher left behind -------------------------------------------------------------------
check "no status watcher was started" test ! -e "$journal/status-watch"

if [ "$failed" -ne 0 ]; then
  echo "$failed checks failed"
  exit 1
fi
echo "all checks passed"
