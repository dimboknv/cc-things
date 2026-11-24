#!/usr/bin/env bash
# Prints the project rules the skills follow: the nearest .claude/planning/rules.md from the top
# of the checkout up to, not including, $HOME, else ~/.config/cc-things/planning/rules.md. The
# first non-empty file wins whole; nothing printed means every section takes its default
# (references/rules.md). Always exits 0.
set -u

dir=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
while [ -n "$dir" ] && [ "$dir" != "$HOME" ] && [ "$dir" != "/" ]; do
  f="$dir/.claude/planning/rules.md"
  if [ -s "$f" ]; then
    echo "<!-- rules: $f -->"
    cat "$f"
    exit 0
  fi
  dir=$(dirname "$dir")
done
f="${XDG_CONFIG_HOME:-$HOME/.config}/cc-things/planning/rules.md"
if [ -s "$f" ]; then
  echo "<!-- rules: $f -->"
  cat "$f"
fi
exit 0
