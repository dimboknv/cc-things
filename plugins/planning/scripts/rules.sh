#!/usr/bin/env bash
# Prints the project rules the skills follow: .claude/planning/rules.md of the checkout, else
# ~/.config/cc-things/planning/rules.md. The first non-empty file wins whole; nothing printed means
# every section takes its default (references/rules.md). Always exits 0.
set -u

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
for f in "$root/.claude/planning/rules.md" "${XDG_CONFIG_HOME:-$HOME/.config}/cc-things/planning/rules.md"; do
  if [ -s "$f" ]; then
    echo "<!-- rules: $f -->"
    cat "$f"
    exit 0
  fi
done
exit 0
