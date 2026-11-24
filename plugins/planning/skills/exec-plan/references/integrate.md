# Integrate prompt

The prompt the integrator subagent gets when every lane of a wave has ended. It brings the
lanes that closed their task into the run's branch, regenerates what is generated, and makes
the tree build and lint clean with the tests green where the lanes of the wave met, as the executor of
the plan and not as a reviewer. The tests of the whole tree are not its job: the run checks the
whole tree once, after the last wave. Substitute every
placeholder before sending it: the subagent runs in a fresh context and sees nothing of this
session or of the lanes.

| Placeholder | Value |
|---|---|
| `CHECKOUT` | absolute path of the run's worktree |
| `BRANCH` | the run's branch |
| `PLAN` | absolute path of the plan inside `CHECKOUT` |
| `SLUG` | the plan's slug, the journal's directory name |
| `SCRIPTS` | absolute path of the skill's `scripts/` in the plugin, `${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts` expanded |
| `RULES` | absolute path of the plugin's `scripts/rules.sh`, `${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh` expanded |
| `BASE` | the base commit of the run, the content of `.exec-plan/<slug>/base` |
| `WAVE` | the wave's number |
| `TIP` | the commit the lanes of this wave were cut from, the run branch's `HEAD` at the start of the wave |
| `LANES` | the lanes to integrate, in merge order, one per line: `task N: <title>`, branch `<name>`, worktree `<path>` |
| `STOPPED` | the lanes that stopped and are not merged, one per line, or `none` |
| `REVIEW` | `none` in a plain run; in a run with a peer, the review lanes to merge before LANES, oldest first, one per line: `review wave N`, branch `<name>`, worktree `<path>` |
| `PREFLIGHT` | the block Step 2 of the skill produced |
| `RETRY` | empty on the first attempt; on the second, "This is the second and last attempt at integrating this wave. The first attempt left:" followed by its errors, its report and the journal lines it wrote |

## Prompt

Every lane of wave WAVE of a plan run has ended. You bring the lanes that closed their task
into the run's branch BRANCH in the git checkout CHECKOUT, and you make the tree build and lint
clean and the tests green where the lanes of the wave met. The tests of the whole tree are not yours:
the run checks the whole tree once, after the last wave.
No human is available: never ask a question, never pause for input, never call a tool that
asks the user. You have no Agent tool.

Paths, absolute, used as written:

- checkout: CHECKOUT (run every command from here)
- plan: PLAN
- the run's base: BASE; the wave's tip: TIP
- lanes to merge, in this order:
LANES
- lanes that stopped, not merged:
STOPPED
- review lanes, merged before the lanes above:
REVIEW
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh; the journal slug is SLUG
- project rules: `bash RULES` from CHECKOUT prints them, or nothing. A section is read by
  its heading; a section the file leaves out takes the default that
  `$(dirname RULES)/../references/rules.md` gives it
- caches: a command that builds, tests or lints Go, `go`, `golangci-lint` or a `make` target
  that runs them, starts with `. SCRIPTS/cache.sh && `, as in `. SCRIPTS/cache.sh && make lint`.
  It sets the Go build cache and the lint cache to the run's own for that one shell call, so
  the next call sources it again
- preflight of this run:
PREFLIGHT

RETRY

### Read first

1. The plan: `## Goal`; `## Owner Sign-off`; `## Decisions`; `## Execution`, its Shared files
   table above all; the `Result:`, `Decision:` and `After:` of every task in LANES. The merge
   order of LANES follows the table: the task it names as second comes after the one it names
   as first.
2. The journal `.exec-plan/SLUG/progress.md` in the main checkout: the lines of every lane in
   LANES, their `[decision]` and `[deviation]` lines in particular. A `[deviation]` that names
   a file outside the lane's `Where:` is where a conflict between two lanes comes from, and the
   two lines say what each meant.
3. The project rules, the sections `Gates`, `Environment` and `Records`. Then the root
   `CLAUDE.md` of CHECKOUT: its rules, where it says who owns a value, and its commit rules.
   Then the `CLAUDE.md` of each surface a conflict or a red check lands in,
   and the skills `## Execution` lists for it, loaded with the Skill tool before your first
   edit. Prose follows the prose rules of the project's `CLAUDE.md`, where it states them.

### Merge

`git status --porcelain` prints nothing before you start; anything printed is a stop:
`[blocker] integration WAVE: dirty tree: <paths>`.

For each lane of LANES, in order:

1. Note the lane's commits, `git log --oneline TIP..<lane branch>`: they become the body of
   its commit message below.
2. `git merge --squash <lane branch>`. One three-way merge; its conflicts are resolved once,
   here. No merge commit is made: `base.sh` refuses a merge commit between BASE and `HEAD` on
   the next start, and the finalize regroups the range anyway.
3. Resolve every conflict in the working tree:
   - a generated file, the output of a generator the `Gates` section names: take either side,
     the generators rewrite it below;
   - lines a gate command writes into a hand-written file, such as the coverage lines a
     record carries, by the `Gates` section: take either side, the command rewrites them below;
   - PLAN: the union of both sides' ticks; every `[x]` either side has is `[x]`, and nothing
     else in the file changes;
   - a hand-written file: read both tasks' `Result:` and `Decision:` and both lanes' journal
     lines for that file, and write the version under which both results hold, where an integrator usually resolves only the mechanical conflicts. Log
     `[decision] integration WAVE: <file>: <what you kept of each side>, because <why>`. A
     conflict under which both results cannot hold is a stop:
     `[blocker] integration WAVE: <file>: <the two intents in plain words>`, the tree left in
     its conflicted state for the owner and nothing merged after it.
4. Regenerate before the commit when the merge can have left a generated file stale: step 3
   took a side of a conflict, or an earlier lane of this merge also changed what a generator
   reads, a contract or a file a gate command reads to write its lines. Then run the
   generators and those commands, as the `Gates` section names them: the pre-commit hooks
   build and check what is staged. Otherwise skip them: the lane ran the generators of what it
   changed, and its output is current. Then `git restore --staged .`, so
   the index holds nothing: `commit.sh` refuses an index that holds a path it is not given.
   Then commit the lane as one commit, naming every path `git status --porcelain` lists:
   `SCRIPTS/commit.sh "<message>" <paths...>`. The tree was clean before the squash, so every
   path listed is this lane's merge or its regeneration. A path the lane deleted is named like
   any other: it is gone from the tree and is staged as its removal. The message is
   the task's title in the project's commit form, `type(scope): <the task's title>` unless
   `SCRIPTS/../references/commit.md` finds another,
   with the lane's commit subjects as the body, one per line, not a `chore: integrate wave` message. Pass
   the message as one argument with real newlines inside the quotes, never through
   `git commit -F -`. End it with the attribution line your session's instructions give, when
   they give one. A hook that fails names its cause: fix the cause and commit again.

A lane in STOPPED is not merged, not read for its diff, and not mentioned in PLAN: its ticks
stay in its own worktree.

A lane in REVIEW holds the fixes of a review of an earlier wave, and is merged first, by the
same four steps. It closes no task and ticks nothing. Its message is `fix(<scope>): <what the
fixes make true>`, with its commit subjects as the body, and after the commit it is logged as
`review wave N: merged`. A conflict with a lane of LANES is
resolved like any other: the fix holds and the task's `Result:` holds. LANES may be `none`,
when only review lanes are left after the last wave: steps 5 and 6 of the checks below then
run over what the review lanes touched.

### Regenerate and check

After the last lane, from CHECKOUT, in the foreground, never in the background, each to its
end, reading the output. A check prints its exit code in the same call,
`<command>; echo "exit=$?"`, and never through a pipe, whose exit code is the pipe's last
command: a check is never run a second time to learn how it ended. A surface whose packages
were never installed here gets what the `Environment` section asks a fresh checkout to install
first. The commands are the ones the `Gates` section names:

1. the generators, then their drift check, when step 4 regenerated for any lane or a fix
   of yours changed what a generator reads
2. the docs check, with the steps the `Gates` section runs before it, on the same condition as
   step 1; otherwise the docs hook, where the project has one, already ran the check on every
   lane's commit, since each stages PLAN
3. the build of the whole tree
4. the lint of the whole tree
5. the tests where the lanes of the wave met. A surface, a component with tests of its own, is
   met when two or more lanes of LANES and REVIEW changed files in it, generated
   files included, when step 3 resolved a conflict in it, or when a fix of yours changed it.
   A surface only one lane changed is not met: that lane ran its tests on the code the merge
   brought in unchanged. For each met surface, its tests narrowed to the files
   `git diff --name-only TIP..HEAD` lists in it: the packages, the modules or the specs that
   hold or relate to a changed file, with the suites the `Gates` section ties to them.

   Log the surfaces that were not met in `- validation:`, each with the lane whose tests
   stand for it.
6. the search commands of every `acceptance:` checkbox of every task in LANES, the `rg` and the
   inventory, run as written on this tree. A search that fails here passed in its lane, so the
   merge broke it: fix the tree, never the acceptance.

The build and the lint run every component, whatever the wave touched: a lane breaks a
neighbour it never opened, two lanes that each passed can fail together, and the next wave's
lanes start from this tip. The tests run only where the lanes met: a lane's own tests passed
on the code the merge brought in, and what only the tests of the whole tree catch, the
whole-tree check after the last wave catches.

### Fix

- A red check is fixed, not handed back as an integrator usually does, and the list runs again from the check that went red, until it is
  green. Fix the cause, never the check: `--no-verify`, a variable that turns the hooks off
  (`LEFTHOOK=0`, `HUSKY=0`), a skipped or deleted test and an edit to a hook or a lint config
  so that it passes are forbidden.
- A test that fails once and passes on a rerun with nothing changed is a flake: rerun it once,
  and when it passes, log it as `[decision]` with the test's name and go on. A test red twice
  is not a flake.
- A failure the wave did not cause is not yours to fix: a check is not the wave's when the same
  check, run alone, is red at TIP as well. Tell it by running only the red test at TIP, in a scratch worktree beside the
  run's own (`git worktree add --detach "$(dirname CHECKOUT)/SLUG-tip" TIP`, removed
  afterwards; not under `/private/tmp`, which Docker does not share, so a stand raised from
  there mounts nothing). Red there as well: leave it, log
  `[deviation] integration WAVE: <check> red at the wave's tip as well: <test or cause>`, and
  go on. It does not stop the run: the run report lists it as open.
- A check red for a reason outside the tree: Docker gone, the disk full, a stand that does
  not come up. It is neither fixed in the tree nor the owner's judgement. A cause you removed
  yourself, with the checks green after it, is a `[decision]`. One you cannot remove: log
  `[blocker] environment integration WAVE: <reason>` and stop. What on the host is not the
  run's is not yours to clear.
- A fix that needs a choice the plan does not make, or would change a Decision, a `Result:` or
  what the owner reserves: change nothing for it and log
  `[owner] integration WAVE: <the question in plain words, the options and what each costs>`.
- Everything else is the run's own: what the tree already does, you repeat; the fix is the
  simplest one; a value goes into the artifact the project's rules name as its owner.
- PLAN gets no tick and no note from you beyond the union of the merge.

Commit each fix with `SCRIPTS/commit.sh "<message>" <path>...`, naming every path you changed:
`fix(<scope>): …` for code, `docs` for a document, `test` for a test; regenerated output goes
in its own commit, `chore(<scope>): regenerate …`. The staging and message rules are in
`SCRIPTS/../references/commit.md`: read it before your first commit.

### Prove

`git status --porcelain` prints nothing. Every task in LANES has every checkbox `[x]` in PLAN.
Every search of step 6 passed. Then log the wave as integrated.

### Journal

Only through `SCRIPTS/progress.sh SLUG "<line>"`, one call per line, never a redirect into
the file:

- `wave WAVE: integrated, lanes <tasks>, <n> conflicts, <n> fixes`
- `- commits: <sha> <subject>`, one per commit
- `- conflict: <file>: <how it was resolved>`, one per conflict
- `- fixed: <check>: <what was red and why>`, one per fix
- `- validation: <each check and its result>`
- `[decision] integration WAVE: <what you decided>, because <why>`, one per judgement call, a
  flake included
- `[deviation] integration WAVE: <check> red at the wave's tip as well: …`, one per failure
  the wave did not cause
- `[owner] integration WAVE: …`, `[blocker] integration WAVE: …` or
  `[blocker] environment integration WAVE: …` when you stopped

The bracketed prefixes are exact; the run collects them verbatim for the owner. Log only what
happened. A wave that stopped before its last lane logs
`wave WAVE: stopped after <task>` in place of `integrated`, so the run knows how far the merge
got.

### Report

Finish with: each lane and its commit's SHA and subject; every conflict and its resolution;
each check and its result, trimmed; every red you fixed and its cause; every `[deviation]`,
`[owner]` and `[blocker]` line verbatim; any error you hit and how it ended. Under about three
kilobytes: a longer report is cut on its way back, and the journal holds the rest.

ONE wave per run. After the commits and the journal, STOP.
