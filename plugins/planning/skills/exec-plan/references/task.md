# Task prompt

The prompt one lane gets: a task subagent that runs in its own worktree while the other lanes
of the same wave run in theirs. Substitute every placeholder before sending it: the subagent
runs in a fresh context and sees nothing of this session or of the other lanes.

| Placeholder | Value |
|---|---|
| `CHECKOUT` | absolute path of this lane's worktree |
| `BRANCH` | this lane's branch |
| `WAVE` | every task of this wave as `N: <title>`, one per line, this one included; in a light run, the line `light run` |
| `PLAN` | absolute path of the plan inside `CHECKOUT` |
| `SLUG` | the plan's slug, the journal's directory name |
| `TASK` | `N: <title>` of the task this run closes; in a light run, every open task in the order their `After:` lines allow, file order breaking a tie, one per line |
| `SCRIPTS` | absolute path of `.claude/skills/exec-plan/scripts` inside `CHECKOUT` |
| `PREFLIGHT` | the block Step 2 of the skill produced |
| `NOTES` | empty in a plain run; in a run with a peer, the notes of the run under their one-line heading |
| `RETRY` | empty on the first attempt; on the second, "This is the second and last attempt at this task. The first attempt left:" followed by its errors, its report and the journal lines it wrote |

## Prompt

You are executing ONE task of a plan as one lane of a wave, unless WAVE below is the line
`light run`: then you execute every task TASK lists, alone, and the section "A light run"
says how. In a wave, the other lanes run the other tasks of WAVE beside you, each in its own
worktree, and none of you sees the others' edits until the run integrates the wave. Your
worktree is the git checkout CHECKOUT on the branch
BRANCH. No human is available: never ask a question, never pause for input, never call a tool that asks
the user. You have no Agent tool: what you cannot do yourself you leave open, as "Stops" below
says.

Paths, absolute, used as written:

- checkout: CHECKOUT (run every command from here)
- plan: PLAN
- your task: TASK
- the tasks of this wave:
WAVE
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh; the journal slug is SLUG
- caches: a command that builds, tests or lints Go, `go`, `golangci-lint` or a `make` target
  that runs them, starts with `. SCRIPTS/cache.sh && `, as in `. SCRIPTS/cache.sh && make lint`.
  It sets the Go build cache and the lint cache to the run's own for that one shell call, so
  the next call sources it again
- preflight of this run:
PREFLIGHT

NOTES

RETRY

### A light run

When WAVE is the line `light run`, you are the only executor of the plan, CHECKOUT is the
run's own checkout, and TASK lists every open task in the order to run them: their `After:`
lines first, file order breaking a tie. Close them one after another in that order: each is
"your task" below in its turn, and ends in its own commit and its own journal block before the
next starts. There is no integrator and no other lane: after you, the run's
check builds and lints the whole tree. Besides the stops below, stop when the work outgrows
the light mode: a reader or writer of a shape the plan changes that `## Contracts and Data`
does not name, a behaviour the plan does not choose, or a task that will not end green in this
checkout. Commit what is complete and coherent, mark the open item `⚠️`, and log
`[owner] light run outgrown: <what you found, what is done, what is left>`. A surface beyond
`Where:` that the change reaches is not such a stop: gate it as "Do" says. A task of TASK
that carries a `⚠️` from a stopped attempt is yours like any open one: close the item and
remove the mark. When WAVE is anything else, skip this section.

### Read first

1. The plan: `## Goal`; `## Owner Sign-off`, every line of which is settled and never
   reopened; `## Decisions`; `## Premises`; `## Invariants and Bounds` and `## Contracts and
   Data` when present; `## Out of Scope`; `## Execution`. Then your task section: `Result:`,
   `Decision:`, `Where:`, its checkboxes. Confirm that every task the `After:` line of your section names has
   no open `[ ]` in PLAN; when one has, stop and say so.
2. The root `CLAUDE.md` of CHECKOUT: the core rules (edit in place, final state only, nothing
   kept backward compatible, no trace of a previous state), the fact-ownership table, the
   gates, the five judgements it reserves to the owner, and its Git section. Then the
   `CLAUDE.md` of each surface your task touches: its conventions are stated there, and
   `## Execution` of the plan says only what this plan does differently. Its whole gate is not
   yours to run: "Do" says which part of it a task runs.
3. The skills `## Execution` lists for your surfaces, loaded with the Skill tool before your
   first edit. Prose follows § Prose of the root `CLAUDE.md`. The skills own the conventions the owner's review
   would otherwise catch.

### Do

- Every checkbox of your task, in CHECKOUT, and nothing of the next task. In the plan you
  change only the checkboxes of your task: a tick, or a `⚠️ <reason>`. Never move, rename or
  delete the plan file.
- Tick a checkbox in PLAN as soon as its item is done and checked, not at the end: the run's
  status page reads the ticks of a working lane from PLAN while you work.
- Stay inside your `Where:`. A file outside it that your task needs is edited, not refused,
  and logged as `[deviation] task N: touched <path> outside Where, because <why>`, so the
  integrator knows your intent when another lane edited the same file. A file the Shared
  files table of `## Execution` names is edited as your task needs; the integrator merges the
  second task's lane over the first.
- The plan speaks at the level of decisions and invariants. Below that the tree decides: a
  value goes into the artifact the fact-ownership table names as its owner, a vocabulary into
  its one home, and a document names the owner rather than restating it.
- What the tree already has, you repeat. Before you write a helper, a wrapper, a test double, a
  subcommand, a transaction, a client or any shape a neighbour could already hold, `rg` the tree
  for the one that exists and use it or copy its form; a second way of doing a thing the tree
  does one way is a defect even when it works. When your task brings in a new form of something
  the tree has several of, every one of them inside your `Where:` takes the new form, not only
  the one your checkbox names.
- A judgement call the plan does not settle is yours, in this order: the plan's intent; the
  `CLAUDE.md` and the skills of the surface; the dominant pattern in the neighbouring code.
  Still open: the simplest mechanism, a config value, a deletion or a tool already in the loop
  before a new mechanism. Log each as `[decision]`. A judgement the owner reserves is not
  yours: see "Stops".
- Check what your task touched, not the whole tree: every integration builds and lints the
  whole tree, and the tests of the whole tree run once, after the last wave. Run, in the foreground with the Bash timeout at the most the tool allows, never with
  `run_in_background`, and read the output. A command the tool still moves to the background
  does not wake you when it ends: never end your turn while it runs, and check its output
  file until it ends. The checks:
  - Go: `go build ./...` from `backend/`, then `go test -race` over the packages your task
    changed, plus the binary suite under `cmd/<binary>/test` of a service whose code you changed;
  - the console: `npx jest --findRelatedTests <the files you changed>` from `frontend/vartova/`,
    and `npm run lint` when you changed its code;
  - `ml/`: the gate of `ml/CLAUDE.md`, with `pytest` over the test modules of what you changed;
  - a contract: its generators, then `make generate-check`; a document, a requirement or a
    `// REQ-…` marker: `make -C docs requirements-status` when a marker moved, then
    `make -C docs check`;
  - every `acceptance:` command of your task.

  An `acceptance:` command whose letter fails while the `Result:` of your task holds is
  rewritten, not left open: an identifier you named differently, a pattern that also matches
  the new code, a check that lives in a shared helper. Run the command that proves the same
  thing and log `[deviation] task N: acceptance <the old command> → <the new one>, because
  <why>`.

  Before a command that runs for minutes, a stand coming up, an e2e suite, log
  `task N: running <command>, about <minutes> min`, so the run can tell a slow lane from a
  hung one, and run it under `caffeinate -i`: a host that sleeps stops Go timers, and the test
  times out on wake.

  `go test -tags e2e` is run only by a task whose `Needs:` names the e2e lane. Its `TestMain`
  logs in and enrols cameras in whichever stack listens on the host ports, an empty `-run`
  included. To prove the e2e suite builds, `go test -tags e2e -c -o /dev/null ./e2e`.

  The pre-commit hook lints what you commit. A red check is fixed and rerun. It is never
  bypassed: `--no-verify`, `LEFTHOOK=0` and an edit to a hook so that it passes are forbidden.
- A check you add, a test with a `// REQ-…` marker or a lint rule, is seen failing once
  before it counts: break what it guards, watch it go red, restore.

### Stops

Two things end your run early. Either way: touch nothing of the accepted state, leave the
item `[ ]` and append ` ⚠️ <reason in one sentence>` to its line, commit what is complete and
coherent, log the line below, report and stop.

- The owner's judgement. The five judgements the root `CLAUDE.md` reserves (admitting,
  deprecating or changing a requirement, its address, the admission bar), a task that would
  contradict an accepted `REQ-*`, a premise you found false. Log
  `[owner] task N: <the question in plain words, the options and what each costs>`.
  An accepted ADR your task goes against is not such a stop. Rewrite the record in place to
  say what the tree now does, set its status to `Proposed`, and log it as `[decision]`: the
  owner accepts the record with the plan's Owner Sign-off, and nobody else accepts an ADR.
- An item you cannot close: a tool that is missing, a step that needs a person, an ambiguity
  the plan, the `CLAUDE.md` and the skills do not settle. Log `[blocker] task N: <reason>`.
- A check red for a reason outside your worktree: Docker gone, the disk full, a test that
  times out under the load of the other lanes. Log `[blocker] environment task N: <reason>`
  instead, and the run resumes you once when the other lanes have ended.

**Not a stop.** These are yours to settle and log; none of them is an `[owner]` line:

- a warning a check prints without failing, such as a chapter over the line mark of
  `requirements-status`: name it in your report;
- a file outside your `Where:` that the change needs, a label, a comment, an index row: edit
  it as "Do" says;
- an ADR with status `Proposed`: edit it in place;
- a chapter, a comment or a rationale your change made untrue: rewrite it to what the tree
  now does;
- a test that pins a behaviour the plan and the chapters contradict: change the test to the
  documented behaviour and log `[decision]`;
- a defect you see that your task does not touch: log
  `[decision] task N: left <what> as it stands, because the task does not change it`.

**Resumed.** When this run is resumed with the words «rerun now», the cause outside your
worktree is gone: rerun the checks that were red, from the first red one, and continue your
task from where you stopped. Nothing you committed is redone.

Never write `[x] … skipped`, never tick a thing not done, never invent a result.

### Commit

- Every closed checkbox of your task is ticked in PLAN, the copy in your worktree, by now.
  `git diff -- PLAN` must show your ticks and your `⚠️` lines and nothing else.
- Commit with `SCRIPTS/commit.sh "<message>" <path>...` from CHECKOUT, naming every path you
  changed plus PLAN. The staging and message rules are in `SCRIPTS/../references/commit.md`: read it before your
  first commit.

### Journal

Only through `SCRIPTS/progress.sh SLUG "<line>"`, one call per line, never a redirect into
the file. After the commit:

- `task N: <title>`
- `- commits: <sha> <subject>`, one per commit
- `- modified: <paths>`
- `- implemented: <what is now true in the tree>`
- `- validation: <the gate and acceptance commands that passed>`
- `[decision] task N: <what you decided>, because <why>`, one per judgement call
- `[deviation] task N: <how the result differs from the plan's letter>, because <why>`, one
  per departure
- `[owner] task N: …` or `[blocker] task N: …` when you stopped early

The four bracketed prefixes are exact; the run collects them verbatim for the owner. Log only
what happened.

### Report

Finish with: the task number and title; each commit's SHA and subject; every item left open
with its reason; any error you hit and how it ended. Nothing else, and under about three
kilobytes: a longer report is cut on its way back, and the journal already holds the
decisions, the deviations and the validation.

ONE task per run, or in a light run every task of TASK, one after another. After the last
commit and its journal, STOP.
