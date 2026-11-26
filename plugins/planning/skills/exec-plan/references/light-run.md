# A light run

A plan whose `## Execution` carries `- **Mode.** light — <reason>` is small enough for one
executor, by the conditions [`form.md`](../../make-plan/references/form.md) gives under Mode. The
run skips what only parallel lanes and a large branch need. It keeps the branch, the gates
of what the work touched, the review the `Review` section names for a light run, the regroup
and the owner's revdiff. A light plan has one repository: the home one of a tracked plan, the
one its tasks name otherwise. Everything in [`SKILL.md`](../SKILL.md) holds except where this
file changes it.

- **Step 1.** A light run has no peer, and the peer question is not asked. A peer the owner
  named after the path is not started, and the message that asks for the go says so. A light
  plan whose repositories are more than one is a stop before anything else: the plan goes back
  through `/planning:make-plan <plan>`, which writes it as a full plan. The anchors run as
  for any plan. For every shape `## Contracts and Data` names, the search of
  [`make-plan`](../../make-plan/SKILL.md) Step 2 for its readers and writers runs again, over the
  places the `Consumers` section names. One the section does not name is a false premise, and
  the plan goes back through `/planning:make-plan <plan>`.
  No waves are printed: the tasks run one after another, in the order their `After:` lines
  allow. The message that asks for the go names the mode with the plan's reason. It says what
  the run skips: the lanes and the integrator, the whole-tree tests of components the branch
  does not touch, the rounds of a full run. The message also names the review the run will make
  instead, below. The go is the same one go; the light mode gets no go of its own.
- **Step 2.** The same preflight, for the run worktree: what the `Environment` section asks a
  fresh checkout to install for each surface a task's `Where:` names.
- **Step 3.** No lane worktree and no integrator. Log `light run: one executor, <the plan's
  reason>`, then `wave N: started, tasks <numbers>`. `N` is one past the highest `wave N` in
  the journal, and the numbers are those of the open tasks alone, comma-separated, the form the
  status page reads.
  One subagent (the Agent tool, `general-purpose`, `name` `<slug>-light`, in the background
  like a lane, under the same rules for a lane that goes idle on a command) runs the prompt of
  [`task.md`](task.md). The prompt gets `CHECKOUT` the run worktree,
  `BRANCH` the run's branch, `TASK` every open task in the order their `After:` lines allow,
  file order breaking a tie, `PROGRESS` the plan itself, `PLAN`, and `WAVE` the line
  `light run`. No progress file is made. The executor closes the tasks one after another and
  ticks the plan itself. In a tracked plan, the plan is in the executor's checkout and goes
  into each task's commit. In an untracked plan, the plan is ticked in place and never
  committed. When every task is closed, log `wave N: integrated, light run, no integrator`.
  The status page ends a wave only on that line. Without that line, the wave reads as running
  through the check and the review. What came back is read as a lane's is: the retry once, the
  resume once on `[blocker] environment`, and a stop with the report of Step 4 on an `[owner]`
  line or a `⚠️`. The executor's `[owner] light run outgrown: …` line is such a stop. That line
  means the executor found a reader or writer the plan does not name, a behaviour the plan does
  not choose, or work one executor cannot close. The run does not switch to the full path by
  itself; the owner decides.
- **The check.** The whole-tree step runs [`check.md`](check.md) with
  `SCOPE` set to `light`. That scope covers the generators' drift check, the docs check, the
  build and the lint of the whole tree, and the tests only of the components the branch
  touched. Log `whole tree: <repo>: started, light`.
- **Step 5.** At most two rounds, both on the light profile and lens set the `Review` section
  names. By default these are `--profile claude-only --lenses bugs,impl,tests`, the lens set
  replacing the profile's roster. The first is
  `NN-initial`. Clean: the minor pass when it holds minors, then Step 6. Not clean: the fixer,
  then one more round, `NN-after-fix`. Its `scope.md` names the critical and major findings of
  the first round and the fix commits. That `scope.md` asks whether each fix closes its finding
  and what it broke around it. That round is the last. Clean: Step 6, its minors open in the run report.
  A critical or a major in it: stop with the report of Step 4. A fixer that committed nothing
  goes to Step 6 with no round after it, as in a full run.
- **Step 6.** The finalize, the clean-up and the revdiff as written. The run report's
  `tasks:` line says `light run`, and its `whole tree:` line names the light scope.
- **A continuation** of a light run: [`continuation.md`](continuation.md), its section
  "A light run".
