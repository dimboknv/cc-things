# Whole-tree prompt

The prompt the subagent gets once every task of the plan is closed, before the first review
round, once per repository of the plan. A task checks only what it touched; this run checks the
whole tree of one repository, and it fixes what it finds red, as the executor of the plan and
not as a reviewer. Substitute every placeholder before
sending it: the subagent runs in a fresh context and sees nothing of this session.

| Placeholder | Value |
|---|---|
| `CHECKOUT` | absolute path of the run worktree of the repository this run checks |
| `BRANCH` | the branch name |
| `REPO` | the directory name of that repository |
| `PLAN` | absolute path of the plan, the one the journal's `plan` names |
| `SLUG` | the plan's slug, the journal's directory name |
| `JOURNAL` | absolute path of the run's journal |
| `SCRIPTS` | absolute path of the skill's `scripts/` in the plugin, `${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts` expanded |
| `RULES` | absolute path of the plugin's `scripts/rules.sh`, `${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh` expanded |
| `BASE` | the base commit of this repository, the content of `<journal>/base.<repo>` |
| `PREFLIGHT` | the block Step 2 of the skill produced |
| `SCOPE` | `full`, or `light` for a plan whose Execution carries the light Mode line |
| `RETRY` | empty on the first attempt; on the second, "This is the second and last attempt at the whole-tree check. The first attempt left:" followed by its errors, its report and the journal lines it wrote |

## Prompt

Every task of a plan is done, in the git checkout CHECKOUT on the branch BRANCH, the run
worktree of the repository REPO. Each task checked only the packages it touched. You check the
whole tree of this repository, and you make it green. The other repositories of the plan get
their own run of this check. No human
is available: never ask a question, never pause for input, never call a tool that asks the user.
You have no Agent tool.

Paths, absolute, used as written:

- checkout: CHECKOUT (run every command from here)
- plan: PLAN, read only
- the branch: `git diff BASE...HEAD`, its commits `git log --oneline BASE..HEAD`
- journal: JOURNAL. Every shell call that runs or sources a file of SCRIPTS sets it first,
  `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh "<line>"`: the scripts refuse without it
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh
- project rules: `bash RULES` from CHECKOUT prints them, or nothing. A section is read by
  its heading; a section the file leaves out takes the default that
  `$(dirname RULES)/../references/rules.md` gives it
- caches: a command that builds, tests or lints Go, `go`, `golangci-lint` or a `make` target
  that runs them, starts with `EXEC_PLAN_JOURNAL=JOURNAL . SCRIPTS/cache.sh && `, as in
  `EXEC_PLAN_JOURNAL=JOURNAL . SCRIPTS/cache.sh && make lint`. It sets the Go build cache and
  the lint cache to the run's own for that one shell call, so the next call sources it again
- preflight of this run:
PREFLIGHT

RETRY

### Read first

1. The plan: `## Goal`; `## Owner Sign-off`, every line of which is settled and never
   reopened; `## Decisions`; `## Out of Scope`; `## Execution`; the `Result:` line of every
   task, those of this repository's tasks above all: a task whose `Repo:` names REPO, or with
   no `Repo:` line when REPO is the home repository. A fix you make keeps every `Result:` true.
2. The project rules, the sections `Gates`, `Environment` and `Records`: the whole-tree
   checks, what a checkout needs, how this repository builds against the run branch of another
   repository of the plan, and the judgements only the owner makes. Then the root
   `CLAUDE.md` of CHECKOUT: its rules, where it says who owns a value, and its commit rules.
   Then the `CLAUDE.md` of each surface a red check lands in.
3. The skills `## Execution` lists for those surfaces, loaded with the Skill tool before your
   first edit. Prose follows the prose rules of the project's `CLAUDE.md`, where it states
   them.

### Run

From CHECKOUT, in the foreground, never in the background, each to its end, reading the output.
A surface whose packages were never installed here gets what the `Environment` section asks a
fresh checkout to install first. The commands are the whole-tree checks the `Gates` section
names, in this order, each one the project has:

1. the generators' drift check
2. the docs check, with the steps the `Gates` section runs before it
3. the build
4. the lint
5. the tests

These run every component, whatever the branch touched: a branch breaks a neighbour it never
opened.

The scope of this run is SCOPE. When it is `light`, the first four run as written and step 5
runs only the tests of the components the branch touched, by `git diff --stat BASE...HEAD`. A
change to the input of a generator touches every component whose code the generator writes
from it; the `Gates` section names which those are. Name the tests you ran and the ones you
left in the validation line of the journal.

### Fix

- A red check is fixed and the whole list runs again from the check that went red, until it is
  green. Fix the cause, never the check: `--no-verify`, a variable that turns the hooks off
  (`LEFTHOOK=0`, `HUSKY=0`), a skipped or deleted test and an edit to a hook or a lint config
  so that it passes are forbidden.
- A test that fails once and passes on a rerun with nothing changed is a flake: rerun it once,
  and when it passes, log it as `[decision]` with the test's name and go on. A test red twice
  is not a flake.
- A failure the branch did not cause is not yours to fix: a check is not the branch's when the
  same check, run alone, is red at BASE as well. Tell it by running only the red test at BASE, in a scratch worktree
  beside the run worktree (`git worktree add --detach "$(dirname CHECKOUT)/SLUG-base" BASE`,
  removed afterwards; not under `/private/tmp`, which Docker does not share, so a stand raised
  from there mounts nothing). Red there as well: leave it, log `[deviation] whole tree: REPO:
  <check> red at the base as well: <test or cause>`, and go on. It does not stop the run, and
  the tree counts as green without it: the run report lists it as open.
- A check red for a reason outside the tree: Docker gone, the disk full, a stand that does
  not come up. It is neither fixed in the tree nor the owner's judgement. A cause you removed
  yourself, with the checks green after it, is a `[decision]`. One you cannot remove: log
  `[blocker] environment whole tree: REPO: <reason>` and stop. What on the host is not the run's is
  not yours to clear.
- A fix that needs a choice the plan does not make, or would change a Decision, a `Result:` or
  what the owner reserves: change nothing for it and log `[owner] whole tree: REPO: <the
  question in plain words, the options and what each costs>`.
- A red check whose cause lies in another repository of the plan, one this repository builds
  against: change nothing there, it is not your checkout. Log
  `[blocker] whole tree: REPO: red because of <repo>: <the check and its cause>` and stop.
- Everything else is the run's own: what the tree already does, you repeat; the fix is the
  simplest one; a value goes into the artifact the project's rules name as its owner.
- PLAN is not edited: no tick, no note.

### Commit

- Commit each fix with `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <path>...` from CHECKOUT: `fix(<scope>): …`
  for code, `docs` for a document, `test` for a test. The staging and message rules are in `SCRIPTS/../references/commit.md`: read it before your
  first commit.
- Nothing red: no commit.

### Journal

Only through `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh "<line>"`, one call per line, never
a redirect into the file:

- `whole tree: REPO: <green | red>, <n> fixes`, with `, light` after it when SCOPE is `light`
- `- commits: <sha> <subject>`, one per commit
- `- fixed: <check>: <what was red and why>`, one per fix
- `- validation: <each check and its result>`
- `[decision] whole tree: REPO: <what you decided>, because <why>`, one per judgement call, a
  flake included
- `[deviation] whole tree: REPO: <check> red at the base as well: …`, one per failure the
  branch did not cause
- `[owner] whole tree: REPO: …`, `[blocker] whole tree: REPO: …` or
  `[blocker] environment whole tree: REPO: …` when you stopped with a check red

The bracketed prefixes are exact; the run collects them verbatim for the owner. Log only what
happened.

### Report

Finish with: each check and its result, trimmed; each commit's SHA and subject; every red you
fixed and its cause; every `[deviation]`, `[owner]` and `[blocker]` line verbatim; any error
you hit and how it ended. Under about three kilobytes: a longer report is cut on its way back,
and the journal holds the rest.

After the commits and the journal, STOP.
