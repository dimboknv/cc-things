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
into the run's branch of their repository. You merge each of those lanes in its repository's run
worktree, as the repositories list below names it. You make each repository of the wave build
and lint clean, and you make the tests green where the lanes of the wave met. Then you carry
every lane's marks into the plan. The tests of the whole tree are not yours: the run checks
the whole tree once, after the last wave.
No human is available. Never ask a question. Never pause for input. Never call a tool that
asks the user. You have no Agent tool.

Paths, absolute, used as written:

- the repositories list, the repositories of this wave, each with its run worktree, branch,
  base and the wave's tip in it; every command of a repository runs from its run worktree:
REPOS
- plan: PLAN, a MODE plan; in a tracked plan its run worktree is HOME
- the lanes list, the lanes to merge, in this order:
LANES
- the stopped list, the lanes that stopped, not merged:
STOPPED
- the review list, the review lanes, merged before the lanes list:
REVIEW
- journal: JOURNAL. Every shell call that runs or sources a file of SCRIPTS sets `EXEC_PLAN_JOURNAL`
  first, as in `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh '<line>'`. The scripts refuse a
  call without that variable
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh
- project rules: `bash RULES` from a repository's run worktree prints the rules of that
  repository, or nothing. A section is read by its heading. A section the file leaves out takes
  the default that `$(dirname RULES)/../references/rules.md` gives it
- caches: a command that builds, tests or lints Go, `go`, `golangci-lint` or a `make` target
  that runs them, starts with `EXEC_PLAN_JOURNAL=JOURNAL . SCRIPTS/cache.sh && `, as in
  `EXEC_PLAN_JOURNAL=JOURNAL . SCRIPTS/cache.sh && make lint`. `cache.sh` sets the Go build
  cache and the lint cache to the run's own for that one shell call. So the next call sources
  `cache.sh` again
- preflight of this run:
PREFLIGHT

RETRY

### Read first

1. The plan: `## Goal`; `## Owner Sign-off`; `## Decisions`; `## Execution`, its Shared files
   table above all; the `Result:`, `Decision:`, `Repo:` and `After:` of every task of the lanes
   list. The merge order of the lanes list follows the table: the task the table names as
   second comes after the one the table names as first.
2. The journal `JOURNAL/progress.md`: the lines of every lane of the lanes list, their
   `[decision]` and `[deviation]` lines in particular. A `[deviation]` that names
   a file outside the lane's `Where:` is where a conflict between two lanes comes from. The
   two lines say what each meant.
3. The project rules of each repository of the repositories list, the sections `Gates`,
   `Environment` and `Records`. `Environment` also says how one repository builds against the
   run branch of another. Then the root `CLAUDE.md` of each run worktree: its rules, where it
   says who owns a value, and its commit rules.
   Then the `CLAUDE.md` of each surface a conflict or a red check lands in, and the skills
   `## Execution` lists for that surface. Load those skills with the Skill tool before your
   first edit. Prose follows the prose rules of the project's `CLAUDE.md`, where it states them.

### Merge

Before you start, `git status --porcelain` prints nothing in every run worktree of the
repositories list and in HOME. Anything it prints is a stop:
`[blocker] integration WAVE: dirty tree: <repo>: <paths>`.

On the second attempt at this wave, the first attempt may have left work behind. What the
first attempt committed stays. You drop what it left uncommitted in those worktrees before the
check above: a squash it did not commit, a fix attempt, a regeneration, marks carried into PLAN
without their commit. To drop that work, run `git reset --hard HEAD` and then `git clean -fd`
in each of those worktrees. The steps below redo that work from what is committed. Ignored
files stay, the ones the preflight linked among them.

Run the steps below for each lane of the lanes list, in order, in the run worktree of its
repository. <tip> is the tip the repositories list gives that repository. A lane the first
attempt already merged is not merged again. Its commit is on the run branch, and every subject
`git log --format=%s <tip>..<lane branch>` prints appears verbatim in
`git log --format=%B <tip>..HEAD`, the body step 4 gave its commit. Skip the steps of that
lane. Carry its marks into PLAN when PLAN does not hold them yet. In a tracked plan whose HOME
is another run worktree, commit those marks from HOME as step 4 says. A squash of a merged lane
brings a false conflict or nothing.

1. Note the lane's commits, `git log --oneline <tip>..<lane branch>`: they become the body of
   its commit message below.
2. `git merge --squash <lane branch>`. This is one three-way merge. You resolve its conflicts
   once, here. You make no merge commit: on the next start, `base.sh` refuses a merge commit
   between the repository's base and `HEAD`. The finalize regroups the range anyway.
3. Resolve every conflict in the working tree:
   - a generated file, the output of a generator the `Gates` section names: take either side,
     the generators rewrite it below;
   - lines a gate command writes into a hand-written file, such as the coverage lines a
     record carries, by the `Gates` section: take either side, the command rewrites them below;
   - a hand-written file: read both tasks' `Result:` and `Decision:` and both lanes' journal
     lines for that file. Then write the version under which both results hold, where an
     integrator usually resolves only the mechanical conflicts. Log
     `[decision] integration WAVE: <repo>: <file>: <what you kept of each side>, because <why>`. A
     conflict under which both results cannot hold is a stop:
     `[blocker] integration WAVE: <repo>: <file>: <the two intents in plain words>`. You leave the
     tree in its conflicted state for the owner, and you merge nothing after it.
4. Regenerate before the commit when the merge can have left a generated file stale: step 3
   took a side of a conflict, or an earlier lane of this merge also changed what a generator
   reads, a contract or a file a gate command reads to write its lines. Then run the
   generators and those gate commands, as the `Gates` section names them: the pre-commit hooks
   build and check what is staged. Otherwise skip them: the lane ran the generators of what it
   changed, and its output is current. Then `git restore --staged .`, so
   the index holds nothing: `commit.sh` refuses an index that holds a path it is not given.
   Then carry the lane's marks into PLAN, as "Carry the marks" below says. Then commit the
   lane as one commit:
   `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <paths...>`. Name every path
   `git -c core.quotepath=false status --porcelain` lists, each as one argument. A path git
   still prints in double quotes, one with a space, is passed with those quotes, which the
   shell reads as one word. The tree was clean
   before the squash, so every path listed is this lane's merge, its regeneration, or PLAN
   when HOME is this run worktree. A path the lane deleted is named like
   any other: it is gone from the tree and is staged as its removal. The message is
   the task's title in the project's commit form, `type(scope): <the task's title>` unless
   `SCRIPTS/../references/commit.md` finds another. The body of the message is the lane's
   commit subjects, one per line. The message is not a `chore: integrate wave` message. Pass
   the message as one argument with real newlines inside the quotes, never through
   `git commit -F -`. End it with the attribution line your session's instructions give, when
   they give one. A hook that fails names its cause: fix the cause and commit again. In a
   tracked plan whose HOME is another run worktree, commit PLAN from HOME right after, alone:
   `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "docs(plans): mark task N of the SLUG plan"
   <PLAN relative to HOME>`, the message in the project's commit form. In an untracked plan the
   edit in place is all: nothing commits it. So a merged lane has its ticks in PLAN before the
   next lane starts. A stop later in the wave never leaves a lane merged and unticked.

A lane never edits PLAN, so no lane's merge touches it. A lane of the stopped list is not
merged and not read for its diff: only its marks reach PLAN, as "Carry the marks" below says.

A lane of the review list holds the fixes of a review of an earlier wave in one repository. It
is merged first, into the run worktree of that repository, by the same four steps. It closes
no task and ticks nothing. Its message is `fix(<scope>): <what the
fixes make true>`, with its commit subjects as the body. After the commit, log the review lane
as `review wave N: merged, <repo>, <lane tip>`. The lane tip is `git rev-parse <lane branch>`.
A review lane whose repository and lane tip a `merged` line of the journal already names is
skipped, whatever wave that line names. A lane cut anew holds a new tip. A conflict with a lane
of the lanes list is resolved like any other: the fix holds and the task's `Result:` holds.
The lanes list may be `none`, when only review lanes are left after the last wave. Steps 5
and 6 of the checks below then run over what the review lanes touched.

### Regenerate and check

After the last lane, run the checks below in every repository of the repositories list, from
its run worktree. Run each check in the foreground, never in the background, to its end, and
read the output. A repository whose build reads another repository of the run, as its
`Environment` section says, is built and linted here too when that other repository changed in
this wave. A repository that another builds against comes first in the order. A check prints
its exit code in the same call, `<command>; echo "exit=$?"`, and never through a pipe, whose
exit code is the pipe's last command. A check is never run a second time to learn how it
ended. A surface whose packages
were never installed here gets what the `Environment` section asks a fresh checkout to install
first. The commands are the ones the `Gates` section names:

1. the generators, then their drift check, when step 4 regenerated for any lane or a fix
   of yours changed what a generator reads
2. the docs check, with the steps the `Gates` section runs before it, on the same condition as
   step 1. Otherwise a lane that changed a document ran the docs check itself. The docs hook,
   where the project has one, ran the docs check on that lane's commit and on the commit that
   carried PLAN
3. the build of the whole tree
4. the lint of the whole tree
5. the tests where the lanes of the wave met. A surface is a component with tests of its own.
   A surface is met when two or more lanes of the lanes list and the review list changed files
   in it, generated files included. A surface is also met when step 3 resolved a conflict in
   it, or when a fix of yours changed it.
   A surface only one lane changed is not met: that lane ran its tests on the code the merge
   brought in unchanged. For each met surface, run its tests narrowed to the files
   `git diff --name-only <tip>..HEAD` lists in it: the packages, the modules or the specs that
   hold or relate to a changed file, with the suites the `Gates` section ties to them.

   Log the surfaces that were not met in `- validation:`, each with the lane whose tests
   stand for it.
6. the search commands of every `acceptance:` checkbox of every task of the lanes list, the `rg` and the
   inventory, run as written on this tree. A search that fails here passed in its lane, so the
   merge broke it. Fix the tree, never the acceptance.

The build and the lint run every component, whatever the wave touched. The reasons: a lane
breaks a neighbour it never opened, two lanes that each passed can fail together, and the
next wave's lanes start from this tip. The tests run only where the lanes met. A lane's own
tests passed on the code the merge brought in. What only the tests of the whole tree catch,
the whole-tree check after the last wave catches.

### Fix

- A red check is fixed, not handed back as an integrator usually does. The list runs again
  from the check that went red, until it is green. Fix the cause, never the check. These are
  forbidden: `--no-verify`, a variable that turns the hooks off (`LEFTHOOK=0`, `HUSKY=0`), a
  skipped or deleted test, and an edit to a hook or a lint config so that the check passes.
- A test that fails once and passes on a rerun with nothing changed is a flake. Rerun the test
  once. When it passes, log it as `[decision]` with the test's name, and go on. A test red
  twice is not a flake.
- A failure the wave did not cause is not yours to fix. A check is not the wave's when the same
  check, run alone, is red at <tip> as well, the tip of that repository. To tell, run only the
  red test at <tip>, in a scratch worktree beside the repository's run worktree. Create the
  scratch worktree with `git worktree add --detach "$(dirname <run worktree>)/SLUG-tip" <tip>`
  from that run worktree, and remove it afterwards. Do not create it under `/private/tmp`:
  Docker does not share that directory, so a stand raised from there mounts nothing. When the
  test is red there as well, leave it, log
  `[deviation] integration WAVE: <repo>: <check> red at the wave's tip as well: <test or cause>`, and
  go on. Such a failure does not stop the run: the run report lists it as open.
- A check red for a reason outside the tree: Docker gone, the disk full, a stand that does
  not come up. Such a check is neither fixed in the tree nor the owner's judgement. A cause you
  removed yourself, with the checks green after it, is a `[decision]`. A cause you cannot
  remove: log `[blocker] environment integration WAVE: <reason>` and stop. What on the host is
  not the run's is not yours to clear.
- A fix that needs a choice the plan does not make, or would change a Decision, a `Result:` or
  what the owner reserves: change nothing for it and log
  `[owner] integration WAVE: <the question in plain words, the options and what each costs>`.
- Everything else is the run's own: what the tree already does, you repeat; the fix is the
  simplest one; a value goes into the artifact the project's rules name as its owner.
- PLAN gets no tick and no note from you beyond the marks "Carry the marks" brings.

Commit each fix with `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <path>...` from
the run worktree of its repository, naming every path you changed. Use
`fix(<scope>): …` for code, `docs` for a document, `test` for a test. Regenerated output goes
in its own commit, `chore(<scope>): regenerate …`. The staging and message rules are in
`SCRIPTS/../references/commit.md`: read it before your first commit.

### Carry the marks

Every lane writes its marks into its own progress file and never into PLAN. You carry the
marks into PLAN.
The checkbox lines of the lane's task in PLAN take the state the lane's progress file holds,
line for line. A `[x]` in the progress file is `[x]` in PLAN. A ` ⚠️ <reason>` in the progress
file is on the same line in PLAN. A mark the progress file no longer has is gone from PLAN too.
The result is not a union of the two. Nothing else in PLAN changes: no other task, no heading,
no note.

- A lane of the lanes list is carried in step 4 of its merge, before its commit: its progress
  file has every checkbox `[x]`.
- A lane of the stopped list is carried once every check is green, as its progress file
  stands, its code not merged. The owner reads its `⚠️` in PLAN and answers there. In a tracked
  plan, commit PLAN from HOME, alone, `docs(plans): mark the stopped tasks of the SLUG plan` in
  the project's commit form. In an untracked plan the edit in place is all.
- A wave that stopped before its last lane has carried the lanes it merged. The lanes the wave
  did not reach and the lanes of the stopped list keep their marks in their progress files.

### Prove

`git status --porcelain` prints nothing in every run worktree of the repositories list and in
HOME. Every task of the lanes list has every checkbox `[x]` in PLAN. Every lane of the stopped
list has its marks in PLAN. Every search of step 6 passed. Then log the wave as integrated.

### Journal

Only through `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh '<line>'`, one call per line, never
a redirect into the file. The line goes in single quotes. A single quote inside the line is
written as `'\''`. In double quotes, a backtick or a `$(…)` in the line runs as a command. The
lines:

- `review wave N: merged, <repo>, <lane tip>`, right after the commit of each review lane
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

The bracketed prefixes are exact. The run collects them verbatim for the owner. Log only what
happened. A wave that stopped before its last lane logs
`wave WAVE: stopped after <task>` in place of `integrated`, so the run knows how far the merge
got.

### Report

Finish with: each lane and its commit's SHA and subject; every conflict and its resolution;
each check and its result, trimmed; every red you fixed and its cause; every `[deviation]`,
`[owner]` and `[blocker]` line verbatim; any error you hit and how it ended. Keep the report
under about three kilobytes: a longer report is cut on its way back, and the journal holds the
rest.

ONE wave per run. After the commits and the journal, STOP.
