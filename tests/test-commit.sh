#!/usr/bin/env bash
# commit.sh commits the named paths and nothing else: a refusal over another session's staged work
# leaves the index as it found it, a path gone from the tree commits its removal, and a file a
# pre-commit hook stages lands in the same commit.
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

unset EXEC_PLAN_JOURNAL
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

repo=$base/repo
git init -q "$repo"
cd "$repo" || exit 1
echo one >mine.txt
echo two >other.txt
echo three >gone.txt
git add -A
git commit -qm init

staged() { git diff --cached --name-only | tr '\n' ' '; }

# --- another session's staged work -----------------------------------------------------------
echo changed >other.txt
git add other.txt
echo changed >mine.txt
check "commit.sh refuses while the index holds a path it does not name" \
  bash -c '! "$1" "mine" mine.txt' _ "$scripts/commit.sh"
check "the refusal leaves the index as it was" test "$(staged)" = "other.txt "
check "the refusal makes no commit" test "$(git log --format=%s -1)" = init
git restore --staged other.txt
git checkout -q -- other.txt

# --- a named path ------------------------------------------------------------------------------
check "commit.sh commits a changed path" "$scripts/commit.sh" "change mine" mine.txt
check "the commit holds the named path only" \
  test "$(git show --name-only --format= HEAD | tr '\n' ' ')" = "mine.txt "

# --- a removal ---------------------------------------------------------------------------------
rm gone.txt
check "commit.sh commits a path gone from the tree" "$scripts/commit.sh" "drop gone" gone.txt
check "the removal is in the commit" bash -c '! git cat-file -e HEAD:gone.txt'

# --- a file the pre-commit hook stages ---------------------------------------------------------
cat >.git/hooks/pre-commit <<'EOF'
#!/bin/sh
echo generated >gen.txt
git add gen.txt
EOF
chmod +x .git/hooks/pre-commit
echo again >mine.txt
check "commit.sh commits with a hook that stages a file" "$scripts/commit.sh" "change again" mine.txt
check "the hook's file lands in the commit" \
  test "$(git show --name-only --format= HEAD | sort | tr '\n' ' ')" = "gen.txt mine.txt "
check "nothing is left staged" test -z "$(staged)"

if [ "$failed" -ne 0 ]; then
  echo "$failed checks failed"
  exit 1
fi
echo "all checks passed"
