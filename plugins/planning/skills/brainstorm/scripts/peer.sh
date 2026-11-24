#!/usr/bin/env bash
# Starts a peer: a second agent in the split pane of this agterm session, told to read the
# brief it is given. `brainstorm` and `exec-plan` both start their peer with it. Prints the
# `mailbox-chat.py status` JSON once the peer listens for mail.
#
# usage: peer.sh <brief.md> claude [model-id]
#        peer.sh <brief.md> codex
#   brief.md   the peer's instructions, the peer.md of the skill that starts it
#   model-id   the model the Claude peer runs on; without it, the account's default
#
# A peer of the asked kind that already listens in the split is mailed the brief and kept: it
# may be one another skill started. A split that holds anything else is refused: the pane is the owner's, and typing a launch line
# into it would run inside whatever the owner started there.
#
# The Claude peer gets a session id of its own and runs the `claude` binary through `command`.
# The owner's `claude` shell function resumes the conversation bound to the agterm session id,
# which both panes share, so a bare `claude` in the split would reopen the lead's own
# conversation. `env` is not used for the account: a shell that wraps it in a colouriser hands
# Claude Code a pipe, and it answers once and exits.
#
# The Codex peer is started the way agterm's two-agent-mailbox-chat recipe says: `--no-daemon`,
# because the shared background server carries another pane's ids, and a first prompt with no
# topic, because Codex registers its thread only once a prompt has run. Its brief goes to it as
# the first mail.
set -euo pipefail

refuse() {
  echo "peer.sh: $*" >&2
  exit 1
}

usage="usage: $(basename "$0") <brief.md> claude [model-id] | <brief.md> codex"
[ $# -ge 2 ] || refuse "$usage"
kind="$2"
model="${3:-}"
case "$kind" in
  claude) [ $# -le 3 ] || refuse "$usage" ;;
  codex) [ $# -eq 2 ] || refuse "$usage" ;;
  *) refuse "$usage" ;;
esac
[ -f "$1" ] || refuse "no brief at $1"
brief="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
case "$brief${CLAUDE_CONFIG_DIR:-}" in
  *"'"*) refuse "a single quote in the brief path or CLAUDE_CONFIG_DIR breaks the launch line" ;;
esac
task="You are the peer of the agent in the other pane, the lead. Read $brief and follow it. The lead sends its requests through the mailbox."
case "$model" in
  *[!A-Za-z0-9._\[\]-]*) refuse "bad model id '$model'" ;;
esac

sid="${AGTERM_SESSION_ID:-}"
[ -n "$sid" ] && [ -n "${AGTERM_PANE_ID:-}" ] || refuse "not inside an agterm pane"
command -v agtermctl >/dev/null || refuse "agtermctl is not on PATH"
command -v mailbox-chat.py >/dev/null || refuse "mailbox-chat.py is not on PATH"

# Without its hooks neither agent is woken by mail, and the chat is two agents writing to nobody.
claude_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
grep -qs 'mailbox-chat.py claude-hook' "$claude_dir/settings.json" .claude/settings.json .claude/settings.local.json \
  || refuse "no 'mailbox-chat.py claude-hook' in $claude_dir/settings.json: the lead is not wired for mailbox-chat"
if [ "$kind" = codex ]; then
  command -v codex >/dev/null || refuse "codex is not on PATH"
  codex_home="${CODEX_HOME:-$HOME/.codex}"
  grep -qs 'mailbox-chat.py codex-hook' "$codex_home/config.toml" "$codex_home/hooks.json" \
    || refuse "no 'mailbox-chat.py codex-hook' SessionStart hook under $codex_home: this Codex is not wired for mailbox-chat (agterm cookbook, two-agent-mailbox-chat, Setup)"
  grep -qs 'mailbox-chat.py agterm-hook' "${XDG_CONFIG_HOME:-$HOME/.config}/agterm/hooks.conf" \
    || refuse "no 'on message … mailbox-chat.py agterm-hook' in agterm's hooks.conf: mail for a Codex pane is never handed over"
  [ -f "$codex_home/skills/mailbox-chat/SKILL.md" ] \
    || refuse "no mailbox-chat skill under $codex_home/skills: Codex would not know how to answer"
fi

receiver() {
  mailbox-chat.py status 2>/dev/null | sed -n 's/.*"receiver": *"\([a-z]*\)".*/\1/p'
}

status="$(mailbox-chat.py status 2>&1 || true)"
case "$status" in
  *"\"receiver\": \"$kind\""*)
    printf '%s\n' "$task" | mailbox-chat.py say --stdin >/dev/null
    echo "$status"
    exit 0
    ;;
  *'no split'*) ;;
  *'"receiver"'*) refuse "the split pane exists and no $kind listens in it: close it and run this again ($status)" ;;
  *) refuse "mailbox-chat.py status failed: $status" ;;
esac

if [ "$kind" = claude ]; then
  uuid="$(uuidgen | tr 'A-Z' 'a-z')"
  line="command claude --session-id $uuid"
  [ -z "$model" ] || line="$line --model '$model'"
  line="$line '$task'"
  [ -z "${CLAUDE_CONFIG_DIR:-}" ] || line="CLAUDE_CONFIG_DIR='$CLAUDE_CONFIG_DIR' $line"
else
  line="command codex --no-daemon 'Answer with the single word READY.'"
fi

agtermctl session split on --axis vertical --target "$sid" >/dev/null
# `session restart` needs Live sessions mode; without it the line is typed into the fresh
# shell, which nothing else writes to yet.
if ! agtermctl session restart --pane right --target "$sid" --command "$line" >/dev/null 2>&1; then
  sleep 1
  printf '%s\n' "$line" | agtermctl session type --stdin --pane right --target "$sid" >/dev/null
fi
agtermctl session focus left --target "$sid" >/dev/null 2>&1 || true

for _ in $(seq 1 60); do
  if [ "$(receiver)" = "$kind" ]; then
    if [ "$kind" = codex ]; then
      printf '%s\n' "$task" | mailbox-chat.py say --stdin >/dev/null
    fi
    mailbox-chat.py status
    exit 0
  fi
  sleep 1
done
refuse "the peer did not start listening in 60s: look at the right pane (a trust or login prompt stops it)"
