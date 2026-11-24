# Integrate prompt

The prompt the integrator subagent gets when every lane of a wave has ended. It brings the
lanes that closed their task into the run's branch of their repository, regenerates what is
generated, makes each repository of the wave build and lint clean with the tests green where
the lanes of the wave met, and carries every lane's marks into the plan, as the executor of
the plan and not as a reviewer. One integrator works through every repository of the wave, so
one agent writes the plan. The tests of the whole tree are not its job: the run checks the
whole tree once, after the last wave. Substitute every
placeholder before sending it: the subagent runs in a fresh context and sees nothing of this
session or of the lanes.

| Placeholder | Value |
|---|---|
| `REPOS` | each repository a lane of this wave or a review lane runs in, one per line: `<repo>`, run worktree `<path>`, branch `<name>`, base `<sha>`, the content of `<journal>/base.<repo>`, tip `<sha>`, the `HEAD` of that run branch at the start of the wave, which its lanes were cut from |
| `PLAN` | absolute path of the plan, the one the journal's `plan` names |
| `MODE` | `tracked`, the plan is the copy in the home repository's run worktree and its marks are committed there, or `untracked`, the plan is edited in place and never committed |
| `HOME` | in a tracked plan, the absolute path of the home repository's run worktree, which holds PLAN; `none` in an untracked plan |
| `SLUG` | the plan's slug, the journal's directory name |
| `JOURNAL` | absolute path of the run's journal |
| `SCRIPTS` | absolute path of the skill's `scripts/` in the plugin, `${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts` expanded |
| `RULES` | absolute path of the plugin's `scripts/rules.sh`, `${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh` expanded |
| `WAVE` | the wave's number |
| `LANES` | the lanes to integrate, in merge order, one per line: `task N: <title>`, repository `<repo>`, branch `<name>`, worktree `<path>`, progress file `<path>` |
| `STOPPED` | the lanes that stopped and are not merged, one per line in the same form, or `none` |
| `REVIEW` | `none` in a plain run; in a run with a peer, the review lanes to merge before LANES, oldest first, one per line: `review wave N`, repository `<repo>`, branch `<name>`, worktree `<path>` |
| `PREFLIGHT` | the block Step 2 of the skill produced |
| `RETRY` | empty on the first attempt; on the second, "This is the second and last attempt at integrating this wave. The first attempt left:" followed by its errors, its report and the journal lines it wrote |

## Prompt

Every lane of wave WAVE of a plan run has ended. You bring the lanes that closed their task
into the run's branch of their repository, each in that repository's run worktree as REPOS
names it, and you make each repository of the wave build and lint clean and the tests green
where the lanes of the wave met. Then you carry every lane's marks into the plan. The tests of
the whole tree are not yours: the run checks the whole tree once, after the last wave.
No human is available: never ask a question, never pause for input, never call a tool that
asks the user. You have no Agent tool.

Paths, absolute, used as written:

- the repositories of this wave, each with its run worktree, branch, base and the wave's tip
  in it; every command of a repository runs from its run worktree:
REPOS
- plan: PLAN, a MODE plan; in a tracked plan its run worktree is HOME
- lanes to merge, in this order:
LANES
- lanes that stopped, not merged:
STOPPED
- review lanes, merged before the lanes above:
REVIEW
- journal: JOURNAL. Every shell call that runs or sources a file of SCRIPTS sets it first,
  `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh "<line>"`: the scripts refuse without it
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh
- project rules: `bash RULES` from a repository's run worktree prints the rules of that
  repository, or nothing. A section is read by its heading; a section the file leaves out takes
  the default that `$(dirname RULES)/../references/rules.md` gives it
- caches: a command that builds, tests or lints Go, `go`, `golangci-lint` or a `make` target
  that runs them, starts with `EXEC_PLAN_JOURNAL=JOURNAL . SCRIPTS/cache.sh && `, as in
  `EXEC_PLAN_JOURNAL=JOURNAL . SCRIPTS/cache.sh && make lint`. It sets the Go build cache and
  the lint cache to the run's own for that one shell call, so the next call sources it again
- preflight of this run:
PREFLIGHT

RETRY

### Read first

1. The plan: `## Goal`; `## Owner Sign-off`; `## Decisions`; `## Execution`, its Shared files
   table above all; the `Result:`, `Decision:`, `Repo:` and `After:` of every task in LANES. The
   merge order of LANES follows the table: the task it names as second comes after the one it
   names as first.
2. The journal `JOURNAL/progress.md`: the lines of every lane in
   LANES, their `[decision]` and `[deviation]` lines in particular. A `[deviation]` that names
   a file outside the lane's `Where:` is where a conflict between two lanes comes from, and the
   two lines say what each meant.
3. The project rules of each repository of REPOS, the sections `Gates`, `Environment` and
   `Records`; `Environment` also says how one repository builds against the run branch of
   another. Then the root `CLAUDE.md` of each run worktree: its rules, where it says who owns a
   value, and its commit rules.
   Then the `CLAUDE.md` of each surface a conflict or a red check lands in,
   and the skills `## Execution` lists for it, loaded with the Skill tool before your first
   edit. Prose follows the prose rules of the project's `CLAUDE.md`, where it states them.

### Merge

`git status --porcelain` prints nothing in every run worktree of REPOS, and in HOME, before you
start; anything printed is a stop: `[blocker] integration WAVE: dirty tree: <repo>: <paths>`.

For each lane of LANES, in order, in the run worktree of its repository, <tip> being the tip REPOS
gives that repository:

1. Note the lane's commits, `git log --oneline <tip>..<lane branch>`: they become the body of
   its commit message below.
2. `git merge --squash <lane branch>`. One three-way merge; its conflicts are resolved once,
   here. No merge commit is made: `base.sh` refuses a merge commit between the repository's
   base and `HEAD` on the next start, and the finalize regroups the range anyway.
3. Resolve every conflict in the working tree:
   - a generated file, the output of a generator the `Gates` section names: take either side,
     the generators rewrite it below;
   - lines a gate command writes into a hand-written file, such as the coverage lines a
     record carries, by the `Gates` section: take either side, the command rewrites them below;
   - a hand-written file: read both tasks' `Result:` and `Decision:` and both lanes' journal
     lines for that file, and write the version under which both results hold, where an integrator usually resolves only the mechanical conflicts. Log
     `[decision] integration WAVE: <repo>: <file>: <what you kept of each side>, because <why>`. A
     conflict under which both results cannot hold is a stop:
     `[blocker] integration WAVE: <repo>: <file>: <the two intents in plain words>`, the tree left in
     its conflicted state for the owner and nothing merged after it.
4. Regenerate before the commit when the merge can have left a generated file stale: step 3
   took a side of a conflict, or an earlier lane of this merge also changed what a generator
   reads, a contract or a file a gate command reads to write its lines. Then run the
   generators and those commands, as the `Gates` section names them: the pre-commit hooks
   build and check what is staged. Otherwise skip them: the lane ran the generators of what it
   changed, and its output is current. Then `git restore --staged .`, so
   the index holds nothing: `commit.sh` refuses an index that holds a path it is not given.
   Then carry the lane's marks into PLAN, as "Carry the marks" below says. Then commit the
   lane as one commit, naming every path `git status --porcelain` lists:
   `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <paths...>`. The tree was clean
   before the squash, so every path listed is this lane's merge, its regeneration, or PLAN
   when HOME is this run worktree. A path the lane deleted is named like
   any other: it is gone from the tree and is staged as its removal. The message is
   the task's title in the project's commit form, `type(scope): <the task's title>` unless
   `SCRIPTS/../references/commit.md` finds another,
   with the lane's commit subjects as the body, one per line, not a `chore: integrate wave` message. Pass
   the message as one argument with real newlines inside the quotes, never through
   `git commit -F -`. End it with the attribution line your session's instructions give, when
   they give one. A hook that fails names its cause: fix the cause and commit again. In a
   tracked plan whose HOME is another run worktree, commit PLAN from HOME right after, alone:
   `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "docs(plans): mark task N of the SLUG plan"
   <PLAN relative to HOME>`, the message in the project's commit form. In an untracked plan the
   edit in place is all: nothing commits it. So a merged lane has its ticks in PLAN before the
   next lane starts, and a stop later in the wave never leaves one merged and unticked.

A lane never edits PLAN, so no lane's merge touches it. A lane in STOPPED is not merged and not
read for its diff: only its marks reach PLAN, as "Carry the marks" below says.

A lane in REVIEW holds the fixes of a review of an earlier wave in one repository, and is
merged first, into the run worktree of that repository, by the same four steps. It closes no task and ticks nothing. Its message is `fix(<scope>): <what the
fixes make true>`, with its commit subjects as the body, and after the commit it is logged as
`review wave N: merged`. A conflict with a lane of LANES is
resolved like any other: the fix holds and the task's `Result:` holds. LANES may be `none`,
when only review lanes are left after the last wave: steps 5 and 6 of the checks below then
run over what the review lanes touched.

### Regenerate and check

After the last lane, in every repository of REPOS, from its run worktree, in the foreground,
never in the background, each to its end, reading the output. A repository whose build reads
another repository of the run, as its `Environment` section says, is built and linted here too
when that other one changed in this wave, the order a repository another builds against first. A check prints its exit code in the same call,
`<command>; echo "exit=$?"`, and never through a pipe, whose exit code is the pipe's last
command: a check is never run a second time to learn how it ended. A surface whose packages
were never installed here gets what the `Environment` section asks a fresh checkout to install
first. The commands are the ones the `Gates` section names:

1. the generators, then their drift check, when step 4 regenerated for any lane or a fix
   of yours changed what a generator reads
2. the docs check, with the steps the `Gates` section runs before it, on the same condition as
   step 1; otherwise a lane that changed a document ran it itself, and the docs hook, where the
   project has one, ran it on that lane's commit and on the commit that carried PLAN
3. the build of the whole tree
4. the lint of the whole tree
5. the tests where the lanes of the wave met. A surface, a component with tests of its own, is
   met when two or more lanes of LANES and REVIEW changed files in it, generated
   files included, when step 3 resolved a conflict in it, or when a fix of yours changed it.
   A surface only one lane changed is not met: that lane ran its tests on the code the merge
   brought in unchanged. For each met surface, its tests narrowed to the files
   `git diff --name-only <tip>..HEAD` lists in it: the packages, the modules or the specs that
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
  check, run alone, is red at <tip> as well, the tip of that repository. Tell it by running only
  the red test at <tip>, in a scratch worktree beside the repository's run worktree
  (`git worktree add --detach "$(dirname <run worktree>)/SLUG-tip" <tip>` from that run worktree,
  removed afterwards; not under `/private/tmp`, which Docker does not share, so a stand raised
  from there mounts nothing). Red there as well: leave it, log
  `[deviation] integration WAVE: <repo>: <check> red at the wave's tip as well: <test or cause>`, and
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
- PLAN gets no tick and no note from you beyond the marks "Carry the marks" brings.

Commit each fix with `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <path>...` from
the run worktree of its repository, naming every path you changed:
`fix(<scope>): …` for code, `docs` for a document, `test` for a test; regenerated output goes
in its own commit, `chore(<scope>): regenerate …`. The staging and message rules are in
`SCRIPTS/../references/commit.md`: read it before your first commit.

### Carry the marks

Every lane writes its marks into its own progress file and never into PLAN; you carry them.
The checkbox lines of the lane's task in PLAN take the state its progress file holds, line for
line: a `[x]` there is `[x]` in PLAN, a ` ⚠️ <reason>` there is on the same line in PLAN, and a
mark the file no longer has is gone from PLAN too. It is not a union of the two. Nothing else in
PLAN changes: no other task, no heading, no note.

- A lane of LANES is carried in step 4 of its merge, before its commit: its file has every
  checkbox `[x]`.
- A lane of STOPPED is carried once every check is green, as its file stands, its code not
  merged: the owner reads its `⚠️` in PLAN and answers there. In a tracked plan commit PLAN from
  HOME, alone, `docs(plans): mark the stopped tasks of the SLUG plan` in the project's commit
  form; in an untracked plan the edit in place is all.
- A wave that stopped before its last lane has carried the lanes it merged; the lanes it did
  not reach and the lanes of STOPPED keep their marks in their progress files.

### Prove

`git status --porcelain` prints nothing in every run worktree of REPOS and in HOME. Every task
in LANES has every checkbox `[x]` in PLAN. Every lane of STOPPED has its marks in PLAN. Every
search of step 6 passed. Then log the wave as integrated.

### Journal

Only through `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh "<line>"`, one call per line, never
a redirect into the file:

- `wave WAVE: integrated, lanes <tasks>, <n> conflicts, <n> fixes`
- `- commits: <sha> <subject>`, one per commit
- `- conflict: <repo>: <file>: <how it was resolved>`, one per conflict
- `- fixed: <repo>: <check>: <what was red and why>`, one per fix
- `- validation: <repo>: <each check and its result>`, one per repository
- `[decision] integration WAVE: <what you decided>, because <why>`, one per judgement call, a
  flake included
- `[deviation] integration WAVE: <repo>: <check> red at the wave's tip as well: …`, one per failure
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
