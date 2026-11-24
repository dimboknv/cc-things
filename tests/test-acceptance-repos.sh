#!/usr/bin/env bash
# acceptance.py runs each task's commands in the repository its `Repo:` line names, and a task
# with no `Repo:` in a plan outside git is skipped with its reason.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
acceptance=${ACCEPTANCE:-$here/../plugins/planning/skills/make-plan/scripts/acceptance.py}

base=$(mktemp -d)
trap 'rm -rf "$base"' EXIT

repo() {
  git -C "$base" init -q "$1"
  mkdir -p "$base/$1/$2"
  printf 'shared-needle\n' >"$base/$1/$2/$3"
  git -C "$base/$1" add -A
  git -C "$base/$1" -c user.name=t -c user.email=t@t commit -qm init
}
repo alpha src a.txt
repo beta lib b.txt

mkdir -p "$base/plans"
cat >"$base/plans/20261124-two-repos.md" <<'EOF'
## Implementation Steps

### Task 1: alpha

Where: `src/`.

Repo: `alpha`.

- [ ] acceptance: `git grep -n shared-needle` finds the needle

### Task 2: beta

Where: `lib/`.

Repo: `beta`.

- [ ] acceptance: `git grep -n shared-needle` finds the needle

### Task 3: nowhere

Where: `src/`.

- [ ] acceptance: `git grep -n shared-needle` finds the needle
EOF

out=$(cd "$base" && python3 "$acceptance" plans/20261124-two-repos.md 2>&1) || true

section() { awk -v t="## Task $1:" '$0 ~ "^## Task" { on = index($0, t) == 1 } on' <<<"$out"; }

fail() {
  printf 'FAIL: %s\n--- output ---\n%s\n' "$1" "$out" >&2
  exit 1
}

section 1 | grep -q 'src/a.txt' || fail "task 1 does not find src/a.txt in alpha"
section 1 | grep -q 'lib/b.txt' && fail "task 1 finds beta's lib/b.txt"
section 2 | grep -q 'lib/b.txt' || fail "task 2 does not find lib/b.txt in beta"
section 2 | grep -q 'src/a.txt' && fail "task 2 finds alpha's src/a.txt"
section 3 | grep -q 'skipped' || fail "task 3 has no Repo: in a plan outside git and is not skipped"
grep -q 'outside Where:' <<<"$out" && fail "a hit is marked outside Where:"

echo "ok: test-acceptance-repos"
