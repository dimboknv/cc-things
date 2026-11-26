#!/usr/bin/env bash
# scripts/ask.py opens agterm's dialog in the session of AGTERM_SESSION_ID and prints the answer
# as `choice <id>` or `text <line>`; without an answer, out of agterm included, it prints nothing
# and exits 1, so the skill asks through AskUserQuestion. A stub agtermctl stands in for agterm.
#
# Every check runs and reports; the script exits non-zero when any failed. ASK_SCRIPT points it
# at another copy of the script.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
ask=${ASK_SCRIPT:-$here/../plugins/planning/scripts/ask.py}

base=$(mktemp -d)
trap 'rm -rf "$base"' EXIT

# The stub records its arguments, one per line, and answers with $STUB_REPLY and $STUB_EXIT.
stub=$base/agtermctl
cat >"$stub" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" >"$STUB_ARGS"
printf '%s\n' "$STUB_REPLY"
exit "$STUB_EXIT"
EOF
chmod +x "$stub"
export AGTERMCTL=$stub STUB_ARGS=$base/args

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

ask_peer() {
  python3 "$ask" 'Peer?' --default none --other 'own words' \
    --item none 'No peer' 'the session as it is' \
    --item claude 'Claude Code' 'a second session'
}
# answers <reply> <exit> <expected stdout>
answers() {
  local out
  out=$(STUB_REPLY=$1 STUB_EXIT=$2 ask_peer) || return 1
  [ "$out" = "$3" ]
}
# no_answer <reply> <exit>: exit 1 and nothing on stdout
no_answer() {
  local out rc
  out=$(STUB_REPLY=$1 STUB_EXIT=$2 ask_peer)
  rc=$?
  [ "$rc" -eq 1 ] && [ -z "$out" ]
}
# passed <arg> <next arg>: the stub got the two as neighbours
passed() {
  grep -A1 -xF -- "$1" "$STUB_ARGS" | grep -qxF -- "$2"
}

export AGTERM_SESSION_ID=SESSION-1

check "a picked item prints its id" \
  answers '{"result":"answered","id":"ok","label":"OK","index":0,"selected":["claude"]}' 0 'choice claude'
check "the dialog is bound to AGTERM_SESSION_ID" passed --target SESSION-1
check "the default item is checked" passed --checked none
check "an item carries its subtitle" passed --choice-subtitle 'claude=a second session'
check "the free line is offered" passed --other 'own words'
check "the dialog says which key picks" grep -qF 'Space picks' "$STUB_ARGS"
check "the free line prints its text" \
  answers '{"result":"answered","id":"ok","label":"OK","index":0,"selected":[],"text":"claude opus"}' 0 'text claude opus'
check "Esc is no answer" no_answer '{"result":"escaped"}' 3
check "a timeout is no answer" no_answer '{"result":"cancelled"}' 2
check "the Cancel button is no answer" \
  no_answer '{"result":"answered","id":"cancel","label":"Cancel","index":1}' 0
check "a failing agtermctl is no answer" no_answer 'error: no socket' 1
check "a default that names no item is refused" \
  bash -c '! python3 "$0" T --default x --item a A "" --item b B ""' "$ask"

unset AGTERM_SESSION_ID
rm -f "$STUB_ARGS"
check "out of agterm is no answer" no_answer '{"result":"answered","id":"ok","selected":["none"]}' 0
check "out of agterm agtermctl is not run" test ! -e "$STUB_ARGS"

[ "$failed" -eq 0 ] || { echo "$failed failed"; exit 1; }
echo "all passed"
