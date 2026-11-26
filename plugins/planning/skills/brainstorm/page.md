# The fork page: markup and answer

`<skill dir>/scripts/fork.py show <fragment>` puts the fragment into the shell
[`assets/fork.html`](assets/fork.html) and opens the result in the agterm overlay. `<skill dir>`
is the absolute path [SKILL.md](SKILL.md) gives, here and for `fork.py result` below. The shell
owns the look, the choice, the comment fields and the answer. The fragment owns the content.
Write the fragment to the scratchpad as `fork-<n>.html`; the built page lands beside it. A
fragment that links a diagram-design drawing is shown with
`fork.py show <fragment> --diagram-design <diagram-design dir>`, as
[Pictures](#pictures) says.

## The fragment

```html
<main data-place="2 из 5" data-title="The fork as a question, in the owner's words" data-layout="columns">

<script type="application/json" data-roles>
{"op":  {"x": 4,   "y": 92, "label": "Оператор"},
 "gw":  {"x": 128, "y": 92, "label": "Гейтвей"},
 "reg": {"x": 128, "y": 8,  "label": "Реестр камер"}}
</script>

<section data-today>
  <script type="application/json" data-flow>
  {"nodes": {"op": "", "gw": "", "reg": "off"}, "edges": [["op", "gw", "", 1]]}
  </script>
  <p>What happens today, in plain words.</p>
</section>

<article data-option="ask" data-title="The option as what happens at run time" data-recommended>
  <script type="application/json" data-flow>
  {"nodes": {"op": "", "gw": "", "reg": ""}, "edges": [["op", "gw", "", 1], ["gw", "reg", "new", 2]]}
  </script>
  <p>The option in one or two sentences.</p>
  <ol class="steps">
    <li>Оператор открыл архив Park-Camera-02</li>
    <li class="new">Гейтвей спросил реестр, кто пишет камеру</li>
  </ol>
  <div class="price"><span class="chip new">+1 вызов между сервисами</span><br>What it costs at run time.</div>
  <p class="why">The reason of the recommendation, on the recommended option only.</p>
</article>

<aside data-rejected="table" data-title="An option that was dropped">Why, in one line.</aside>

</main>
```

- `data-place` is the fork's place as the list gave it. `data-layout` is `columns`, options
  side by side, or `rows`, each option across the whole panel with its picture on the left.
  `columns` holds only while every option gets 330 px in one row; below that the page shows
  rows, so a third card never drops under the first two.
- An option's `data-option` is a short id in Latin letters. It comes back in the answer and
  never reaches the owner's eyes; `data-title` does.
- The picture of the today block and of an option is its first element: a `data-flow` script,
  a `<figure>`, an `<svg>` or a `<figure data-diagram>`. A block without one is text only.
- `data-rejected` blocks are optional and land in a folded list with a "bring it back" mark.
- Text from outside the session, a log line or an issue body, is HTML-escaped: the page can run
  agterm commands.

## Pictures

Who draws which kind is in [`../../references/diagrams.md`](../../references/diagrams.md): a
flow is the page's own `data-flow`; everything else is a diagram-design drawing; a shape
diagram-design has no type for, the user's screen above all, is an `<svg>` the lead writes by
hand. Below is the markup of each.

**A flow, who asks whom.** `data-roles` places every role once, by `x` and `y` of its top
left corner; the width follows the label unless `w` is given. Every `data-flow` draws from
those roles, so a role stands in the same place in the today block and in every option.
`nodes` lists the roles this picture shows, each `""`, `"new"` or `"off"` (present today, not
part of this option). An edge is `[from, to, kind, step]`: `kind` is `""`, `"new"` or
`"gone"`, and `step` is the number of the scenario step the arrow carries, left out for an
arrow outside the scenario.

**A hand-drawn picture**, a shape diagram-design has no type for, is an inline `<svg>` with a
`viewBox`. The shell's classes keep it in the theme:
`node`, `node new`, `node off` on a `<g>` holding a `<rect>` and a `<text>`; `edge`,
`edge new`, `edge gone` on a `<line>` or a `<path>`, which also draws the arrowhead. Colours
come from `var(--new)`, `var(--gone)`, `var(--dim)`, `var(--accent)`, never from a literal.

**A diagram-design drawing** is an empty `<figure data-diagram="fork-2-today.html"></figure>`
as the block's first element. The value is the HTML file diagram-design wrote, a path relative
to the fragment's folder or an absolute one. Pass the folder the diagram-design skill printed
when it loaded ("Base directory for this skill: …") as `--diagram-design <dir>`; `fork.py` does
not look for it, because the path changes with the version and the way the skill is installed.
For each such figure `fork.py`:

- exports the file with `<dir>/scripts/export_svg.py --system-fonts`, which carries the
  drawing's styles into the SVG and prefixes its `<defs>` ids; the SVG lands beside the
  fragment as `fork-<n>.diagram-<k>.svg`;
- swaps Geist Mono, Geist and Instrument Serif for the system stacks
  `ui-monospace, 'SF Mono', Menlo, monospace`, `system-ui, -apple-system, sans-serif` and
  `ui-serif, Georgia, serif` in its `font-family` attributes, its `style` attributes and its
  `<style>`, and leaves a label's text as it is: an SVG inside `<img>` loads no web font, and a
  bare `monospace` there is a serif Courier;
- embeds the result as an `<img>` with a data URI, so the page still opens without file
  access.

The shell shows such a picture across the whole card with the text under it, without its own
legend of the marks, since the drawing carries one, and the whole fork in `rows`, whatever `data-layout` says: in a column or in three fifths of a row the
drawing's labels shrink below reading size. A linked figure without `--diagram-design`, a
folder without `scripts/export_svg.py`, a missing file or a failed export ends `show` with
exit 1 and the reason on stderr.

## The answer

```json
{"place": "2 из 5", "choice": "ask", "comments": {"today": "…", "copy": "…"}, "general": "…", "reopen": ["table"]}
```

`choice` is an option id, `own` (the owner's option is in `comments.own`), `explain` (what is
unclear is in `comments.explain`) or `null`, comments only. `comments` is keyed by option id,
plus `today`. `reopen` lists the rejected options the owner wants back.

| Exit | Meaning | Next |
|---|---|---|
| 0 | stdout is the answer | Proceed as after any answer |
| 2 | the owner closed the page | Ask in chat what to do; nothing is chosen |
| 3 | still open after 3 hours, stdout is the page id | `fork.py result <page-id>` when the owner says the page is answered. Never open a second page over it |
| 1 | an error, on stderr | Outside agterm give the fork as text; otherwise fix the fragment and show again |

Run `show` as a background Bash call (`run_in_background: true`) and end the turn on the one
line saying which fork is open. Claude Code wakes the session when the command exits, that is
when the owner submits or closes the page, and the exit code and the output are in the
notification. A foreground call is cut at ten minutes, and an answer given after that reaches
nobody. While the page is open no second page opens over it; a message the owner types in the
chat meanwhile is answered in the chat, and the page keeps waiting.
