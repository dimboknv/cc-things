#!/usr/bin/env bash
# acceptance.py runs each task's commands in the repository its `Repo:` line names, and a task
# with no `Repo:` in a plan outside git is skipped with its reason. It marks hits against
# `Where:` on path boundaries, refuses commands that write or run a program, and never reads
# its own stdin.
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

# A tracked plan in its home repository: Where: boundaries, the plan's own hit, commands that
# write or run a program, commands that do not start with a search, and a closed stdin.
git -C "$base" init -q gamma
g=$base/gamma
mkdir -p "$g/src" "$g/.github" "$g/internal/foobar" "$g/docs/plans"
for f in src/a.txt .github/ci.yml internal/foobar/f.txt Makefile; do
  printf 'shared-needle\n' >"$g/$f"
done
cat >"$g/docs/plans/20261125-checks.md" <<'EOF'
## Implementation Steps

### Task 1: boundaries

Where: `src/`, `./.github/`, `internal/foo/`, `Makefile`.

- [ ] acceptance: `git grep -n shared-needle` finds the needle

### Task 2: refused

Where: `src/`.

- [ ] acceptance: `awk 'BEGIN { system("touch pwned-awk") }'` is refused
- [ ] acceptance: `git grep -l shared-needle | sort -o pwned-sort` is refused
- [ ] acceptance: `git grep -l shared-needle | uniq - pwned-uniq` is refused
- [ ] acceptance: `find . -name a.txt -fprint pwned-find` is refused
- [ ] acceptance: `git grep -Otouch shared-needle` is refused
- [ ] acceptance: `rg --pre ./x shared-needle` is refused
- [ ] acceptance: `FOO=1 rg shared-needle` is refused
- [ ] acceptance: `cd src && rg shared-needle` is refused
- [ ] acceptance: `! rg shared-needle` is refused
- [ ] acceptance: `rg shared-needle src#;touch pwned-hash` is refused
- [ ] acceptance: `git grep -l shared-needle | sort --o=pwned-sort-abbrev` is refused
- [ ] acceptance: `git grep -l shared-needle | sort --compress-prog=touch` is refused
- [ ] acceptance: `git grep --open=touch shared-needle` is refused

### Task 3: stdin

Where: `src/`.

- [ ] acceptance: `rg -l shared-needle` finds the needle

### Task 4: quoted operators

Where: `src/`.

- [ ] acceptance: `rg -l '|' src` finds the pipe
- [ ] acceptance: `rg -l ">" src` finds the arrow

### Task 5: grep with no file

Where: `src/`.

- [ ] acceptance: `grep shared-needle` reads stdin
- [ ] acceptance: `grep -e shared-needle -n` reads stdin
- [ ] acceptance: `grep -n shared-needle src/a.txt` finds the needle
- [ ] acceptance: `grep -rn shared-needle src` finds the needle
EOF
printf 'a|b>c\n' >"$g/src/ops.txt"
git -C "$g" add -A
git -C "$g" -c user.name=t -c user.email=t@t commit -qm init

out=$(cd "$base" && python3 "$acceptance" gamma/docs/plans/20261125-checks.md 2>&1 <<<"shared-needle") || true

line() { section "$1" | grep -F -- "$2" || true; }
[[ -n $(line 1 .github/ci.yml) ]] || fail "task 1 does not find .github/ci.yml"
line 1 .github/ci.yml | grep -q 'outside Where:' && fail ".github/ci.yml is marked outside Where: ./.github/"
line 1 internal/foobar/f.txt | grep -q 'outside Where:' || fail "internal/foobar/f.txt is not marked outside Where: internal/foo/"
line 1 Makefile | grep -q 'outside Where:' && fail "Makefile is marked outside Where: Makefile"
line 1 docs/plans/20261125-checks.md | grep -q 'the plan itself' || fail "the plan's own hit is not marked as the plan itself"
for cmd in "awk 'BEGIN" "sort -o" "uniq - pwned" "-fprint" "git grep -Otouch" "rg --pre" "FOO=1 rg" "cd src && rg" "! rg" \
  "src#;touch" "sort --o=" "sort --compress-prog" "git grep --open="; do
  line 2 "$cmd" | grep -q '^ *skipped (' || fail "task 2 runs or ignores: $cmd"
done
ls "$g" | grep -q pwned && fail "a refused command wrote a file"
line 3 src/a.txt | grep -q . || fail "task 3 searched stdin instead of the repository"
line 4 skipped | grep -q . && fail "task 4 reads a quoted | or > as a shell operator"
[[ $(line 4 src/ops.txt | wc -l) -eq 2 ]] || fail "task 4 does not find src/ops.txt for both quoted operators"
for cmd in "grep shared-needle" "grep -e shared-needle"; do
  line 5 "$cmd" | grep -q '^ *skipped (grep with no file reads stdin)' || fail "task 5 reports a clean miss for: $cmd"
done
[[ $(line 5 src/a.txt | wc -l) -eq 2 ]] || fail "task 5 does not run a grep with a file or -r"

echo "ok: test-acceptance-repos"
