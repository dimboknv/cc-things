#!/usr/bin/env bash
# The brainstorm peer.sh refuses to start a peer of either kind when Claude has no mailbox-chat
# skill, in its configuration directory or in the project's .claude/skills, and names the skill
# in the reason. With the skill in either place the check passes. Stubs of agtermctl,
# mailbox-chat.py and codex stand first in PATH; the stub status answers that a peer of the
# asked kind already listens, so a run that passes every check mails the brief and exits 0.
#
# Every check runs and reports; the script exits non-zero when any failed. PEER_SCRIPT points it
# at another copy of the script.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
peer=${PEER_SCRIPT:-$here/../plugins/planning/skills/brainstorm/scripts/peer.sh}
peer=$(cd "$(dirname "$peer")" && pwd)/$(basename "$peer")

base=$(mktemp -d)
base=$(cd "$base" && pwd -P)
trap 'rm -rf "$base"' EXIT

# Nothing here may reach the owner's agterm, Claude Code or Codex configuration.
bin=$base/bin
mkdir -p "$bin"
cat >"$bin/agtermctl" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
cat >"$bin/mailbox-chat.py" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  status) printf '{"receiver": "%s"}\n' "$STUB_RECEIVER" ;;
  say) cat >/dev/null ;;
esac
EOF
cat >"$bin/codex" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$bin"/*
export PATH="$bin:$PATH"
export AGTERM_SESSION_ID=SESSION-1 AGTERM_PANE_ID=PANE-1

export CLAUDE_CONFIG_DIR=$base/claude
mkdir -p "$CLAUDE_CONFIG_DIR"
echo '{"hooks": {"UserPromptSubmit": [{"hooks": [{"command": "mailbox-chat.py claude-hook"}]}]}}' \
  >"$CLAUDE_CONFIG_DIR/settings.json"
export CODEX_HOME=$base/codex XDG_CONFIG_HOME=$base/config
mkdir -p "$CODEX_HOME/skills/mailbox-chat" "$XDG_CONFIG_HOME/agterm"
echo 'command = "mailbox-chat.py codex-hook"' >"$CODEX_HOME/config.toml"
touch "$CODEX_HOME/skills/mailbox-chat/SKILL.md"
echo 'on message run mailbox-chat.py agterm-hook' >"$XDG_CONFIG_HOME/agterm/hooks.conf"

project=$base/project
mkdir -p "$project"
cd "$project" || exit 1
brief=$base/brief.md
echo brief >"$brief"

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
# refuses_skill <kind>: non-zero, and the reason names the Claude mailbox-chat skill
refuses_skill() {
  local err
  if err=$(STUB_RECEIVER=$1 bash "$peer" "$brief" "$1" 2>&1 >/dev/null); then
    return 1
  fi
  grep -qF "no mailbox-chat skill under $CLAUDE_CONFIG_DIR/skills" <<<"$err"
}
# starts <kind>: every check passes and the listening peer is mailed the brief
starts() {
  STUB_RECEIVER=$1 bash "$peer" "$brief" "$1"
}

for kind in claude codex; do
  check "$kind peer: refused without the Claude mailbox-chat skill" refuses_skill "$kind"
done

mkdir -p "$CLAUDE_CONFIG_DIR/skills/mailbox-chat"
touch "$CLAUDE_CONFIG_DIR/skills/mailbox-chat/SKILL.md"
for kind in claude codex; do
  check "$kind peer: the skill in CLAUDE_CONFIG_DIR passes" starts "$kind"
done

rm -rf "$CLAUDE_CONFIG_DIR/skills"
mkdir -p .claude/skills/mailbox-chat
touch .claude/skills/mailbox-chat/SKILL.md
for kind in claude codex; do
  check "$kind peer: the skill in the project's .claude/skills passes" starts "$kind"
done

[ "$failed" -eq 0 ] || { echo "$failed failed"; exit 1; }
echo "all passed"
