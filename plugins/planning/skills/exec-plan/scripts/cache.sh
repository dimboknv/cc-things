# Points the Go build cache and the golangci-lint cache at the journal of the run, the directory
# EXEC_PLAN_JOURNAL names. Sourced, never executed: a shell keeps the two variables only for the
# commands that follow in the same call.
#
# usage: EXEC_PLAN_JOURNAL=<journal> . cache.sh && <command>
#
# The Go build cache is one per run, cache/go-build, so the checkouts of a run compile a
# dependency once. The lint cache is one per checkout, cache/lint/<repo>/<checkout dir name>:
# golangci-lint keeps the absolute path of every file it read, and an entry of a worktree that is
# gone comes back as an issue no exclusion matches. <repo> is the directory name of the main
# checkout, because the run worktree of every repository of the run has the same name, the slug.
# Without the journal, or outside a git work tree, it sets no variable and returns non-zero.
#
# Read by bash and by zsh, under `set -u` as well.
case "${EXEC_PLAN_JOURNAL:-}" in
  '')
    echo "cache.sh: EXEC_PLAN_JOURNAL is not set" >&2
    return 1
    ;;
  /*) ;;
  *)
    echo "cache.sh: EXEC_PLAN_JOURNAL is not an absolute path: '$EXEC_PLAN_JOURNAL'" >&2
    return 1
    ;;
esac
_xp_top="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "cache.sh: not inside a git work tree" >&2
  unset _xp_top
  return 1
}
_xp_main="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
export GOCACHE="$EXEC_PLAN_JOURNAL/cache/go-build"
export GOLANGCI_LINT_CACHE="$EXEC_PLAN_JOURNAL/cache/lint/$(basename "$_xp_main")/$(basename "$_xp_top")"
mkdir -p "$GOCACHE" "$GOLANGCI_LINT_CACHE"
unset _xp_top _xp_main
