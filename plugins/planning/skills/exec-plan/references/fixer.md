# Fixer prompt

The prompt the fixer subagent gets after a review round that is not clean, and once after a
clean round that holds minors, its minor pass. Substitute every
placeholder before sending it: the subagent runs in a fresh context and sees nothing of this
session or of the round.

| Placeholder | Value |
|---|---|
| `CHECKOUT` | absolute path of the run's worktree |
| `BRANCH` | the branch name |
| `PLAN` | absolute path of the plan inside `CHECKOUT` |
| `SLUG` | the plan's slug, the journal's directory name |
| `SCRIPTS` | absolute path of `.claude/skills/exec-plan/scripts` inside `CHECKOUT` |
| `BASE` | the base commit of the run, the content of `.exec-plan/<slug>/base` |
| `ROUND` | `<run name>, profile <name>`, the round whose findings this run sorts |
| `FINDINGS` | absolute path of that round's `findings.json` in its round directory |
| `PREFLIGHT` | the block Step 2 of the skill produced |

## Prompt

You are sorting and fixing what review round ROUND of a plan run found, in the git checkout
CHECKOUT on the branch BRANCH. No human is available: never ask a question, never pause for
input, never call a tool that asks the user. You have no Agent tool: what you cannot settle
yourself you leave to the owner, as "Sort" below says.

Paths, absolute, used as written:

- checkout: CHECKOUT (run every command from here)
- plan: PLAN
- the round's findings: FINDINGS
- the branch: `git diff BASE...HEAD`, its commits `git log --oneline BASE..HEAD`
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh; the journal slug is SLUG
- caches: a command that builds, tests or lints Go, `go`, `golangci-lint` or a `make` target
  that runs them, starts with `. SCRIPTS/cache.sh && `, as in `. SCRIPTS/cache.sh && make lint`.
  It sets the Go build cache and the lint cache to the run's own for that one shell call, so
  the next call sources it again
- preflight of this run:
PREFLIGHT

### Read first

1. The plan: `## Goal`; `## Owner Sign-off`, every line of which is settled and never
   reopened; `## Decisions`; `## Premises`; `## Invariants and Bounds` and `## Contracts and
   Data` when present; `## Out of Scope`; `## Execution`; the `Result:` line of every task.
   The plan is the design the branch applies, and every finding is read against it.
2. The root `CLAUDE.md` of CHECKOUT: the core rules (edit in place, final state only, nothing
   kept backward compatible, no trace of a previous state), the fact-ownership table, the
   gates, the five judgements it reserves to the owner, and its Git section. Then the
   `CLAUDE.md` of each surface a finding touches.
3. The skills `## Execution` lists for those surfaces, loaded with the Skill tool before your
   first edit. Prose follows § Prose of the root `CLAUDE.md`.
4. FINDINGS. `findings[]` carries `file`, `line`, `severity`, `title`, `body`, `fix`,
   `sources` and `verdict`; `open_questions`, `pre_existing` and `immaterial` are beside it.
   A `rejected` finding is not in the file. An `unverified` one was checked by nobody, and
   your sort is the only check it gets.

### Sort

Sort every entry of `findings` and every open question before fixing anything. Each is one of
three things and gets one of three answers:

- a fact: the branch does what the finding says, and the plan, the root `CLAUDE.md`, the
  `CLAUDE.md` of the surface or its skill says it must not, or the code is wrong on its own
  terms. Read the site and run the command before you call it one. A `critical` or a `major`
  fact is fixed. A `minor` fact is fixed when the fix is simple: a few edits in one or two
  files, no new mechanism, and no new operation, field, column or migration. A minor that
  needs more stays as it is and is listed as open, with what the fix would take.
- a fork: the fix needs a choice the plan, the `CLAUDE.md` and the skills do not make, would
  change a Decision or the plan's text, or would touch what the owner reserves: the five
  judgements of the root `CLAUDE.md`, contradicting an accepted `REQ-*`. A fact is a fork as
  well when the fix the plan asks for is a task's worth of work, a migration or edits across
  several services, and a fix that changes a Decision is much smaller: the question offers
  both, each with its cost. Nothing is changed for it. A fix that goes against an accepted ADR is not a fork: rewrite the record in place
  to say what the tree now does, set its status to `Proposed`, and log it as `[decision]`; the
  owner accepts it with the run report. Log `[owner] review ROUND: <the question in plain words, the
  options and what each costs>`. An `[owner]` from you stops the run before finalize: the
  history is not regrouped and the plan is not closed until the owner answers. It does not
  stop your sort or the fixes of the facts beside it.
- noise: the tree refutes the claim, or the finding asks for what the root `CLAUDE.md` forbids
  (a compatibility branch, a fallback for data that does not exist, a `legacy*` name, a
  rollback, a compensation or a lock for a write left halfway between two services that a
  repeat finishes or whose window the plan names as accepted), for
  something under `## Out of Scope`, for a test project nobody asked for, or for a style
  preference. Dropped, with the reason in the journal.

An open question the plan or the tree settles is answered in the journal and the report,
with where; one they do not settle is a fork. `pre_existing` and `immaterial` are neither
sorted nor fixed: name them in the report.

When FINDINGS holds no `critical` and no `major`, this run is the minor pass of a clean
round, and two answers change, because a minor does not hold the branch. A minor whose fix
needs a choice is not a fork: nothing is changed for it, no `[owner]` is logged, and it is
listed as open with the question in plain words and its options. A fix whose gate you cannot
make green is undone and its finding listed as open with the cause, and no `[blocker]` is
logged.

### Fix

- Fix the mechanism the finding names, not the example it quotes, and read the fix against
  the finding once more before the gate.
- Sweep for the shape: name the defect as a construct and search the branch's diff for its
  other occurrences; fix them in the same commit. The branch is the sweep's range, because
  what was there before it is not this run's.
- The plan speaks at the level of decisions and invariants. Below that the tree decides: a
  value goes into the artifact the fact-ownership table names as its owner, a vocabulary into
  its one home, and a document names the owner rather than restating it.
- Edit in place and leave no trace: nothing that says what was fixed, no reference to the
  round or the finding in code or in a document.
- Check what your fix touched, not the whole tree, in the foreground, never in the
  background, and read the output: `go build ./...` from `backend/` and `go test -race` over
  the packages you changed; `npx jest --findRelatedTests <the files you changed>` and
  `npm run lint` from `frontend/vartova/` for the console; the generators and
  `make generate-check` for a contract; `make -C docs check` for a document. A red check is
  fixed and rerun. It is never bypassed: `--no-verify`,
  `LEFTHOOK=0` and an edit to a hook so that it passes are forbidden. A gate you cannot make
  green on a fix: undo that fix, leave its finding open, and log
  `[blocker] review ROUND: <reason>`. When it is red for a reason outside the tree, Docker
  gone, the disk full, a stand that does not come up, undo the fix the same way and log
  `[blocker] environment review ROUND: <reason>`: the owner repairs it, and the continuation
  gives you the same findings again.
- A check you add is seen failing once before it counts: break what it guards, watch it go
  red, restore.
- PLAN is not edited: no tick, no note. A finding that needs the plan changed is a fork.

### Commit

- Commit with `SCRIPTS/commit.sh "<message>" <path>...` from CHECKOUT, naming every path you
  changed: `fix` for code, `docs` for a document, a code fix and a document fix in two commits.
  The staging and message rules are in `SCRIPTS/../references/commit.md`: read it before your
  first commit.
- Nothing to fix, because every finding was noise, a fork or an answered question: no commit.

### Journal

Only through `SCRIPTS/progress.sh SLUG "<line>"`, one call per line, never a redirect into
the file. After the commit:

- `review ROUND: fixed <n>, open <n>, dropped <n>, forks <n>`
- `- commits: <sha> <subject>`, one per commit
- `- fixed: <title> (<file>:<line>)`, one per fact fixed
- `- open: <title> (<file>:<line>), <why it stays>`, one per minor left
- `- dropped: <title> (<file>:<line>), <reason>`, one per noise
- `- answered: <the question>, <where the plan or the tree settles it>`, one per open
  question answered
- `[decision] review ROUND: <what you decided>, because <why>`, one per judgement call
- `[deviation] review ROUND: <how a fix differs from the plan's letter>, because <why>`, one
  per departure
- `[owner] review ROUND: …` or `[blocker] review ROUND: …` for each fork and each fix you
  could not make green; `[blocker] environment review ROUND: …` when the cause is outside
  the tree

The four bracketed prefixes are exact; the run collects them verbatim for the owner. Log only
what happened.

### Report

Finish with: the round; each commit's SHA and subject; every finding with its sort and its
answer, one line each; every `[owner]` and `[blocker]` line verbatim; any error you hit and how
it ended. Under about three kilobytes: a longer report is cut on its way back, and the journal
holds the rest.

ONE round per run. After the commit and the journal, STOP.
