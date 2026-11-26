#!/usr/bin/env bash
# The brainstorm peer.sh refuses to start a peer of either kind when Claude has no mailbox-chat
# skill, in its configuration directory or in the project's .claude/skills, and names the skill
# in the reason. With the skill in either place the check passes. Stubs of agtermctl,
# mailbox-chat.py and codex stand first in PATH: the stub status reports no split until the stub
# agtermctl opens one, then a peer of the asked kind listening in it, so a run that passes every
# check starts the peer, mails it the brief and exits 0.
#
# A listener in the split is kept only when peer.sh started it; one it did not start may be the
# owner's own session and is refused. The mark that records it is written as soon as the pane
# is launched, so a peer that listens only after the wait ran out is kept on a rerun; it lives
# outside TMPDIR, is refreshed on each kept run, and is dropped once its peer stopped listening.
# A failed `say` is refused with its message, and every agtermctl call carries the socket of
# AGTERM_SOCKET.
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
echo "$*" >>"$STUB_LOG"
[ "$1 $2 $3" != "session split on" ] || touch "$STUB_SPLIT"
exit 0
EOF
cat >"$bin/mailbox-chat.py" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  status)
    if [ ! -e "$STUB_SPLIT" ]; then
      echo '{"error": "this session has no split; open one with `agtermctl session split on`"}'
      exit 1
    fi
    printf '{"pane": "PANE-1", "peerPane": "PANE-2", "receiver": "%s"}\n' "$STUB_RECEIVER"
    ;;
  say)
    cat >/dev/null
    if [ -n "${STUB_SAY_FAIL:-}" ]; then
      echo '{"error": "the mailbox of pane PANE-2 is full"}'
      exit 1
    fi
    echo '{"sent": 5}'
    ;;
esac
EOF
cat >"$bin/codex" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
# the wait for a listener sleeps a second per look; here it does not wait
cat >"$bin/sleep" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$bin"/*
export PATH="$bin:$PATH"
export AGTERM_SESSION_ID=SESSION-1 AGTERM_PANE_ID=PANE-1
export STUB_SPLIT=$base/split STUB_LOG=$base/agtermctl.log TMPDIR=$base/tmp
mkdir -p "$TMPDIR"
unset AGTERM_SOCKET STUB_SAY_FAIL

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
# starts <kind>: every check passes, the split opens and the listening peer is mailed the brief
starts() {
  rm -f "$STUB_SPLIT"
  STUB_RECEIVER=$1 bash "$peer" "$brief" "$1"
}
# refuses <text> <kind> [receiver]: with the split already open and <receiver>, <kind> unless
# given, listening in it, non-zero and the reason holds <text>
refuses() {
  local err
  if err=$(STUB_RECEIVER=${3:-$2} bash "$peer" "$brief" "$2" 2>&1 >/dev/null); then
    return 1
  fi
  grep -qF -- "$1" <<<"$err"
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

# A listener peer.sh started is kept; one it did not start is refused.
for kind in claude codex; do
  starts "$kind" >/dev/null 2>&1
  : >"$STUB_LOG"
  check "$kind peer: a peer this script started is kept" \
    env STUB_RECEIVER="$kind" bash "$peer" "$brief" "$kind"
  check "$kind peer: kept without a second split" bash -c '! grep -q "split on" "$0"' "$STUB_LOG"
done
marks=$CLAUDE_CONFIG_DIR/planning-peer
rm -rf "$base/tmp" && mkdir "$base/tmp"
check "a mark outlives a cleared TMPDIR" env STUB_RECEIVER=claude bash "$peer" "$brief" claude
touch -t 200001010000 "$marks/PANE-2"
STUB_RECEIVER=claude bash "$peer" "$brief" claude >/dev/null 2>&1
check "a kept run refreshes the mark" test -n "$(find "$marks/PANE-2" -newermt 2001-01-01)"
rm -rf "$marks"
check "a listener this script did not start is refused" refuses "did not start" claude

starts claude >/dev/null 2>&1
check "a split where the started peer no longer listens is refused" refuses "no claude listens" claude none
check "then a listener in that pane is not taken for the peer" refuses "did not start" claude

rm -rf "$marks" "$base/tmp" && mkdir "$base/tmp"
check "a peer that listens only after the wait is kept on a rerun" bash -c \
  'rm -f "$STUB_SPLIT"; ! STUB_RECEIVER=none bash "$0" "$1" claude && STUB_RECEIVER=claude bash "$0" "$1" claude' \
  "$peer" "$brief"
rm -f "$STUB_SPLIT" && rm -rf "$marks"
STUB_RECEIVER=none bash "$peer" "$brief" claude >/dev/null 2>&1
check "a started peer that does not listen yet is named so on a rerun" \
  refuses "does not listen yet" claude none

check "a failed say is refused with its message" env STUB_SAY_FAIL=1 STUB_RECEIVER=codex bash -c \
  'rm -f "$STUB_SPLIT"; ! err=$(bash "$0" "$1" codex 2>&1 >/dev/null) && grep -qF "is full" <<<"$err"' \
  "$peer" "$brief"

: >"$STUB_LOG"
check "the peer starts with AGTERM_SOCKET set" env AGTERM_SOCKET=/run/agterm.sock bash -c \
  'rm -f "$STUB_SPLIT"; STUB_RECEIVER=claude bash "$0" "$1" claude' "$peer" "$brief"
check "every agtermctl call carries --socket" \
  bash -c '[ -s "$0" ] && ! grep -vqF -- "--socket /run/agterm.sock" "$0"' "$STUB_LOG"

[ "$failed" -eq 0 ] || { echo "$failed failed"; exit 1; }
echo "all passed"
