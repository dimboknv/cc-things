# Pictures through diagram-design

A skill of planning that shows the owner a picture draws it by these rules. Today that is the
fork page of `brainstorm`. Another skill takes them by one line that links this file; its own
page says how a picture lands on it.

## Who draws which picture

- **A flow, who asks whom between roles**, is drawn by the page from its own markup. The page
  keeps every role in one place across today and the options, and that is what the flow needs.
- **Everything else**, where data lives, which states an object passes, what follows what, goes
  to diagram-design first. The lead hands over the content: the roles, what changes between
  today and the option, and the question the fork asks. diagram-design picks the type by its own
  selection rules. The lead does not pick the type for it.
- **A shape diagram-design has no type for** is drawn by the lead by hand, as an inline `<svg>`
  in the page's markup. A sketch of the user's screen is the known case. The nearest type is
  not taken instead: for a screen it gives a chart of nested boxes, not a screen.
- **Neither name of the skill loads**: the lead draws by hand as well, and says once in the chat
  that diagram-design is missing.

All the pictures of one fork come from one drawer, so today and every option read as the same
picture.

## Loading the skill

Load it with the Skill tool under either name: `diagram-design:diagram-design`, the plugin
planning declares, or `diagram-design`, a bare skill in the skills folder of the configuration.
Load it once per session, before the first picture it draws.

The load prints the skill's folder: "Base directory for this skill: <dir>". Keep that path for
the rest of the session. The page needs it to export the drawing, and nothing else looks for
it, because the path changes with the version and with the way the skill is installed.

## The two pauses

diagram-design stops twice before a drawing. The owner is asked neither time: the lead answers
both, because the picture serves a fork the owner is waiting on, and its style is not a
decision of the design.

- **The style guide gate.** On the first drawing in a project with the shipped tokens it asks
  whether to customize the style. The answer is "keep default". Its offer to write a
  `.diagram-design` marker into the project is declined: the marker is a file in the owner's
  tree. The gate comes back in the next session and gets the same answer.
- **Confirm before drawing.** It states its plan, the type, the size and what it cuts, and waits.
  The lead draws without waiting and writes that plan as one line in the chat, so the owner
  sees what was chosen.

These answers rest on the current text of diagram-design's skill. When an update adds a pause
or changes one, this file is fixed, not each skill that reads it.

## What to ask for

- **The dark variant**, from its `assets/template-dark.html`, whatever theme the terminal has.
  The terminal is dark, and one run with no colour mapping is the simplest. There is no light
  copy and no switch by theme.
- **One file per picture**: the self-contained `.html` diagram-design writes. It lands in the
  scratchpad beside the page's fragment, named after the fork and the block:
  `fork-<n>-today.html`, `fork-<n>-<option id>.html`. The page exports it; the lead does not
  ask diagram-design for an `.svg` or a `.png`.

## Today first, the options as copies

One picture per fork. Today is drawn first. Each option is a copy of today's file, not a new
drawing: the same nodes in the same places, with what the option adds marked as new and what it
removes marked as gone, and a legend that says which mark is which. The marks come from the
drawing's own palette: its accent for the new, a dashed muted stroke for the gone. A new layout
per option would hide the difference the owner has to see.

## Onto the page

The page that shows the picture owns its markup and the call that embeds it. For the fork page
of `brainstorm` that is [page.md, Pictures](../skills/brainstorm/page.md#pictures): a
`<figure data-diagram>` that links the file, and `fork.py show` with the skill's folder passed
as `--diagram-design <dir>`.
