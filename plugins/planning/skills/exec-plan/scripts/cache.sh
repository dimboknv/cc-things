# Points the Go build cache and the golangci-lint cache at the journal of the run the current
# checkout belongs to. Sourced, never executed: a shell keeps the two variables only for the
# commands that follow in the same call.
#
# usage: . cache.sh && <command>
#
# The Go build cache is one per run, so the checkouts of a run compile a dependency once. The
# lint cache is one per checkout: golangci-lint keeps the absolute path of every file it read,
# and an entry of a worktree that is gone comes back as an issue no exclusion matches.
#
# The run is found by the checkout's directory name, which starts with the slug: <slug>,
# <slug>-task-<N>, <slug>-review-<N>, <slug>-tip, <slug>-base. A checkout of no run gets a
# non-zero status and no variable.
#
# Read by bash and by zsh, under `set -u` as well.
_xp_top="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "cache.sh: not inside a git work tree" >&2
  return 1
}
_xp_main="$(cd "$(git rev-parse --git-common-dir)/.." && pwd -P)"
_xp_name="$(basename "$_xp_top")"
_xp_slug="$_xp_name"
while [ ! -d "$_xp_main/.exec-plan/$_xp_slug" ]; do
  case "$_xp_slug" in
    *-*) _xp_slug="${_xp_slug%-*}" ;;
    *)
      echo "cache.sh: $_xp_top is the checkout of no run" >&2
      unset _xp_top _xp_main _xp_name _xp_slug
      return 1
      ;;
  esac
done
export GOCACHE="$_xp_main/.exec-plan/$_xp_slug/cache/go-build"
export GOLANGCI_LINT_CACHE="$_xp_main/.exec-plan/$_xp_slug/cache/lint/$_xp_name"
mkdir -p "$GOCACHE" "$GOLANGCI_LINT_CACHE"
unset _xp_top _xp_main _xp_name _xp_slug
