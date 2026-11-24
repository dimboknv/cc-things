---
name: exec-plan
description: >
  Use when a plan `/planning:make-plan` wrote is to be run, or a run of one continued: start a
  branch in every repository the plan names, run every task whose `After:` is met as a lane in
  its own worktree, integrate each wave through one subagent, check the whole tree of each
  repository once after the last wave, then review each branch, regroup its history and close
  the plan. A plan marked light runs with one executor, a
  narrower check and one review agent. With `peer` after the path, a second agent in the
  split pane reads the plan before the go and every wave after it is integrated. Not for a
  mechanical edit one session makes in place.
user-invocable: true
disable-model-invocation: true
---

# Run a plan

This skill takes a plan in the form of
[`make-plan/references/form.md`](../make-plan/references/form.md) to a closed plan: a branch in
every repository the plan names, the tasks in waves of parallel lanes, one journal, then the
review rounds, the regroup of the history, the move to the closed-plans directory and the
owner's revdiff. The argument is the path of the plan. A path that does not exist is the
first stop, and a plan that already sits in the closed-plans directory is such a path.

A run may have a peer: a second agent in the split pane of the same agterm session, which
reads the plan before the go, reads every wave after it is integrated while the next wave
runs, and keeps the notes the later lanes get. It fixes nothing: a subagent of this session
does. A run with a peer is a trial, and its report says what the peer found. Who the peer is
the owner says after the path, `peer` or `peer claude`, `peer codex`, `no peer`, or answers
when Step 1 asks. Before the rest of Step 1 of a run with a peer, and of the continuation of a
run whose journal holds `review/`, read [`references/with-peer.md`](references/with-peer.md)
with the Read tool: it adds to the steps below and changes none of them. A run without a peer
is plain and does not read that file.

A wave is every open task whose `After:` tasks are closed. Each task of a wave runs as a lane, a
subagent in its own worktree on its own branch in its task's repository, and the lanes of a
wave run at the same time. When every lane of the wave has ended, one integrator subagent
merges the lanes that ticked every checkbox of their task into the run's branch of their
repository, regenerates
what is generated, builds and lints each repository the wave touched, runs the tests where two
lanes of the wave met, and carries the lanes' ticks into the plan. The next wave starts from
those tips. The tests of the whole tree run once, in the whole-tree check after the last wave. A plan with no `After:` line
runs every task in the first wave. A plan whose `## Execution` carries the Mode line
`light` runs as "A light run" below says.

## The project rules

Load them once, at the start of Step 1, before the question about the peer:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh
```

It prints the project's rules file, its path on the first line as `<!-- rules: <path> -->`, or
nothing. The sections, and the default each takes when the file is absent or leaves it out, are
[`../../references/rules.md`](../../references/rules.md). The script looks from the checkout it
runs in and from each directory above it, so in a plan of several repositories run it once more
from the main checkout of each repository: when one finds another file, the `Trunk`, `Gates`
and `Environment` of that repository come from its own file. This skill reads:

- `Plans`: the plans directory, the closed-plans directory a run moves the plan into, the file
  name the slug comes from;
- `Trunk`: the branch a run is cut from and its pull request lands on. This file calls it the
  trunk;
- `Gates`: the gate of each surface, the generators and their drift check, and the whole-tree
  checks;
- `Environment`: what a fresh worktree needs per surface, the caches, the stands a task's
  `Needs:` names, how a stand is seen up and how the run takes one down, and how one repository
  builds against the unpublished run branch of another;
- `Records`: the records that bind a change and the ones that only explain it, what a lane does
  with a decision record its task goes against, and the judgements only the owner makes;
- `Consumers`: where the light run searches for the readers and writers of a shape;
- `Review`: the revmux profiles of the branch rounds and the lens set of a light run, and the
  rules a review holds the branch to.

A heading the schema does not list is an addition to this skill's rules too. The project's
`CLAUDE.md` files hold the rest a subagent reads: the conventions of each surface, the prose
rules and the commit rules.

## The plugin's files in a subagent's prompt

The plugin root is `${CLAUDE_PLUGIN_ROOT}`, which Claude Code substitutes in this file only. A
subagent, the peer and a script get no plugin variables, so every prompt under `references/`
names the plugin's files through placeholders, and the lead substitutes absolute paths when it
builds the prompt: `SCRIPTS` is `${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts` and `RULES`
is `${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh`, each expanded to the absolute path. The same holds
for a command this file shows as `scripts/<name>`: it runs as
`${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts/<name>`. A subagent runs `bash RULES` from its
checkout and reads the sections its prompt names.

Every script reads the run's journal from the variable `EXEC_PLAN_JOURNAL`, the journal's
absolute path, and refuses with one line when it is unset or not absolute. No script finds the
journal by itself. This session sets the variable for every call,
`EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh "<line>"`, and every prompt under
`references/` gets the path as the placeholder `JOURNAL` and sets it the same way. A placeholder
is replaced only where it stands as a whole word: `EXEC_PLAN_JOURNAL` is the variable's name,
not `PLAN` or `JOURNAL`, and stays as written.

Three operations are scripts under `scripts/`, and this file never spells out their git
commands:

- `scripts/commit.sh <message> <path>...` stages the named paths in the checkout it runs in,
  refuses an index that holds anything else, and commits without a pathspec, so the hooks run
  on the real index and a file a pre-commit hook stages lands in the commit. A tracked path gone
  from the tree is staged as its removal, so a file is deleted with `rm` and moved with `mv`,
  never `git rm` or `git mv`: those take the path out of the index before the script can name
  it, and it fails;
- `scripts/base.sh <repo> <trunk>`, run inside that repository's run worktree, computes the
  base commit of the repository and records it as `base.<repo>` in the journal, or checks the
  one recorded;
- `scripts/progress.sh <line>` appends one timestamped line to the journal.

Each exits non-zero with one line of reason on a refusal. A refusal is a stop: the line goes
into the report, and nothing is tried around it.

A fourth file there is sourced, not run, and it matters when the project builds Go.
`. scripts/cache.sh` sets `GOCACHE` and `GOLANGCI_LINT_CACHE` to the run's own caches for the
commands that follow in the same shell call, and the next call sources it again. Every command
of a run that builds, tests or lints Go starts with it,
`EXEC_PLAN_JOURNAL=<journal> . scripts/cache.sh && make lint`, in a subagent and in this
session alike. `commit.sh` sources it itself, for the pre-commit hooks, so it gets the variable
too. A project with no Go never runs a command it covers, and sourcing it there changes
nothing.

`EXEC_PLAN_JOURNAL=<journal> scripts/audit.py` reads the run back. Claude Code keeps the
transcript of every subagent, and the script lists the shell commands in them that break a rule
of the prompts: Go built outside the run's caches, a commit made around `commit.sh`, a bypassed
hook. A finding is a place to look, not a verdict, and it changes nothing in the run: it tells
the owner which line of a prompt an agent did not follow.

`EXEC_PLAN_JOURNAL=<journal> scripts/status.py [--watch] [--open]` draws the run as one page,
`<journal>/status.html`: the
phase; this session and the peer of a run that has one, with their turns, their tokens and
the mail between them; every wave with its tasks and its integrator under it, each with its
time, model, context, turns and tokens in and out; the waves still ahead, as the `After` chains
of the open tasks allow them at the earliest; the whole-tree check with the gates it
ran; the review rounds; and the stops nobody has answered. It reads everything from the
journal: the plan through `plan` and the line `finalize: plan closed, <path>`, the repositories
through `repos`, the ticks of a running lane from its progress file, and the ticks of a closed
task from the plan. The times, the turns, the tokens
and the steps come from the transcripts Claude Code keeps: one of every subagent, one of this
session, whose id the script records in `<journal>/lead`, and one of the peer. `progress.sh` runs the script after a line
that changes what the page shows, so nobody calls it by hand. In an agterm session the line
that starts or continues a run opens the page as a companion row under the session and
starts one watcher for the run, `status.py --watch`, which redraws every ten seconds, so the
tokens and the checkboxes of a working lane move between journal lines. The watcher ends when
the run stops or closes, and when its page is gone. The open page pulls `status.js`, written
beside it, every five seconds and replaces its content in place, so it is never reloaded and
keeps the reader's scroll position. The page is a view of the journal, the plan, the lanes'
progress files and the transcripts: the run reads nothing from it, and a page that cannot be
drawn fails nothing.

The prompts of the subagents are under `references/`: [`task.md`](references/task.md) for a
lane, [`integrate.md`](references/integrate.md) for the integrator of a wave,
[`check.md`](references/check.md) for the whole tree, [`fixer.md`](references/fixer.md) for a
review round and [`finalize.md`](references/finalize.md) for the close. Each of them sends its
subagent to [`commit.md`](references/commit.md) for how a commit is made.
[`peer.md`](references/peer.md) is the brief of the peer, which its launcher hands it.

## Names and state

- The slug is the plan's file name without its date and extension:
  `20260930-make-plan-and-exec-plan.md` gives `make-plan-and-exec-plan`.
- **The repositories.** A task names its repository with the line `Repo: <dir>` right after
  `Where:`, the repository's directory relative to the session's working directory, and its
  `Where:` paths are relative to that repository. A task without the line belongs to the home
  repository, the one whose checkout holds the plan file. A plan outside every git checkout has
  no home repository, and each of its tasks names its own. `<repo>` below is the repository's
  directory name. The repositories of the plan are the ones its tasks name and, for a tracked
  plan, the home repository, which holds the plan's commits. A plan of several repositories runs
  in a session whose working directory holds all of them.
- **The plan's mode.** The place of the plan decides it, by the same test make-plan uses: a plan
  in a repository's work tree that git does not ignore (`git -C <the plan's directory>
  check-ignore -q <plan>` exits 1) is tracked. A tracked plan must be committed before a run
  starts, because the run's worktree is cut from a commit: when
  `git -C <the plan's directory> ls-files --error-unmatch <plan>` fails, Step 1 stops and tells
  the owner to commit the plan, which make-plan's menu does. A tracked plan is
  read, ticked and closed in the copy in the home repository's run worktree, and every change to
  it is a commit there through `commit.sh`. Any other plan, outside git or in a directory git
  ignores, is untracked: it is read, ticked and closed at its own path, and nothing of it is
  ever committed. "The plan" below is that one file, and its absolute path is `PLAN` in every
  prompt. Nobody edits the copy of a tracked plan in a main checkout.
- **The journal** is one directory per run, `<journal>` below. For a tracked plan it is
  `.exec-plan/<slug>/` in the main checkout of the home repository, the first entry of
  `git worktree list`. For an untracked plan it is `.exec-plan/<slug>/` in the plan's
  directory. It is not a run block committed in the plan. It holds:
  - `progress.md`, the log;
  - `plan`, one line: the plan's absolute path as the run reads it, the copy in the home
    repository's run worktree or the untracked file;
  - `repos`, one line per repository of the plan:
    `<repo> <main checkout> <run worktree> <branch>`, absolute paths, written in Step 1 after
    the branches are cut;
  - `base.<repo>`, the base commit of each repository, written by `base.sh`;
  - `lanes/task-<N>.md`, a lane's progress file: the plan's `### Task N:` section, which this
    session copies there before the lane starts. The lane ticks `[x]` and appends
    ` ⚠️ <reason>` there and never edits the plan;
  - `lead`, `status.html` and `status.js`, the status page's own files, and `review/` in a run
    with a peer.

  The project's `.gitignore` lists `.exec-plan/` and `.claude/worktrees/`; where it does not,
  both show as untracked in the main checkout, and nothing of the run stages them.
- **Per repository.** The run's branch, `<branch>` below, has one name in every repository of
  the plan. It is named as the `Trunk` section says; by default it is `<type>/<slug>`, `<type>`
  the commit type of the plan's Goal as the go confirms it. Its checkout, the run worktree, is
  `.claude/worktrees/<slug>` in the repository's main checkout. The trunk is never run on, and
  neither is a branch another checkout stands on. Each repository has its own trunk, its own
  `base.<repo>`, its own lane worktrees and its own lint caches.
- The run builds into its own caches, `<journal>/cache/`, and the `Environment`
  section may name more of them there. For Go: `go-build/` is one Go build
  cache for every checkout of the run, in every repository, so a dependency is compiled once.
  `lint/<repo>/<the checkout's directory name>/` is a golangci-lint cache per checkout, `<repo>`
  the directory name of the repository's main checkout: that cache
  keeps the absolute path of every file it read, and an entry of a worktree that is gone comes
  back as an issue no exclusion matches. Nobody else builds into them, so the run deletes them
  without asking who is building: a cold build costs the next wave one compile, which is
  cheaper than a cache that grows by a copy of the tree per lane. The Go build cache goes after
  every wave, a lane's lint cache with the lane, and the rest when the run ends. A stop leaves
  what is there for the continuation. Downloaded modules stay in the shared `GOMODCACHE`.
- A lane is named after its task: the branch `<slug>-task-<N>`, the worktree
  `.claude/worktrees/<slug>-task-<N>` in the main checkout of its task's repository, the
  progress file `<journal>/lanes/task-<N>.md`, and the subagent's name the same string as the
  branch, cut to its last 64 characters when it is longer: the Agent tool takes no longer name.
  The lane's branch is cut from the tip of its repository's run branch at the start of its wave.
  A lane's branch is local and removed after its wave, so it keeps the bare slug.
- The state of a run is the plan's checkboxes, the lanes' progress files, the `base.<repo>` of
  each repository, and the lane worktrees that exist, nothing more: no phase marker, no lock, no
  dirty-tree check. A task is closed when every checkbox of its section is `[x]` in the plan,
  which happens only after its lane was integrated, or, in a light run, once the executor has
  ticked it there. A lane worktree that exists for an open task is a lane that stopped: its
  branch holds what it committed, and its progress file what it ticked.
- A `base.<repo>` file in the journal is also what says a run exists: Step 1 continues a run
  when the journal holds one and starts one when it holds none. A second `/planning:exec-plan`
  on the same plan goes the way the first went: the wave loop from the ready set, then the
  whole-tree check, then the review, which goes on from the rounds each repository's task
  already holds and never starts over (Step 5). With every task already closed it goes straight
  to the whole-tree check.
- The trunk of a repository is the branch the `Trunk` section names, resolved once per
  repository in Step 1 and named `<trunk>` below. With no `Trunk` section it is the branch
  `origin/HEAD` of that repository points at, else `main`, else `master`.
- Every tick and every `⚠️` of a lane is written into its progress file. The integrator of the
  wave carries them into the plan: the checkbox lines of each lane's task take the state its
  progress file holds, for a lane it merged and for a lane that stopped alike, while only the
  merged lanes' code reaches the run's branches. In a tracked plan that is a commit in the home
  repository's run worktree; in an untracked plan an edit in place. In a light run, which has
  no integrator, the executor ticks the plan itself. The owner's answer to a stop goes where
  Step 4 says. Nobody else edits the plan.
- The run is one session. Between the go of Step 1 and a report it asks the owner nothing. It
  ends on the run report, or on the stop report of Step 4 when it meets an owner's judgement or
  an environment it cannot repair. A stop is an ordinary end of a session:
  `/planning:exec-plan <plan>` continues the run.
- No Agent call of the run names a `model`: every subagent runs on the model of this session.

## A light run

A plan whose `## Execution` carries `- **Mode.** light — <reason>` is small enough for one
executor, by the conditions [`form.md`](../make-plan/references/form.md) gives under Mode. The
run skips what only parallel lanes and a large branch need, and keeps the branch, the gates
of what the work touched, the review the `Review` section names for a light run, the regroup
and the owner's revdiff. A light plan has one repository: the home one of a tracked plan, the
one its tasks name otherwise. Every step below holds except where this section changes it.

- **Step 1.** A light run has no peer, and the peer question is not asked. A peer the owner
  named after the path is not started, and the message that asks for the go says so. A light
  plan whose repositories are more than one is a stop before anything else: the plan goes back
  through `/planning:make-plan <plan>`, which writes it as a full plan. The anchors run as
  for any plan. For every shape `## Contracts and Data` names, the search of
  [`make-plan`](../make-plan/SKILL.md) Step 2 for its readers and writers runs again, over the
  places the `Consumers` section names; one the
  section does not name is a false premise, and the plan goes back through `/planning:make-plan <plan>`.
  No waves are printed: the tasks run one after another, in the order their `After:` lines
  allow. The message that asks
  for the go names the mode with the plan's reason, and says what the run skips: the lanes and
  the integrator, the whole-tree tests of components the branch does not touch, the
  rounds of a full run. It names the review the run will make instead, below. The go is the
  same one go; the light mode gets no go of its own.
- **Step 2.** The same preflight, for the run worktree: what the `Environment` section asks a
  fresh checkout to install for each surface a task's `Where:` names.
- **Step 3.** No lane worktree and no integrator. Log `light run: one executor, <the plan's
  reason>`, then `wave N: started, tasks <list>`, `N` one past the highest `wave N` in the
  journal, the form the status page reads.
  One subagent (the Agent tool, `general-purpose`, `name` `<slug>-light`, in the background
  like a lane, under the same rules for a lane that goes idle on a command) runs the prompt of
  [`references/task.md`](references/task.md) with `CHECKOUT` the run worktree, `BRANCH` the
  run's branch, `TASK` every open task in the order their `After:` lines allow, file order
  breaking a tie, `PROGRESS` the plan itself, `PLAN`, and `WAVE` the line `light run`. No
  progress file is made. It closes the tasks one after another and ticks the plan itself: in a
  tracked plan the plan is in its checkout and goes into each task's commit; in an untracked
  plan it is ticked in place and never committed. When every task is closed, log
  `wave N: integrated, light run, no integrator`: the status page ends a wave only on that
  line, and without it the wave reads as running through the check and the review. What came
  back is read as a lane's is: the retry once, the resume once on `[blocker] environment`, and
  a stop with the report of Step 4 on an `[owner]` line or a `⚠️`. The executor's
  `[owner] light run outgrown: …` line is such a stop: it found a reader or writer the plan
  does not name, a behaviour the plan does not choose, or work one executor cannot close. The
  run does not switch to the full path by itself; the owner decides.
- **The check.** The whole-tree step runs [`references/check.md`](references/check.md) with
  `SCOPE` set to `light`: the generators' drift check, the docs check, the build and the lint
  of the whole tree, and the tests only of the components the branch touched. Log
  `whole tree: <repo>: started, light`.
- **Step 5.** At most two rounds, both on the light profile and lens set the `Review` section
  names, by default `--profile claude-only --lenses bugs,impl,tests`, the lens set replacing
  the profile's roster. The first is
  `NN-initial`. Clean: the minor pass when it holds minors, then Step 6. Not clean: the fixer,
  then one more round, `NN-after-fix`, whose `scope.md` names the critical and major findings
  of the first and the fix commits, and asks whether each fix closes its finding and what it
  broke around it. That round is the last. Clean: Step 6, its minors open in the run report.
  A critical or a major in it: stop with the report of Step 4. A fixer that committed nothing
  goes to Step 6 with no round after it, as in a full run.
- **Step 6.** The finalize, the clean-up and the revdiff as written. The run report's
  `tasks:` line says `light run`, and its `whole tree:` line names the light scope.
- **A continuation** reads the same state: `base.<repo>` and the checkboxes. A `⚠️` the
  executor left is in the plan itself, not in a lane's progress file, so it does not take its
  task out of the ready set here: the executor runs again over every task with an open `[ ]`, a marked one
  included, and removes the mark when it closes the item. Then the check. Then the review,
  from the rounds the task holds: with one round, the fixer on its findings, then
  `NN-after-fix` on the lens set as above; with two, the fixer on the second round's findings
  and no round after it, and what it leaves goes into `open:` of the run report. Never a
  round on the profiles of a full run and never a third.

## Step 1: where the run happens

The only step with questions. After the question about the peer its order is the point: the
premises are rechecked in every repository, the environment is checked and the go is given
before a branch, a worktree or a base exists in any of them, so a plan that fails the recheck
goes back to `/planning:make-plan` with nothing to remove, and what the run would stop on an
hour later is said before it starts.

**The journal.** Find the plan's mode and the journal's place as "Names and state" says: a
tracked plan's journal is in the main checkout of its home repository, an untracked plan's in
the plan's directory. Every script call of the run sets `EXEC_PLAN_JOURNAL` to that absolute
path.

**Continuation.** The run is continuing when the journal holds a `base.<repo>` file. Nothing
else says so: a branch `<branch>` or a worktree without one is a first run, a checkout the
owner made by hand included. On a continuation the repositories are the lines of `repos`, and
the checkout that runs in each is its run worktree; a run worktree that is gone gets it back by
hand, `git -C <main checkout> worktree add .claude/worktrees/<slug> <branch>`, with the branch
the line names. The one check of a branch is the base check below: a checkout that does not
stand on the recorded base fails there, with the line of `base.sh` as the reason. Go to the
base check; the premises were rechecked and the go given when the run started, and nothing is
asked.

On a continuation, list the lane worktrees under `.claude/worktrees/<slug>-task-*` in the main
checkout of every repository of `repos`. One whose task is closed in the plan was integrated
before a stop: remove it and its branch. One whose task is open is a lane that stopped, and
Step 3 resumes it.

**The peer.** The first question of a new run, asked before anything else and alone, unless
the request already answers it or the session is not in agterm, where no peer can run. Three
answers, each with what it costs:

- no peer: the run as this file describes it. A bare «ок» means this;
- Claude Code: a second session of the same account in the split pane. It reads the plan and
  every wave, and its turns are paid like this session's;
- Codex: the same work by another model, which catches what two Claudes agree on by habit.
  The Claude Code hooks and skills of the project do not bind it, and the status page does not
  count its tokens.

It is a closed question, asked as
[`../../references/questions.md`](../../references/questions.md) says, no peer first; the free
line takes the owner's own words, a model for the Claude peer among them.

A continuation asks nothing: the journal says whether the run has a peer.

**The repositories.** Read every task's `Repo:` line and list the repositories of the plan as
"Names and state" defines them. The home repository is found from the plan's path: the
repository whose checkout holds the plan file, its main checkout the first entry of its
`git worktree list`. A plan with no `Repo:` line has that one repository, and the session runs
wherever it runs today. A repository a `Repo:` line names must be the main checkout of a git
repository at `<the session's working directory>/<repo>`. One that is not there is a stop that
names it: the session runs from a directory that holds every repository of the plan, and the
owner starts it again from there. A plan outside git whose task has no
`Repo:` line is the same stop, and the plan goes back through `/planning:make-plan <plan>`. A
light plan whose repositories are more than one is the stop "A light run" names. Resolve the
trunk of each repository here, from its rules as "The project rules" says.

**The plan is committed.** For a tracked plan, `git ls-files --error-unmatch <plan>` must
succeed, and the plan file must exist at the local `<trunk>` of the home repository. For every repository of the plan, the commit its `<trunk>` stands on,
`git -C <main checkout> rev-parse <trunk>`, is kept in the session and in no file: a tracked
plan is read at the home repository's commit, the anchors run in each main checkout as it
stands there, and each branch is cut from its repository's commit, so a trunk that moves while
the owner reads changes nothing the run stands on. When a tracked plan is not committed, or not
at the trunk, stop and say that the plan is not committed; the commit item of `/planning:make-plan` is how it
gets there. An untracked plan is read from its file and has no commit to check.

**Behind origin.** For each repository that has a remote `origin`: `git fetch origin`, then
count how far the local `<trunk>` is behind `origin/<trunk>`. Behind by anything: say by how
many commits and in which repository, and the go below is the answer to whether the run goes on
with the local trunks as they are. Each branch is cut from its recorded commit, the plan's
commit on the home one; the freshness against `origin` is the pull request's job, after the run.

**Premises, Owner Sign-off, waves, go.** Read the plan as the paragraph above says, with each
anchor run in the main checkout of the repository it names, at that repository's recorded
commit. Run every anchor in `## Premises` the way the refresh mode of
[`make-plan`](../make-plan/SKILL.md) does, and report each as in place, moved, or false. A
moved anchor is reported and the run goes on. A false premise is a fork for the owner and
stops the start with no branch, no worktree and no journal made in any repository: the plan
goes back through `/planning:make-plan <plan>`, and `/planning:exec-plan <plan>` starts again
from it. Then show `## Owner Sign-off` as it is written. Every line there is settled; the run
does not reopen it, and a subagent that meets an owner's judgement not written there stops the
run. Then print the waves: read every task's `After:` and `Needs:`, and list wave by wave which
tasks run together, each with its repository and the reason its `After:` gives. An `After:`
that names a title no task carries, or a cycle, is a stop: the plan goes back through
`/planning:make-plan <plan>`.

**The environment, before the go.** Everything that can be checked without a worktree is
checked here, in every repository of the plan, and what is missing is said in the message that
asks for the go:

- what `## Execution` of the plan names beyond the tree: a binary on `PATH`, credentials, a
  device's address, fetched weights. Check each the way Execution says. An item the host does
  not have is a stop before the go: a task cannot be gated without it;
- what the `Environment` section of each repository names for the surfaces its tasks' `Where:`
  lines touch: a toolchain, a service, a stand, and how it builds against the run branch of
  another repository of the plan. Checked the same way, with the same stop;
- the review tools, `revmux`, `claude` and `codex` on `PATH`. No `revmux`: stop, with the
  install command (`brew install umputun/apps/revmux`). No `claude`: stop, nothing here runs
  without it. No `codex`: not a stop. Say so in the message that asks for the go: the review
  rounds then run on the profile `claude-only` instead of the profiles of Step 5;
- a stand a task's `Needs:` names: whether it is up, checked the way the `Environment` section
  says. A stand another run raised, or another stand on the same ports, is where this run would
  stop. Say which stand is up; the owner's go decides whether the run starts beside it;
- disk: the free space of each volume that holds a main checkout of the plan (`df -k`) and, on
  a host that runs Docker, what Docker holds (`docker system df`). A lane is one more copy of
  its repository's checkout, plus the packages the `Environment` section installs for the
  surfaces its `Where:` names. Free space below two copies per lane of the widest wave is where
  the run cleans before it stops: what can be rebuilt and nobody else holds. The caches a
  stopped run of this plan left, `rm -rf <journal>/cache`, then `docker image prune -f` and
  `docker builder prune -f`. Never a build cache the host shares, an image by name, a
  named volume or a stand: those are other sessions' work. Measure again. Still below: a stop
  before the go, with the numbers;
- a barrier `## Execution` names: an open plan whose merge this one waits for;
- in every repository, a branch `<branch>` or a worktree `.claude/worktrees/<slug>` that
  already exists: it stands on that repository's recorded commit, or it is the stop that
  "Worktrees" below names. This is checked in every repository before the go, so the cut never
  stops halfway.

The same message names the branch the run will cut in every repository, `<branch>`, and the
trunk and the recorded commit of each. The name follows the `Trunk` section; by default it is
`<type>/<slug>`, its type the commit type the plan's Goal reads as: `feat` for new behaviour,
`fix` for a defect, `refactor`, `docs` or `chore` when nothing a user sees changes.

Then wait for the owner's go; it confirms the schedule, the branch and what the environment
check said.
After the go the run asks nothing until a report.

**Worktrees.** On the go, in every repository of the plan, from its main checkout, `<sha>`
being that repository's recorded trunk commit:

```bash
git worktree add .claude/worktrees/<slug> -b <branch> <sha>
```

Each branch starts from the tree the premises were checked on, wherever the trunk stands by
then. A branch `<branch>` that already exists without a worktree gets the worktree without `-b`
when `git rev-parse <branch>` is `<sha>`; on any other commit the start is a stop: the branch
was made outside the skill and holds commits the premises never saw, and the owner deletes or
renames it. A worktree already at `.claude/worktrees/<slug>` is taken by the same rule, its
`HEAD` at `<sha>` or the same stop. A main checkout is not touched beyond that: no merge
into the trunk, no checkout, nothing that moves what the other sessions there stand on.
What a fresh worktree needs is Step 2.

Then write the journal's `repos`, one line per repository,
`<repo> <main checkout> <run worktree> <branch>`, and its `plan`, the plan's absolute path: in
a tracked plan the copy in the home repository's run worktree, in an untracked plan the file
itself.

**Base.** In every repository of `repos`, run `EXEC_PLAN_JOURNAL=<journal> scripts/base.sh
<repo> <trunk>` from its run worktree. It records `<journal>/base.<repo>`, the trunk commit the
branch was cut from, or checks the one recorded. It refuses a merge commit between the base and
`HEAD`, and a recorded base the tree no longer matches: a branch rebased or merged by hand since
the run started. The review range, the regroup and the revdiff of the repository all start at
this commit, so the refusal is the stop and its line is the reason. On a continuation a
repository of `repos` without its `base.<repo>` gets it recorded here: its branch has not moved
since the cut.

Then log it with `EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh "run started: <plan>,
<repositories>, base <repo> <sha>, ..."`, or `run continued` when the journal already holds
a base.

## Step 2: preflight, once

Once per run, before the first wave: what only a worktree can be given, in each repository of
the plan. Its result goes into the prompt of every lane and of every integrator as the
`PREFLIGHT` block.

- **The worktree's own environment**: what the `Environment` section of each repository asks a
  fresh checkout to install for each surface a task's `Where:` names, and what `## Execution`
  asks for beyond it, and the files git ignores that a gate needs, model weights first of all,
  linked from the main checkout the way Execution says. A repository that builds against the
  run branch of another is set up the way its `Environment` section says. An item that cannot
  be met is a stop before the first wave.
- **The block.** Three to seven lines: what is present, what was done and where (which
  install in which path, in which repository), which profiles the review rounds will use, what
  Execution named and how it was met, which stand is up and whose it is when the owner said so,
  and the free space the check of Step 1 found.

## Step 3: the wave loop

Repeat until no task section holds an open `[ ]`:

1. **The ready set.** Re-read the plan. A task is ready when its section holds an open `[ ]`,
   every task its `After:` names has no open `[ ]`, and either no checkbox of it carries a
   `⚠️` or its lane worktree exists: a stopped lane whose marks the integrator carried into the
   plan is resumed on a continuation, and its `⚠️` is the question the continuation answers.
   Two ready tasks with the same `Needs:` value do not run together: the one earlier in the
   file runs now, the other waits. An empty ready set with open tasks left is a stop: the open
   tasks wait on a task that stopped, or on the owner, and the report of Step 4 says which. No
   open task left: go to the whole tree, below.
2. **Announce the wave** in one block: its number, one past the highest `wave N` in the
   journal, and each task with its repository and its open checkboxes. Log
   `EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh "wave N: started, tasks <list>"`.
3. **Cut the lanes.** For each task of the wave, from the main checkout of its repository,
   `<tip>` being the `HEAD` of that repository's run branch:

   ```bash
   git worktree add .claude/worktrees/<slug>-task-<N> -b <slug>-task-<N> <tip>
   ```

   Then copy the task's section of the plan, from its `### Task N:` line to the line before
   the next heading, into its progress file `<journal>/lanes/task-<N>.md`, which the lane ticks
   from then on.

   A lane worktree that already exists is a stopped lane continuing: it keeps its branch and
   its commits, and before its lane runs, its repository's run branch is merged into it from
   inside that worktree, `git merge <run branch>`, so the lane sees the waves integrated since
   it stopped. A conflict in that merge is a stop with the report of Step 4. Its progress file
   is written anew from the plan's section as it stands, which brings the owner's answer, and
   every mark of the old file, a tick or a `⚠️`, is set again on the item whose text still
   stands word for word; an item the owner rewrote comes without a mark. A task gets in its
   worktree, before the lane starts, what the `Environment` section of its repository asks a
   fresh checkout to install for each surface its `Where:` names, a surface a generator writes
   from what the task changes included: a generator that runs without the packages of the
   surface it writes stops there. The ignored files of Step 2 are linked into the lane the same
   way. A lane that continues keeps both.
4. **Launch the lanes**, all of them in one message, each a subagent (the Agent tool,
   `general-purpose`, `name` the lane's name, in the background) with the prompt of
   [`references/task.md`](references/task.md), every placeholder substituted; `WAVE` lists every
   task of the wave, and `PROGRESS` is the lane's progress file. Then wait for all of them.
   This session reads no code, fixes nothing and
   runs no gate itself; a lane that comes back red goes to a fresh subagent, not to this
   session. A lane logs a line before every command that runs for minutes, with the time it
   expects. When the owner asks how the run stands, answer from the journal: which lane is in
   which command and since when. A lane whose last such line is older than twice the time it
   named is not waited for further: look at its worktree and at its processes, and at
   `pmset -g log` for a sleep of the host, which stops Go timers and makes a live test look
   hung. A lane that went idle with its task open, saying it waits for a command, is not
   woken when that command ends: watch the command's output file, and when it ends, send the
   lane by name, with the SendMessage tool, «your command has ended: read <the file> and go
   on».
5. **Read what came back**, lane by lane, as each ends: the lane's progress file and the
   journal lines it appended.
   - Every checkbox of the task is `[x]`: say "Task N done" in one line; the lane has logged
     the details.
   - `[blocker] environment task N` in the journal and no `⚠️` of another kind: when every
     other lane of the wave has ended, resume this lane once by its name, with the SendMessage
     tool and the words «rerun now»; the tool is deferred in a fresh session and is loaded
     with ToolSearch first. Read it again when it ends. Still red: the lane stopped, as below.
   - A `⚠️` on a checkbox, or an `[owner]` or `[blocker]` line of another kind: the lane
     stopped. Its worktree, branch and progress file stay. The wave goes on without it.
   - Open checkboxes and no `⚠️`: one retry, a fresh subagent on the same lane, the same
     worktree, branch and progress file, not a clean worktree cut again, with the errors of the
     first attempt in `RETRY`, its report and the
     journal lines it wrote. One retry, not two. Still open: the lane stopped, and this session
     logs `[blocker] task N: <what the two attempts left>`.
6. **Integrate.** When every lane of the wave has ended, spawn one subagent (the Agent tool,
   `general-purpose`) with the prompt of [`references/integrate.md`](references/integrate.md),
   every placeholder substituted: `REPOS` names each repository a lane of the wave runs in,
   with its run worktree, its branch, its base and the tip its lanes were cut from; `LANES`
   names only the lanes whose progress file has every checkbox `[x]`, each with its
   repository, worktree and progress file, in the order the Shared files table of the plan gives, the lane that is second after
   the one that is first, the rest in file order; `STOPPED` names the lanes that stopped, the
   same way. One integrator works through every repository of the wave: one agent writes the
   plan. Wait for it. Read the journal lines it appended:
   - `wave N: integrated` and no `[owner]` or `[blocker]` line: remove the integrated lanes,
     `git worktree remove .claude/worktrees/<slug>-task-<N>` and
     `git branch -D <slug>-task-<N>` from the main checkout of each lane's repository, for the
     integrated lanes only, then the lint cache of each,
     `rm -rf <journal>/cache/lint/<repo>/<slug>-task-<N>`, and
     the Go build cache of the run, `rm -rf <journal>/cache/go-build`. Go compiles the
     module's packages again under the path of every worktree, a copy of the compiled tree per
     lane, and nothing reads those entries once the lane is gone. No lane builds at this
     moment, and the next wave starts with a cold build. The progress file of an integrated
     lane stays in the journal: the status page reads it. The lint caches
     of the run worktrees stay. Then, when no lane of the wave stopped, the next pass of
     the loop; when one did, the report of Step 4, after the integration and not before it.
     The review and the finalize do not run after such a stop.
   - A red check the integrator could not make green: one retry of the integrator with `RETRY`,
     as for a lane. An `[owner]` line, a `[blocker] environment integration N` line, or a
     merge it could not resolve: a stop with the report of Step 4. Nothing of the wave is
     integrated twice: the integrator's own journal line says how far it got, and the lanes it
     merged have their ticks in the plan.

Nothing is asked between waves. A lane that cannot close an item leaves it open with its
reason, and the owner reads the reason in the report, not a question mid-run.

**The whole tree.** A lane checks only what it touched: the build of the surfaces it changed
and the tests of the packages it changed, the generators and the docs check when it
moved them. An integrator builds and lints the whole tree of each repository its wave touched
and runs the tests only of a surface two lanes of its wave changed, since a surface one lane
changed was tested by that lane. Once every task is closed, the whole tree of every repository
of the plan is checked once, before the first review round, by an executor like the lanes' and
not by the finalize: what goes red there is fixed by the run, and the fix is reviewed with the
rest of the branch. For each repository, one after another, spawn one subagent (the Agent tool,
`general-purpose`) with the prompt of [`references/check.md`](references/check.md), every
placeholder substituted for that repository, and wait for it. The order is the one the
`Environment` section gives the builds across repositories, a repository another builds against
first; with none given, the order of `repos`. A repository whose branch holds only the plan's
own commits has nothing to check and is skipped. The subagent runs the whole-tree checks the
`Gates` section names, the generators' drift check, the docs check, the build, the lint and the
tests, every component whatever the branch touched, and fixes and commits until they are green.
Read what came back:

- `whole tree: <repo>: green` in the journal and no `[owner]` or `[blocker]` line: say so in
  one line and go to the next repository, then to the review. A
  `[deviation] … red at the base as well` line beside it is a failure the branch did not cause:
  the same check, run alone, is red at the base. The run goes on, and the line goes into
  `open:` of the run report.
- an `[owner]` or `[blocker]` line: stop with the report of Step 4. The review and the finalize
  do not run.
- neither: one retry, a fresh subagent with the errors of the first attempt in `RETRY`. Still
  not green after it: this session logs `[blocker] whole tree: <repo>: <what the two attempts
  left>` and stops the same way.

Log the start of each with
`EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh "whole tree: <repo>: started"`. A continuation
with every task closed runs it again in every repository: it is the one state of the run no
checkbox records.

## Step 4: the stop report

In chat, no file. A stop in Step 3, 5 or 6 ends on it:

```
stopped at: wave N: <tasks> | integration of wave N | whole tree, <repo> | review round <repo>/<run>, <profile> | finalize, <repo>, <regroup | close>
open:       <the checkboxes left open, each with its ⚠️ reason | the findings left, each with
            its sort | the gate that is red>
lanes:      <each lane worktree that still exists: its task, its repository, its branch @ <sha>,
            why it stopped>
journal:    <every [owner] and [blocker] line, verbatim>
logged:     <every [decision] and [deviation] line, verbatim>
branches:   <one line per repository: <repo>: <branch> @ <sha>, base <sha>, <worktree path>>
next:       <what the owner decides | for a [blocker] environment line, what on the host to
            repair>; an answer that changes the plan goes into the plan, <the plan's absolute
            path>: in a tracked plan committed there through `commit.sh` from the home
            repository's run worktree, in an untracked plan edited in place; then
            `/planning:exec-plan <plan>` continues: the stopped lanes are brought onto their
            repository's run branch and rerun, and the loop goes on from the ready set, or from
            the whole-tree check when every task is closed
```

The plan the run reads is the one the journal's `plan` names, and that is where an answer to an
`[owner]` or a `[blocker]` line that changes the plan lands. In a tracked plan it is an edit to
the copy in the home repository's run worktree, committed there through
`EXEC_PLAN_JOURNAL=<journal> scripts/commit.sh`, then the run continues. A tracked plan
refreshed on the trunk through `/planning:make-plan <plan>` instead never reaches the branch,
because the trunk is not merged into it: for that, remove the run worktrees, the lane
worktrees and the branches in every repository and the journal, and start the run again from
the refreshed commit. In an untracked plan the answer is an edit to the file in place, with no
commit. A refresh that moves its premises to newer trunks needs the same restart: the branches
stand on the commits the old premises were checked on.

## Step 5: review rounds

Every task is closed. The branch of each repository from its `base.<repo>` now goes through
revmux rounds until one is clean or three have run. Each repository is reviewed on its own:
its rounds, its fixer and its count of rounds are its own, and a plan of three repositories
starts with three first rounds. The repositories are reviewed one after another, in the order
of the whole-tree check; a stop in one is the stop of the run, and the repositories after it
wait for the continuation. A repository whose branch holds only the plan's own commits gets no
round. "The branch", "the task" and "the round" below are those of the repository under review.

The `Review` section names two profiles: the first round's, by
default `comprehensive`, and the profile of every round after it on the fixes, by default
`final`. Every round runs on `claude-only` when Step 1 found no `codex`. This file calls
them the first-round profile and the last-round profile.
The three are counted over the whole run, by the round directories under the task in the
repository's main checkout, `.revmux/tasks/<slug>-<repo>/`, not per session. The first-round
profile runs once on a branch: it is the round with both models and every lens, and a second
one reads a diff that was already read. Load the `revmux:revmux` skill and follow it, with what
a run changes:

- The subject is the branch: `git diff <base>...HEAD` in the repository's run worktree, the
  whole range in every round. The lanes are already in it, and no lane worktree exists by now.
  `scope.md` carries that range and the repository's name, says to read the plan at its
  absolute path in full before the diff, and on a round after the first names the fix commits
  since the previous round. `goal.md` is the plan's Goal in two lines and the criteria: the
  `Result:` of every task of this repository holds, nothing under `## Out of Scope` moved, the
  rules of the project hold. On a round of the last-round profile it is the merge
  gate, as the revmux
  skill asks of the last round before a merge: the round answers whether anything in the branch
  should not ship, and finding nothing is a valid answer. `profile.md` names the root
  `CLAUDE.md` of the repository, the `CLAUDE.md` of each surface the branch touches, the rules
  file the repository's rules come from when it has one, with the rules its `Review` section
  holds a branch to, and the plan's `## Decisions`
  as where the rules live, and says a Decision is settled: that the branch does what a Decision
  says is not a finding, and that a Decision is wrong is an open question.
- The task id is `<slug>-<repo>`, whatever the branch is called, also in a plan of one
  repository. The plan's own review ran under `plan-<slug>` and is another subject; the two are
  never joined. The rounds are `NN-initial`, `NN-after-fix` and `NN-final`, `NN` one past the
  highest round already under the task.
- Rounds run from the repository's main checkout with `--workdir <its run worktree>`, headless
  (`--no-tui`), in the background: the project layer,
  `.revmux/prompts/` and `.revmux/lenses/`, is read from the process working directory, and
  the archive lands in that main checkout's `.revmux/tasks/`. `revmux new` runs from there
  too. The round's command starts with `caffeinate -i`: Claude Code keeps the host awake
  while a subagent runs and drops that hold while a background shell is all that runs, so a
  host on battery sleeps in the middle of a round.
- The revmux skill's questions are not asked, and its loop is not entered: headless is
  settled, the fixer below decides what is fixed, and this step is the loop.

**A continuation.** The repositories are reviewed in a fixed order, so the journal says where
the review stopped: the repositories before the one whose `review round <repo>/…` line or
fixer stopped the run are done, and the ones after it have not started. A repository that is
done is not reviewed again. In the one that stopped, its task already holds a round, and its
review does not start over. The last round stopped on an `[owner]` line, and the plan now holds the answer, or on
a `[blocker] environment` line, and the owner has repaired the host: give the
fixer the findings of that round again, `findings.json` in its directory, then run the
last-round profile on the commits it makes. With three rounds already under the task, the fixer
runs and no round follows. The repositories after it start at the first-round profile.

Read the result in this order; the first line that applies decides:

1. The exit code. `0` and `1` are finished rounds. `2` is a failed one: read the stderr log.
   When the round directory holds `findings.json`, the round finished and only its write to
   stdout failed; read the findings there. Otherwise stop with the report of Step 4. A failed
   round is not evidence; the finalize and the close do not run.
2. `sources.degraded`. Non-empty, or `sources.expected` not equal to `sources.reported`: stop
   with the report of Step 4. A partial round says nothing about the branch, and its silence
   is not a clean round; the finalize and the close do not run.
3. `findings`. No `critical` and no `major`: the round is clean. With no `minor` either, log
   it and go to the next repository, or to Step 6 after the last. With a `minor`, the fixer
   runs once more, in its minor pass, and the repository is done with no round after: a round
   over the fixes of minors brings about as many new minors as it closes, so a loop on them
   never ends. Otherwise the fixer, then the next round. After the third round no fixer runs
   and no round follows, unless the third is clean and holds minors, which get the minor pass
   like any clean round: what the third round leaves goes into the run report as open
   findings, and the repository is done.

Log every round with `EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh "review round
<repo>/<run>: <profile>, <n> critical, <n> major, <n> minor, degraded <none | names>, <clean |
clean, minor pass | fixer | stop>"`.

**The fixer.** One subagent (the Agent tool, `general-purpose`) with the prompt of
[`references/fixer.md`](references/fixer.md), every placeholder substituted for the repository,
and wait for it. It sorts every finding into fact, fork or noise: a fact is fixed, gated and
committed through `commit.sh`; a fork is logged as `[owner]` with the question in plain words;
noise is dropped with its reason in the journal. This session fixes nothing itself. Read what
came back, the journal lines it appended and its report:

- an `[owner]` or `[blocker]` line: stop with the report of Step 4, the same stop as after a
  wave. The finalize and the close do not run, and the branch waits on the owner's answer;
  `/planning:exec-plan <plan>` after it continues the review as "A continuation" above says.
- no commit, because every finding was noise or an answered question: no round follows. A
  round on an unchanged diff reads the same diff again. The dropped findings go into the run
  report with their reasons, and the repository is done.
- after the minor pass: the repository is done, whatever was committed. The minors it left go
  into the run report as open, each with its reason or its question. The minor pass logs no
  `[owner]` and no `[blocker]`, because a minor does not hold the branch.
- otherwise: the next round, on the fixes.

When every repository is done, Step 6.

## Step 6: finalize

One subagent (the Agent tool, `general-purpose`) with the prompt of
[`references/finalize.md`](references/finalize.md), every placeholder substituted, and wait
for it. In every repository of `repos` it regroups the history from that repository's base
behind a `backup/` branch and proves the tree did not move. Then it closes the plan by its
mode: a tracked plan moves into the closed-plans directory of the `Plans` section in a commit of
the home repository; an untracked plan moves with a plain `mv` into the closed-plans directory
beside it, as [`form.md`](../make-plan/references/form.md) places it, and nothing is committed.
Either way it logs `finalize: plan closed, <the plan's absolute path after the close>`, the line
the status page follows, and reports. It runs no gate, not the usual last check on the final
tip: the whole tree was checked before the review, and the regroup leaves the tree byte for byte
as it was. This session does none of that itself. A `[blocker]` line from it, or a diff against
a backup that is not empty: stop with the report of Step 4. The history stays as the subagent
left it, the backup branch holds the tip, and the plan stays where it was.

**Clean up after the run.** Before the report, from the main checkout of each repository,
remove what the run left on the disk and nothing it did not make:

- a stand the run's lanes raised that was down when Step 1 looked, taken down the way the
  `Environment` section says, its volumes with it. A stand that was up before the run is
  another session's and stays. A command that takes down every stand on the host, the stand
  of another checkout included, is never run here;
- the scratch worktrees of the base and tip checks, when one is left in any repository;
- on a host that runs Docker, `docker image prune -f`: every rebuild of a stand's images left
  the old layers dangling;
- the run's caches, `rm -rf <journal>/cache`.

The report's `whole tree:` line is followed by what was freed, `df -k` before and after.

Then run `EXEC_PLAN_JOURNAL=<journal> scripts/audit.py`. Its count goes into the report's
`audit:` line, and its findings follow that line as they were printed, up to twenty; past
that, the count per rule.

Then the run report, in chat, no file:

```
run:       <one line per repository: <repo>: <branch> @ <sha>, base <sha>, <worktree path>>
tasks:     <n>, all closed, in <m> waves
review:    <one line per repository: <repo>: <n> rounds (<run>: <profile>, ...); <n> fixed,
            <n> dropped, <n> open>
history:   <one line per repository: <repo>: <n> commits → <m> commits, backup/<slug>-<stamp>>
whole tree: <one line per repository: <repo>: green, <n> fixes | <the checks and their result>>
plan:      <the plan's absolute path after the close>
audit:     <n> findings in <n> commands of <n> agents | no transcript found
logged:    <every [decision] and [deviation] line, verbatim>
open:      <every finding not fixed: a minor left, a finding dropped and why, an open
            question and where the plan answers it, a finding of the third round; every check
            red at the base as well; every record a lane or a fixer left waiting for the
            owner's acceptance, as the `Records` section says>
owner:     <in a plan of several repositories, the steps the owner takes before each branch can
            land, in the order of the dependencies between them: push the branch of a
            repository another builds against and tag it, then pin that tag in the repository
            that builds against it, as its `Environment` section says; the run did none of
            them | none>
next:      revdiff | the pull requests of <branch>, one per repository, revdiff is not installed
```

A consumer's branch built against the unpushed run branch of its producer is not ready for a
pull request until the owner's steps of `owner:` are done: the report says so plainly, and the
run takes none of those steps.

**revdiff.** The owner is back, and from here questions are allowed again. When `revdiff` is
on `PATH`, load the `revdiff:revdiff` skill and open it from each repository's run worktree in
turn, in the order of `repos`, on the whole branch, `<base>...HEAD` with that repository's
base: not the last commit, not the working tree. When it closes, read the
annotations by the refs of this run, never by the newest history file: parallel reviews of
other branches write there too. Every annotation gets one line in the reply,
`<repo> <file>:<line> <the comment, shortened> -> answered | fixed in <sha> | disagree: <why>`. A
question is answered and changes nothing. A change is made by this session in that repository's
run worktree, gated, and committed through
`EXEC_PLAN_JOURNAL=<journal> scripts/commit.sh` on top of the regrouped history, as
`fix(<scope>): ...` or `docs(<scope>): ...`. An annotation that is unclear is quoted back with
two readings. None is skipped, and none becomes a backlog item, a plan or a decision record
unless it says so. No annotations: say so and name the history file that was read. Reopen
revdiff on the fixes only when the owner asks. A gate run here builds the run's caches again:
remove them once more after the last fix. End on one line: the count of annotations, how many
were fixed, answered and disagreed with, and that the pull requests of `<branch>` onto each
repository's trunk are next, after the owner's steps of `owner:`. Without `revdiff`, the run
report is the end and the pull requests are the owner's next step.

## Common mistakes

| Mistake | Fix |
|---|---|
| Cut the worktree before the premises were rechecked | Premises, Owner Sign-off, waves, go, then the cut; a false premise leaves nothing to remove |
| Took a branch `<branch>` or a worktree for a continuation | A `base.<repo>` file in the journal says a run exists; without one, the question of Step 1 |
| Cut the worktree from the trunk as it stood after the go, or attached a branch `<branch>` as it stood | From the trunk commit the premises were checked on, per repository; a branch `<branch>` on any other commit is a stop |
| Cut the branch in one repository, then found the next one missing or its branch on another commit | Every repository is found and checked before the go, the cut runs in all of them after it |
| Derived the journal from the checkout a script runs in, or ran a script without `EXEC_PLAN_JOURNAL` | The journal's place comes from the plan's mode; every script call sets the variable to its absolute path |
| Started a light plan of several repositories | A stop before anything else; `/planning:make-plan` writes it as a full plan |
| Sent a mid-run answer through `/planning:make-plan` on the trunk | The plan the journal's `plan` names: in a tracked plan the home repository's run worktree, through `commit.sh`; in an untracked plan in place; a refresh on the trunk restarts the run |
| Committed an untracked plan, or closed it with a commit | Never; it is ticked in place and closed with `mkdir -p` and a plain `mv` |
| Cut the branch from `origin/<trunk>` | From the recorded local trunk commit, plan commit included; the pull request brings origin |
| Merged or fast-forwarded the trunk in the main checkout | Never; other sessions stand there. Count, ask, then cut |
| Wrote git commands for the three scripted operations | `commit.sh`, `base.sh`, `progress.sh` |
| Ran `git rm` or `git mv` before `commit.sh` | `rm` or `mv`; the script stages a path gone from the tree as its removal |
| Ran the tasks one after another because the plan has `After:` lines | Every task whose `After:` is met runs in the same wave |
| Took the plan's file order as the order of execution | The ready set; file order only breaks a tie for `Needs:` |
| Cut a lane from the trunk, from the previous wave's tip or in the home repository for a task of another | From the `HEAD` of its own repository's run branch at the start of the wave |
| Started a lane before its progress file existed | Copy the task's section into `lanes/task-<N>.md` first; the lane ticks that file |
| Cut a second worktree for a stopped lane | Its worktree exists; merge its repository's run branch into it, write its progress file anew from the plan with its old marks, and rerun |
| Launched the lanes one per message, waiting for each | All lanes of a wave in one message, then wait for all |
| Resumed an environment-stopped lane while its siblings still ran | After every other lane of the wave has ended, once |
| Fixed a red lane in this session | A fresh subagent on the same lane with the errors in `RETRY`, once |
| Asked a question between waves | Nothing is asked between the go and a report; a lane leaves an item open with its reason |
| Asked for the go, then stopped a minute later on a missing credential or a busy stand | The environment is checked before the go and said in the same message |
| Waited on a lane that had been silent for hours | The journal says which command it is in; past twice the named time, look at its worktree and processes |
| Retried a lane that stopped on `[owner]` | It is the owner's; report and stop |
| Stopped the run the moment one lane stopped | The wave ends, the integrator merges the closed lanes, then the report |
| Continued after a `⚠️` | The wave's integration, then stop; the review and the finalize do not run |
| Integrated a lane whose task has a `⚠️` | Only lanes with every checkbox `[x]`; a stopped lane keeps its worktree and branch |
| Merged a lane in this session, or resolved a conflict here | The integrator subagent; this session merges nothing |
| Removed a stopped lane's worktree at the end of the wave | Only integrated lanes are removed |
| Let a lane tick the plan, or ticked the main checkout's copy | A lane ticks its progress file; the integrator carries the marks into the plan |
| Ran one integrator per repository | One per wave, through every repository: one agent writes the plan |
| Wrote the report to a file | The report is in chat; the journal is the file |
| Ran the whole-tree tests in every lane or integration, or not at all | A lane tests what it touched, an integrator what its wave touched; the whole-tree tests run once, in the whole-tree check after the last wave |
| Left a red whole tree to the finalize | The check's own subagent fixes it; the finalize runs no gate |
| Took a failed or degraded round as clean | Exit code, then `sources.degraded`, then the findings; a partial round stops the run |
| Ran revmux from the worktree | From the repository's main checkout with `--workdir`; the project layer is read from the process directory |
| Reviewed several repositories in one round, or under the task `<slug>` | One loop per repository, task `<slug>-<repo>`, also for a plan of one repository |
| Fixed a finding in this session | The fixer subagent, one per round; it sorts before it fixes |
| Ran a fourth round, or one on an unchanged diff | Three at most over the whole run; what the third leaves, and what a fixer dropped, goes to the report |
| Ran the first-round profile again after the owner answered a finding | The fixer on the last round's findings, then the last-round profile on its commits |
| Passed a `model` to a subagent | None; every subagent runs on the session's model |
| Took down every stand on the host, removed an image by name or a named volume to free space | Only what the run made: the stand its lanes raised, dangling layers, its own caches |
| Ran `go clean -cache` or `golangci-lint cache clean` | Those clear the caches every session on the host shares; the run removes `<journal>/cache` |
| Built, tested or linted Go without `. scripts/cache.sh` in the same shell call | The command writes into the shared caches, and the lint leaves there the paths of a worktree that will be gone |
| Went to the finalize from a clean round with simple minors left open | The minor pass: one fixer run over the minors, then Step 6 with no round after it |
| Ran another round on the fixes of the minor pass | None; minors arrive at about three a round, and a loop on them does not end |
| Regrouped without the backup, or with `--soft` | `backup/` at the tip, `git reset <base>`, groups through `commit.sh`, an empty diff |
| Merged the trunk into the branch at finalize | Never here; the pull request brings the branch onto the trunk |
| Pushed or tagged a producer, or pinned it in its consumer | The owner's steps; the run report lists them in dependency order |
| Read the newest revdiff history file | By the refs of this run; other reviews write there too |
| Opened revdiff on the last commit | The whole branch of each repository, `<base>...HEAD` with its own base |
| Cut lanes or ran the first-round profile for a plan whose Execution says light | One executor in the run worktree, the light check, two rounds at most on the lens set |
| Moved a light run onto the full path when the executor outgrew it | Stop with the report of Step 4; the owner decides |
