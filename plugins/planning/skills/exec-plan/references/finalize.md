# Finalize prompt

The prompt the finalize subagent gets after a clean review round, or after the third.
Substitute every placeholder before sending it: the subagent runs in a fresh context and sees
nothing of this session or of the rounds.

| Placeholder | Value |
|---|---|
| `CHECKOUT` | absolute path of the run's worktree |
| `BRANCH` | the branch name |
| `PLAN` | absolute path of the plan inside `CHECKOUT` |
| `SLUG` | the plan's slug, the journal's directory name |
| `SCRIPTS` | absolute path of `.claude/skills/exec-plan/scripts` inside `CHECKOUT` |
| `BASE` | the base commit of the run, the content of `.exec-plan/<slug>/base` |
| `PREFLIGHT` | the block Step 2 of the skill produced |

## Prompt

You are closing a plan run in the git checkout CHECKOUT on the branch BRANCH: the history is
regrouped and the plan moves into `completed/`. No human is available: never ask
a question, never pause for input, never call a tool that asks the user. You have no Agent
tool.

Paths, absolute, used as written:

- checkout: CHECKOUT (run every command from here)
- plan: PLAN
- base: BASE, the commit the run started from; every range below starts there
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh; the journal slug is SLUG
- preflight of this run:
PREFLIGHT

### Read first

1. The root `CLAUDE.md` of CHECKOUT, its Git section in full: the message format, the split
   where a reviewer's attention splits, the staging rules.
2. The branch: `git log --oneline BASE..HEAD`, `git diff --stat BASE...HEAD`, then the diff
   itself, once, to see which kinds of change it holds and which components they touch.
3. PLAN: `## Decisions`, and the `Result:` and `Decision:` lines of every task. The reset below
   drops the bodies of the branch's commits, and the plan is where the reason of each change
   is kept, so the bodies of the new commits are written from it.

### Regroup the history

The branch's commits are the shape the work was executed in: one or more per task, then the
fixes of the review rounds. The reader of the pull request reads it in another shape, by
kind. Regroup from BASE:

1. `git status --porcelain` prints nothing. Anything printed is a stop:
   `[blocker] finalize: dirty tree: <paths>`.
2. Keep the tip before anything moves: `git branch backup/SLUG-<yyyymmddHHMM> HEAD`, at the
   current tip and not an earlier one, because the check below compares against it. Note
   `git rev-list --count BASE..HEAD`, the count before.
3. `git reset BASE`. The working tree keeps every change of the branch and the index is the
   base, so each group is staged from nothing. Never `--hard`, and never `--soft`: a soft
   reset leaves the whole branch staged, and `commit.sh` refuses an index that holds more than
   the paths it is given.
4. Commit each group with `SCRIPTS/commit.sh "<message>" <path>...` from CHECKOUT, naming the
   paths of that group and nothing else. The staging and message rules are in
   `SCRIPTS/../references/commit.md`: read it before the first commit. Here the index starts
   empty, so there is no `git add` of any kind. A group that changes behaviour gets the body
   the root `CLAUDE.md` Git section asks for: what is now true, from the `Result:` of the
   tasks whose changes the group holds; why this way, from their `Decision:`; then
   `Plan: docs/plans/completed/<file name>`, the path the plan has after the close.
5. Prove nothing moved: `git diff backup/SLUG-<stamp> HEAD` prints nothing, and
   `git status --porcelain` prints nothing. Anything printed is a stop:
   `[blocker] finalize: the regroup lost <paths>`. The backup branch holds the tip.

The groups follow the root `CLAUDE.md`: a semantic edit per component, a mechanical move,
generated artifacts, a large documentation rewrite, each apart wherever they can be
separated, each `type(scope): description`. The plan with its ticks is a documentation change
and travels with the documentation group, or alone as `docs(plans): …` when the branch has no
other. One commit for the whole branch is wrong unless the branch is one small change; a
commit per plan task is wrong too, because that is the shape the work was executed in and not
the shape it is read in. The bar is the reader's attention, and it is a count: past a dozen
or so commits the branch is regrouped, however well each commit is worded on its own. A branch
that is already few and already split by kind keeps its commits; the backup and the check of
step 5 are still made, and "already reads that way" excuses nothing else.

`master` is not merged into the branch and the branch is not rebased onto it: bringing the
branch onto `master` is `/ship`'s step, and a merge commit between the base and `HEAD` is what
`base.sh` refuses on the next run.

### Close the plan

`mv PLAN docs/plans/completed/<file name>`, a plain `mv`, then
`SCRIPTS/commit.sh "docs(plans): close the SLUG plan" docs/plans/<file name>
docs/plans/completed/<file name>`: the old path, gone from the tree, is staged as its removal
and the new one as its addition, in one commit. The plan's text does not change: no status,
no date, no note. Then `git status --porcelain` prints nothing.

### Journal

Only through `SCRIPTS/progress.sh SLUG "<line>"`, one call per line, never a redirect into
the file:

- `finalize: history <n> → <m> commits, backup/SLUG-<stamp>`
- `finalize: plan closed, docs/plans/completed/<file name>`
- `[decision] finalize: <what you decided>, because <why>`, one per judgement call, the
  grouping included when the kinds were not plain
- `[deviation] finalize: <what differs from the plan's letter>, because <why>`
- `[blocker] finalize: …` when you stopped early

The bracketed prefixes are exact; the run collects them verbatim for the owner. Log only what
happened.

### Report

Finish with: the commit count before and after and the backup branch; each group commit's SHA
and subject; the diff check and what it printed; the plan's new path; every `[decision]`, `[deviation]` and `[blocker]` line verbatim; any
error you hit and how it ended.

After the close commit and the journal, STOP.
