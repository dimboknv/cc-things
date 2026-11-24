# A closed question

A question whose answers are a fixed list goes to the owner as a picker, not as text: the peer
in `brainstorm` and `exec-plan`, the menu of `make-plan`, the last question of `brainstorm`. An
open question, a fork of a design and the go of `exec-plan` stay text.

## In agterm

When `AGTERM_SESSION_ID` is set, the picker is agterm's dialog. Run it through the Bash tool
with a timeout of 600000, `<plugin root>` being `${CLAUDE_PLUGIN_ROOT}` written out as an
absolute path:

```bash
python3 <plugin root>/scripts/ask.py '<question>' --default <id> --other '<placeholder>' \
  --item <id> '<label>' '<subtitle>' \
  --item <id> '<label>' '<subtitle>'
```

- `choice <id>` on stdout is the answer.
- `text <line>` is the owner's own words from the free line. Read them as a reply given in text.
- A non-zero exit means no answer: the owner pressed Esc, the dialog waited nine minutes, or
  agterm failed. Ask the same question through the AskUserQuestion tool.

## Outside agterm

Ask through the AskUserQuestion tool straight away. A closed question goes there also when an
output style or a user rule sends questions as text.

## The items

- The label is a few words. The subtitle (AskUserQuestion's description) says what the answer
  gives and what it costs, in the words the skill gives that item.
- The recommended item goes first. In agterm `--default` names it, so Enter, or a bare «ок»,
  picks it. In AskUserQuestion its label is marked as recommended.
- The question, labels, subtitles and the placeholder are in the language of the conversation.
- `--other` takes the owner's own answer: a model for the peer, an edit before the menu. Its
  placeholder says what may go there. AskUserQuestion has that field without asking.
- AskUserQuestion takes four options at most. A question with five drops the item the skill
  names, and the owner still gives it in the free field.
