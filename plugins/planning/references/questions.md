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

## The peer question

`brainstorm` and `exec-plan` may run with a peer, a second agent in the split pane, and ask
about it the same way. It is the first question, asked before anything else and alone. It is
not asked when the request already answers it, or when the session is not in agterm, where no
peer can run. It is a closed question, asked as this file says, no peer first. Three answers,
each with what it costs:

- no peer: the session or the run as the skill's own file describes it. A bare «ок» means
  this;
- Claude Code: a second session of the same account in the split pane, doing the work the
  skill gives its peer. Its turns are paid like this session's;
- Codex: the same work by another model, which catches what two Claudes agree on by habit. The
  Claude Code hooks and skills of the project do not bind it.

The free line takes the owner's own words, a model for the Claude peer among them. The skill
says what its peer does and any cost of its own.
