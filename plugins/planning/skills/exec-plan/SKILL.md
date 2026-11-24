---
name: exec-plan
description: >
  Use when a plan in `docs/plans/` is to be run, or a run of one continued: start the branch,
  run every task whose `After:` is met as a lane in its own worktree, integrate each wave
  through one subagent, check the whole tree once after the last wave, then review the branch,
  regroup its history and close the plan. A plan marked light runs with one executor, a
  narrower check and one review agent. With `peer` after the path, a second agent in the
  split pane reads the plan before the go and every wave after it is integrated. Not for a
  mechanical edit one session makes in place.
user-invocable: true
disable-model-invocation: true
---

# Run a VMS plan

This skill takes a plan in the form of
[`make-plan/references/form.md`](../make-plan/references/form.md) from its commit to a closed
plan: a branch, the tasks in waves of parallel lanes, a journal, then the review rounds, the
regroup of the history, the move to `completed/` and the owner's revdiff. The argument is the
path of the plan under `docs/plans/`. A path that does not exist is the first stop, and a plan
that already sits under `completed/` is such a path.

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
subagent in its own worktree on its own branch, and the lanes of a wave run at the same time.
When every lane of the wave has ended, one integrator subagent merges the lanes that closed
their task into the run's branch, regenerates what is generated, builds and lints the tree and
runs the tests where two lanes of the wave met. The next wave starts from that tip. The tests of the
whole tree run once, in the whole-tree check after the last wave. A plan with no `After:` line
runs every task in the first wave. A plan whose `## Execution` carries the Mode line
`light` runs as "A light run" below says.

Three operations are scripts under `scripts/`, and this file never spells out their git
commands:

- `scripts/commit.sh <message> <path>...` stages the named paths, refuses an index that holds
  anything else, and commits without a pathspec, so the hooks run on the real index and a file a
  pre-commit hook stages lands in the commit. A tracked path gone from the tree is staged as its
  removal, so a file is deleted with `rm` and moved with `mv`, never `git rm` or `git mv`: those
  take the path out of the index before the script can name it, and it fails;
- `scripts/base.sh <slug>` computes the base commit of the run and records it;
- `scripts/progress.sh <slug> <line>` appends one timestamped line to the journal.

Each exits non-zero with one line of reason on a refusal. A refusal is a stop: the line goes
into the report, and nothing is tried around it.

A fourth file there is sourced, not run. `. scripts/cache.sh` sets `GOCACHE` and
`GOLANGCI_LINT_CACHE` to the run's own caches for the commands that follow in the same shell
call, and the next call sources it again. Every command of a run that builds, tests or lints
Go starts with it, `. scripts/cache.sh && make lint`, in a subagent and in this session alike.
`commit.sh` sources it itself, for the pre-commit hooks.

`scripts/audit.py <slug>` reads the run back. Claude Code keeps the transcript of every
subagent, and the script lists the shell commands in them that break a rule of the prompts: Go
built outside the run's caches, a commit made around `commit.sh`, a bypassed hook. A finding
is a place to look, not a verdict, and it changes nothing in the run: it tells the owner which
line of a prompt an agent did not follow.

`scripts/status.py <slug>` draws the run as one page, `.exec-plan/<slug>/status.html`: the
phase; this session and the peer of a run that has one, with their turns, their tokens and
the mail between them; every wave with its tasks and its integrator under it, each with its
time, model, context, turns and tokens in and out; the waves still ahead, as the `After` chains
of the open tasks allow them at the earliest; the whole-tree check with the gates it
ran; the review rounds; and the stops nobody has answered. The times, the turns, the tokens
and the steps come from the transcripts Claude Code keeps: one of every subagent, one of this
session, whose id the script records in `.exec-plan/<slug>/lead`, and one of the peer. `progress.sh` runs the script after a line
that changes what the page shows, so nobody calls it by hand. In an agterm session the line
that starts or continues a run opens the page as a companion row under the session and
starts one watcher for the run, `status.py --watch`, which redraws every ten seconds, so the
tokens and the checkboxes of a working lane move between journal lines. The watcher ends when
the run stops or closes, and when its page is gone. The open page pulls `status.js`, written
beside it, every five seconds and replaces its content in place, so it is never reloaded and
keeps the reader's scroll position. The page is a view of the journal, the plan and the
transcripts: the run reads nothing from it, and a page that cannot be drawn fails nothing.

The prompts of the subagents are under `references/`: [`task.md`](references/task.md) for a
lane, [`integrate.md`](references/integrate.md) for the integrator of a wave,
[`check.md`](references/check.md) for the whole tree, [`fixer.md`](references/fixer.md) for a
review round and [`finalize.md`](references/finalize.md) for the close. Each of them sends its
subagent to [`commit.md`](references/commit.md) for how a commit is made.
[`peer.md`](references/peer.md) is the brief of the peer, which its launcher hands it.

## Names and state

- The slug is the plan's file name without its date and extension:
  `docs/plans/20260930-make-plan-and-exec-plan.md` gives `make-plan-and-exec-plan`. The run's
  branch is `<type>/<slug>`, `<type>` the commit type of the plan's Goal as the go confirms it,
  and its checkout is the worktree `.claude/worktrees/<slug>` in the main checkout. The trunk is never run on, and neither is a branch another checkout stands on.
- The journal is `.exec-plan/<slug>/` in the main checkout, the first entry of
  `git worktree list`, and git ignores it. It is not a run block committed in the plan. `progress.md` is the log, `base` the base commit.
  The scripts find the main checkout themselves from whichever checkout they run in.
- The run builds into its own caches, `.exec-plan/<slug>/cache/`. `go-build/` is one Go build
  cache for every checkout of the run, so a dependency is compiled once. `lint/<the checkout's
  directory name>/` is a golangci-lint cache per checkout: that cache keeps the absolute path
  of every file it read, and an entry of a worktree that is gone comes back as an issue no
  exclusion matches. Nobody else builds into them, so the run deletes them without asking who
  is building: a cold build of the backend takes about half a minute and a cold lint under a
  minute. The Go build cache goes after every wave, a lane's lint cache with the lane, and
  the rest when the run ends. A stop leaves what is there for the continuation. Downloaded modules stay in the shared
  `GOMODCACHE`.
- A lane is named after its task: the branch `<slug>-task-<N>`, the worktree
  `.claude/worktrees/<slug>-task-<N>` in the main checkout, and the subagent's name the same
  string, cut to its last 64 characters when it is longer: the Agent tool takes no longer name.
  The lane's branch is cut from the tip of the run's branch at the start of its wave. A lane's branch is local
  and removed after its wave, so it keeps the bare slug.
- The state of a run is the plan's checkboxes in the run's checkout, `base`, and the lane
  worktrees that exist, nothing more: no phase marker, no lock, no dirty-tree check. A task is closed when every checkbox of its section is `[x]` in
  the run's checkout, which happens only after its lane was integrated, or, in a light run,
  once the executor has committed it there. A lane worktree that
  exists for an open task is a lane that stopped, and its branch holds what it committed.
- `base` is also what says a run exists: Step 1 continues a run when the journal holds it and
  starts one when it does not. A second `/exec-plan` on the same plan goes the way the first
  went: the wave loop from the ready set, then the whole-tree check, then the review, which
  goes on from the rounds the task already holds and never starts over (Step 5). With every
  task already closed it goes straight to the whole-tree check.
- Every tick and every `⚠️` is written by a lane into the copy of the plan in its worktree;
  the integrator brings the ticks of the integrated lanes into the run's checkout. The owner's
  answer to a stop goes where Step 4 says. Nobody else edits the plan, and the main checkout's
  copy is not touched.
- The run is one session. Between the go of Step 1 and a report it asks the owner nothing. It
  ends on the run report, or on the stop report of Step 4 when it meets an owner's judgement or
  an environment it cannot repair. A stop is an ordinary end of a session:
  `/exec-plan <plan>` continues the run.
- No Agent call of the run names a `model`: every subagent runs on the model of this session.

## A light run

A plan whose `## Execution` carries `- **Mode.** light — <reason>` is small enough for one
executor, by the conditions [`form.md`](../make-plan/references/form.md) gives under Mode. The
run skips what only parallel lanes and a large branch need, and keeps the branch, the gates
of what the work touched, a review that carries the architecture check, the regroup and the
owner's revdiff. Every step below holds except where this section changes it.

- **Step 1.** A light run has no peer, and the peer question is not asked. A peer the owner
  named after the path is not started, and the message that asks for the go says so. The anchors run as
  for any plan. For every shape `## Contracts and Data` names, the search of
  [`make-plan`](../make-plan/SKILL.md) Step 2 for its readers and writers runs again; one the
  section does not name is a false premise, and the plan goes back through `/make-plan <plan>`.
  No waves are printed: the tasks run one after another, in the order their `After:` lines
  allow. The message that asks
  for the go names the mode with the plan's reason, and says what the run skips: the lanes and
  the integrator, the whole-tree tests of components the branch does not touch, the
  `comprehensive` round. It names the review the run will make instead, below. The go is the
  same one go; the light mode gets no go of its own.
- **Step 2.** The same preflight, for the run's checkout: `npm ci` in its `frontend/vartova/`
  when a task's `Where:` names `frontend/vartova/` or `contracts/`.
- **Step 3.** No lane worktree and no integrator. Log `light run: one executor, <the plan's
  reason>`, then `wave N: started, tasks <list>`, `N` one past the highest `wave N` in the
  journal, the form the status page reads.
  One subagent (the Agent tool, `general-purpose`, `name` `<slug>-light`, in the background
  like a lane, under the same rules for a lane that goes idle on a command) runs the prompt of
  [`references/task.md`](references/task.md) with `CHECKOUT` the run's worktree, `BRANCH` the
  run's branch, `TASK` every open task in the order their `After:` lines allow, file order
  breaking a tie, and `WAVE` the line `light run`. It closes the tasks one after another and
  ticks the run's plan copy itself. When every task is closed, log
  `wave N: integrated, light run, no integrator`: the status page ends a wave only on that
  line, and without it the wave reads as running through the check and the review. What came
  back is read as a lane's is: the retry once, the resume once on `[blocker] environment`, and
  a stop with the report of Step 4 on an `[owner]` line or a `⚠️`. The executor's
  `[owner] light run outgrown: …` line is such a stop: it found a reader or writer the plan
  does not name, a behaviour the plan does not choose, or work one executor cannot close. The
  run does not switch to the full path by itself; the owner decides.
- **The check.** The whole-tree step runs [`references/check.md`](references/check.md) with
  `SCOPE` set to `light`: the generators, the docs check, the build and the lint of the whole
  tree, and the tests only of the components the branch touched. Log
  `whole tree: started, light`.
- **Step 5.** At most two rounds, both on one agent: `--profile claude-only --lenses
  bugs,impl,tests,conformance`, the lens set replacing the profile's roster. The first is
  `NN-initial`. Clean: the minor pass when it holds minors, then Step 6. Not clean: the fixer,
  then one more round, `NN-after-fix`, whose `scope.md` names the critical and major findings
  of the first and the fix commits, and asks whether each fix closes its finding and what it
  broke around it. That round is the last. Clean: Step 6, its minors open in the run report.
  A critical or a major in it: stop with the report of Step 4. A fixer that committed nothing
  goes to Step 6 with no round after it, as in a full run.
- **Step 6.** The finalize, the clean-up and the revdiff as written. The run report's
  `tasks:` line says `light run`, and its `whole tree:` line names the light scope.
- **A continuation** reads the same state: `base` and the checkboxes. A `⚠️` the executor
  left is in the run's own plan copy, not in a lane's, so it does not take its task out of the
  ready set here: the executor runs again over every task with an open `[ ]`, a marked one
  included, and removes the mark when it closes the item. Then the check. Then the review,
  from the rounds the task holds: with one round, the fixer on its findings, then
  `NN-after-fix` on the lens set as above; with two, the fixer on the second round's findings
  and no round after it, and what it leaves goes into `open:` of the run report. Never a
  `final` round and never a third.

## Step 1: where the run happens

The only step with questions. After the question about the peer its order is the point: the premises are rechecked, the
environment is checked and the go is given before a branch, a worktree or a base exists, so a
plan that fails the recheck goes back to `/make-plan` with nothing to remove, and what the run
would stop on an hour later is said before it starts.

**Continuation.** The run is continuing when `.exec-plan/<slug>/base` exists in the main
checkout. Nothing else says so: a branch `<type>/<slug>` or a worktree without that file is a
first run, a checkout the owner made by hand included. The checkout that runs is
`.claude/worktrees/<slug>`; a run whose worktree is gone gets it back by hand,
`git worktree add .claude/worktrees/<slug> <branch>`, the branch `git branch --list '*/<slug>'`
names. The one check of the branch is the base
check below: a checkout that does not stand on the recorded base fails there, with the line
of `base.sh` as the reason. Enter the checkout and go to the base check; the premises were
rechecked and the go given when the run started, and nothing is asked.

On a continuation, list the lane worktrees under `.claude/worktrees/<slug>-task-*`. One whose
task is closed in the run's checkout was integrated before a stop: remove it and its branch.
One whose task is open is a lane that stopped, and Step 3 resumes it.

**The peer.** The first question of a new run, asked before anything else and alone, unless
the request already answers it or the session is not in agterm, where no peer can run. Three
answers, each with what it costs:

- no peer: the run as this file describes it. A bare «ок» means this;
- Claude Code: a second session of the same account in the split pane. It reads the plan and
  every wave, and its turns are paid like this session's;
- Codex: the same work by another model, which catches what two Claudes agree on by habit.
  The hooks and the skills of this repository do not bind it, and the status page does not
  count its tokens.

A continuation asks nothing: the journal says whether the run has a peer.

**The plan is committed.** The plan file must exist at local `master`, and
the commit `master` stands on, `git rev-parse master`, is kept in the session and in no file:
the plan is read at that commit, the anchors run in the main checkout as it stands there, and
the branch is cut from that commit, so a `master` that moves while the owner reads changes
nothing the run stands on. When it does not, stop and
say that the plan is not committed; the commit item of `/make-plan` is how it gets there.

**Behind origin.** `git fetch origin`, then count how far local `master` is
behind `origin/master`. Behind by anything: say by how many commits, and the go below is the
answer to whether the run goes on with local `master` as it is. The branch is cut from the
recorded commit, with the plan's commit on it; the freshness against `origin` is `/ship`'s
job.

**Premises, Owner Sign-off, waves, go.** Read the plan at the recorded `master` commit, with
the anchors run in the main checkout. Run every anchor in `## Premises` the way the refresh mode of
[`make-plan`](../make-plan/SKILL.md) does, and report each as in place, moved, or false. A
moved anchor is reported and the run goes on. A false premise is a fork for the owner and
stops the start with no branch, no worktree and no journal made: the plan goes back through
`/make-plan <plan>`, and `/exec-plan <plan>` starts again from its new commit. Then show
`## Owner Sign-off` as it is written. Every line there is settled; the run does not reopen it,
and a subagent that meets an owner's judgement not written there stops the run. Then print the
waves: read every task's `After:` and `Needs:`, and list wave by wave which tasks run together,
each with the reason its `After:` gives. An `After:` that names a title no task carries, or a
cycle, is a stop: the plan goes back through `/make-plan <plan>`.

**The environment, before the go.** Everything that can be checked without a worktree is
checked here, and what is missing is said in the message that asks for the go:

- what `## Execution` of the plan names beyond the tree: a binary on `PATH`, credentials, a
  camera's address, fetched weights. Check each the way Execution says. An item the host does
  not have is a stop before the go: a task cannot be gated without it;
- the review tools, `revmux`, `claude` and `codex` on `PATH`. No `revmux`: stop, with the
  install command (`brew install umputun/apps/revmux`). No `claude`: stop, nothing here runs
  without it. No `codex`: not a stop. Say so in the message that asks for the go: the review
  rounds then run on the profile `claude-only` instead of `comprehensive` and `final`;
- a stand a task's `Needs:` names: `docker compose ls` says which stack is up. Every stack out
  of the compose file shares the same ports and device subnet, so a stack another run raised
  is where this run would stop. Say which stack is up; the owner's go decides whether the run
  starts beside it;
- disk: the free space of the checkout's volume (`df -k`) and what Docker holds
  (`docker system df`). A lane is one more copy of the checkout, plus the console's packages
  when its `Where:` names `frontend/vartova/` or `contracts/`. Free space below two copies per
  lane of the widest wave is where the run cleans before it stops: what can be rebuilt and
  nobody else holds. The caches a stopped run of this plan left,
  `rm -rf .exec-plan/<slug>/cache`, then `docker image prune -f` and
  `docker builder prune -f`. Never the Go or lint cache the host shares, an image by name, a
  named volume or a stack: those are other sessions' work. Measure again. Still below: a stop
  before the go, with the numbers;
- a barrier `## Execution` names: an open plan whose merge this one waits for.

The same message names the branch the run will cut, `<type>/<slug>`, its type the commit type
the plan's Goal reads as: `feat` for new behaviour, `fix` for a defect, `refactor`, `docs` or
`chore` when nothing an operator sees changes.

Then wait for the owner's go; it confirms the schedule, the branch and what the environment
check said.
After the go the run asks nothing until a report.

**Worktree.** On the go, from the main checkout, `<sha>` being the recorded `master` commit:

```bash
git worktree add .claude/worktrees/<slug> -b <type>/<slug> <sha>
```

The branch starts from the tree the premises were checked on, wherever `master` stands by
then. A branch `<type>/<slug>` that already exists without a worktree gets the worktree without `-b`
when `git rev-parse <type>/<slug>` is `<sha>`; on any other commit the start is a stop: the branch
was made outside the skill and holds commits the premises never saw, and the owner deletes or
renames it. A worktree already at `.claude/worktrees/<slug>` is taken by the same rule, its
`HEAD` at `<sha>` or the same stop. The main checkout is not touched beyond that: no merge
into `master`, no checkout, nothing that moves what the other sessions there stand on.
`npm ci` and the rest of what a fresh worktree needs are Step 2.

**Base.** Run `scripts/base.sh <slug>` from the run's checkout. It records
`.exec-plan/<slug>/base`, the `master` commit the branch was cut from. It refuses a merge
commit between the base and `HEAD`, and a recorded base the tree no longer matches: a branch
rebased or merged by hand since the run started. The review range, the regroup and the revdiff
all start at this commit, so the refusal is the stop and its line is the reason.

Then log it with `scripts/progress.sh <slug> "run started: <plan>, <worktree path>, base
<sha>"`, or `run continued` when the journal already exists.

## Step 2: preflight, once

Once per run, before the first wave: what only a worktree can be given. Its result goes into
the prompt of every lane and of every integrator as the `PREFLIGHT` block.

- **The worktree's own environment**: `npm ci` in a fresh worktree where `## Execution` asks
  for it, and the files git ignores that a gate needs, model weights first of all, linked from
  the main checkout the way Execution says. An item that cannot be met is a stop before the
  first wave.
- **The block.** Three to seven lines: what is present, what was done and where (`npm ci` in
  which path), which profiles the review rounds will use, what Execution named and how it
  was met, which stack is up and whose it is when
  the owner said so, and the free space the check of Step 1 found.

## Step 3: the wave loop

Repeat until no task section holds an open `[ ]`:

1. **The ready set.** Re-read the plan from the run's checkout. A task is ready when its
   section holds an open `[ ]`, no checkbox of it carries a `⚠️`, and every task its `After:`
   names has no open `[ ]`. Two ready tasks with the same `Needs:` value do not run together:
   the one earlier in the file runs now, the other waits. An empty ready set with open tasks left is a stop: the open
   tasks wait on a task that stopped, or on the owner, and the report of Step 4 says which. No
   open task left: go to the whole tree, below.
2. **Announce the wave** in one block: its number, one past the highest `wave N` in the
   journal, and each task with its open checkboxes. Log
   `scripts/progress.sh <slug> "wave N: started, tasks <list>"`.
3. **Cut the lanes.** For each task of the wave, from the main checkout, `<tip>` being the run
   branch's `HEAD`:

   ```bash
   git worktree add .claude/worktrees/<slug>-task-<N> -b <slug>-task-<N> <tip>
   ```

   A lane worktree that already exists is a stopped lane continuing: it keeps its branch and
   its commits, and before its lane runs, the run's branch is merged into it from inside that
   worktree, `git merge <run branch>`, so the lane sees the waves integrated since it stopped
   and the plan copy with the owner's answer. A conflict in that merge is a stop with the
   report of Step 4. A task whose `Where:` names `frontend/vartova/` or `contracts/` gets
   `npm ci` in its worktree's `frontend/vartova/` before the lane starts: `make generate`
   regenerates the console's client from the contract, and without the console's packages it
   stops at `openapi-typescript`. The ignored files of Step 2 are linked into the lane the same
   way. A lane that continues keeps both.
4. **Launch the lanes**, all of them in one message, each a subagent (the Agent tool,
   `general-purpose`, `name` the lane's name, in the background) with the prompt of
   [`references/task.md`](references/task.md), every placeholder substituted; `WAVE` lists every
   task of the wave. Then wait for all of them. This session reads no code, fixes nothing and
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
5. **Read what came back**, lane by lane, as each ends: the lane's plan copy and the journal
   lines it appended.
   - Every checkbox of the task is `[x]`: say "Task N done" in one line; the lane has logged
     the details.
   - `[blocker] environment task N` in the journal and no `⚠️` of another kind: when every
     other lane of the wave has ended, resume this lane once by its name, with the SendMessage
     tool and the words «rerun now»; the tool is deferred in a fresh session and is loaded
     with ToolSearch first. Read it again when it ends. Still red: the lane stopped, as below.
   - A `⚠️` on a checkbox, or an `[owner]` or `[blocker]` line of another kind: the lane
     stopped. Its worktree and branch stay. The wave goes on without it.
   - Open checkboxes and no `⚠️`: one retry, a fresh subagent on the same lane, the same
     worktree and branch, not a clean worktree cut again, with the errors of the first attempt in `RETRY`, its report and the
     journal lines it wrote. One retry, not two. Still open: the lane stopped, and this session
     logs `[blocker] task N: <what the two attempts left>`.
6. **Integrate.** When every lane of the wave has ended, spawn one subagent (the Agent tool,
   `general-purpose`) with the prompt of [`references/integrate.md`](references/integrate.md),
   every placeholder substituted: `LANES` names only the lanes whose task is closed, in the
   order the Shared files table of the plan gives, the lane that is second after the one that
   is first, the rest in file order; `STOPPED` names the lanes that stopped. Wait for it. Read
   the journal lines it appended:
   - `wave N: integrated` and no `[owner]` or `[blocker]` line: remove the integrated lanes,
     `git worktree remove .claude/worktrees/<slug>-task-<N>` and
     `git branch -D <slug>-task-<N>` from the main checkout, for the integrated lanes only,
     then the lint cache of each, `rm -rf .exec-plan/<slug>/cache/lint/<slug>-task-<N>`, and
     the Go build cache of the run, `rm -rf .exec-plan/<slug>/cache/go-build`. Go compiles the
     module's packages again under the path of every worktree, about a third of a gigabyte a
     lane, and nothing reads those entries once the lane is gone. No lane builds at this
     moment, and the next wave starts with a cold build, about half a minute. The lint cache
     of the run's checkout stays. Then, when no lane of the wave stopped, the next pass of
     the loop; when one did, the report of Step 4, after the integration and not before it.
     The review and the finalize do not run after such a stop.
   - A red check the integrator could not make green: one retry of the integrator with `RETRY`,
     as for a lane. An `[owner]` line, a `[blocker] environment integration N` line, or a
     merge it could not resolve: a stop with the report of Step 4. Nothing of the wave is integrated twice: the integrator's own journal line says
     how far it got, and the lanes it merged have their ticks in the run's checkout.

Nothing is asked between waves. A lane that cannot close an item leaves it open with its
reason, and the owner reads the reason in the report, not a question mid-run.

**The whole tree.** A lane checks only what it touched: `go build ./...` and the tests of the
packages it changed, the related console specs, the generators and the docs check when it
moved them. An integrator builds and lints the whole tree and runs the tests only of a surface
two lanes of its wave changed, since a surface one lane changed was tested by that lane. Once every task is closed, the whole tree is checked once, before the first review
round, by an executor like the lanes' and not by the finalize: what goes red there is fixed by
the run, and the fix is reviewed with the rest of the branch. Spawn one subagent (the Agent
tool, `general-purpose`) with the prompt of [`references/check.md`](references/check.md), every
placeholder substituted, and wait for it. It runs `make generate-check`, the docs check,
`make build`, `make lint` and `make test` from the root, every component whatever the branch
touched, and fixes and commits until they are green. Read what came back:

- `whole tree: green` in the journal and no `[owner]` or `[blocker]` line: say so in one line
  and go to the review. A `[deviation] … red at the base as well` line beside it is a failure
  the branch did not cause (root `CLAUDE.md`, Gates): the run goes on, and the line goes into
  `open:` of the run report.
- an `[owner]` or `[blocker]` line: stop with the report of Step 4. The review and the finalize
  do not run.
- neither: one retry, a fresh subagent with the errors of the first attempt in `RETRY`. Still
  not green after it: this session logs `[blocker] whole tree: <what the two attempts left>`
  and stops the same way.

Log the start with `scripts/progress.sh <slug> "whole tree: started"`. A continuation with every
task closed runs it again: it is the one state of the run no checkbox records.

## Step 4: the stop report

In chat, no file. A stop in Step 3, 5 or 6 ends on it:

```
stopped at: wave N: <tasks> | integration of wave N | whole tree | review round <run>, <profile> | finalize, <regroup | close>
open:       <the checkboxes left open, each with its ⚠️ reason | the findings left, each with
            its sort | the gate that is red>
lanes:      <each lane worktree that still exists: its task, its branch @ <sha>, why it stopped>
journal:    <every [owner] and [blocker] line, verbatim>
logged:     <every [decision] and [deviation] line, verbatim>
branch:     <branch> @ <sha>, base <sha>, <worktree path>
next:       <what the owner decides | for a [blocker] environment line, what on the host to
            repair>; an answer that changes the plan goes into the copy in
            the run's checkout, <checkout>/docs/plans/<file>, committed there through
            `commit.sh`; then `/exec-plan <plan>` continues: the stopped lanes are brought
            onto the run's branch and rerun, and the loop goes on from the ready set, or from
            the whole-tree check when every task is closed
```

The plan the run reads is the copy in the run's checkout, and that is where an answer to an
`[owner]` or a `[blocker]` line that changes the plan lands: an edit to
`<checkout>/docs/plans/<file>`, committed through `commit.sh`, then the run continues. A plan
refreshed on `master` through `/make-plan <plan>` instead never reaches the branch, because
`master` is not merged into it: for that, remove the worktree, the lane worktrees, the branches
and the journal `.exec-plan/<slug>/`, and start the run again from the refreshed commit.

## Step 5: review rounds

Every task is closed. The branch from `base` now goes through revmux rounds until one is
clean or three have run: `comprehensive` first, `final` on the fixes of each round after it,
and `claude-only` for every round when Step 1 found no `codex`.
The three are counted over the whole run, by the round directories under the task in the main
checkout's `.revmux/tasks/<slug>/`, not per session. `comprehensive` runs once on a branch: it
is the round with both models and every lens, and a second one reads a diff that was already
read. Load the `revmux:revmux` skill and follow it, with what a run changes:

- The subject is the branch: `git diff <base>...HEAD` in the run's checkout, the whole range in
  every round. The lanes are already in it, and no lane worktree exists by now. `scope.md`
  carries that range, says to read the plan at its path in full before the diff, and on a round
  after the first names the fix commits since the previous round. `goal.md` is the plan's Goal
  in two lines and the criteria: every task's `Result:` holds, nothing under `## Out of Scope`
  moved, the root `CLAUDE.md` rules hold. On a `final` round it is the merge gate, as the revmux
  skill asks of the last round before a merge: the round answers whether anything in the branch
  should not ship, and finding nothing is a valid answer. `profile.md` names the root
  `CLAUDE.md`, the `CLAUDE.md` of each surface the branch touches and the plan's `## Decisions`
  as where the rules live, and says a Decision is settled: that the branch does what a Decision
  says is not a finding, and that a Decision is wrong is an open question.
- The task id is the slug, whatever the branch is called. The plan's own review ran under
  `plan-<slug>` and is another subject; the two are never joined. The rounds are
  `NN-initial`, `NN-after-fix` and `NN-final`, `NN` one past the highest round already under
  the task.
- Rounds run from the main checkout with `--workdir <run's checkout>`, headless
  (`--no-tui`), in the background: the project layer,
  `.revmux/prompts/` and `.revmux/lenses/`, is read from the process working directory, and
  the archive lands in the main checkout's `.revmux/tasks/`. `revmux new` runs from there
  too. The round's command starts with `caffeinate -i`: Claude Code keeps the host awake
  while a subagent runs and drops that hold while a background shell is all that runs, so a
  host on battery sleeps in the middle of a round.
- The revmux skill's questions are not asked, and its loop is not entered: headless is
  settled, the fixer below decides what is fixed, and this step is the loop.

**A continuation.** When the task already holds a round, the review does not start over. The
last round stopped on an `[owner]` line, and the plan copy now holds the answer, or on a
`[blocker] environment` line, and the owner has repaired the host: give the
fixer the findings of that round again, `findings.json` in its directory, then run `final` on
the commits it makes. With three rounds already under the task, the fixer runs and no round
follows.

Read the result in this order; the first line that applies decides:

1. The exit code. `0` and `1` are finished rounds. `2` is a failed one: read the stderr log.
   When the round directory holds `findings.json`, the round finished and only its write to
   stdout failed; read the findings there. Otherwise stop with the report of Step 4. A failed
   round is not evidence; the finalize and the close do not run.
2. `sources.degraded`. Non-empty, or `sources.expected` not equal to `sources.reported`: stop
   with the report of Step 4. A partial round says nothing about the branch, and its silence
   is not a clean round; the finalize and the close do not run.
3. `findings`. No `critical` and no `major`: the round is clean. With no `minor` either, log
   it and go to Step 6. With a `minor`, the fixer runs once more, in its minor pass, and Step 6
   follows it with no round after: a round over the fixes of minors brings about as many new
   minors as it closes, so a loop on them never ends. Otherwise the fixer, then the next
   round. After the third round no fixer runs and no round follows, unless the third is clean
   and holds minors, which get the minor pass like any clean round: what the third round
   leaves goes into the run report as open findings, and Step 6 runs.

Log every round with `scripts/progress.sh <slug> "review round <run>: <profile>, <n>
critical, <n> major, <n> minor, degraded <none | names>, <clean | clean, minor pass | fixer
| stop>"`.

**The fixer.** One subagent (the Agent tool, `general-purpose`) with the prompt of
[`references/fixer.md`](references/fixer.md), every placeholder substituted, and wait for
it. It sorts every finding into fact, fork or noise: a fact is fixed, gated and committed
through `commit.sh`; a fork is logged as `[owner]` with the question in plain words; noise
is dropped with its reason in the journal. This session fixes nothing itself. Read what came
back, the journal lines it appended and its report:

- an `[owner]` or `[blocker]` line: stop with the report of Step 4, the same stop as after a
  wave. The finalize and the close do not run, and the branch waits on the owner's answer;
  `/exec-plan <plan>` after it continues the review as "A continuation" above says.
- no commit, because every finding was noise or an answered question: no round follows. A
  round on an unchanged diff reads the same diff again. The dropped findings go into the run
  report with their reasons, and Step 6 runs.
- after the minor pass: Step 6, whatever was committed. The minors it left go into the run
  report as open, each with its reason or its question. The minor pass logs no `[owner]` and
  no `[blocker]`, because a minor does not hold the branch.
- otherwise: the next round, on the fixes.

## Step 6: finalize

One subagent (the Agent tool, `general-purpose`) with the prompt of
[`references/finalize.md`](references/finalize.md), every placeholder substituted, and wait
for it. It regroups the history from `base` behind a `backup/` branch and proves the tree did
not move, moves the plan into `docs/plans/completed/` and reports. It runs no gate, not the usual last check on the final tip: the whole
tree was checked before the review, and the regroup leaves the tree byte for byte as it was.
This session does none of that itself. A `[blocker]` line from it, or a diff against the
backup that is not empty: stop with the report of Step 4. The history stays as the subagent
left it, the backup branch holds the tip, and the plan stays under `docs/plans/`.

**Clean up after the run.** Before the report, from the main checkout, remove what the run
left on the disk and nothing it did not make:

- a stack the run's lanes raised that was down when Step 1 looked: `make -C deploy e2e-down`
  or `e2e-fed-down`, which remove its volumes. A stack that was up before the run is another
  session's and stays. `compose-down` is never run here: it takes down every stack out of the
  compose file, the stand of another checkout included;
- the scratch worktrees of the base and tip checks, when one is left;
- `docker image prune -f`: every rebuild of the stand's images left the old layers dangling;
- the run's caches, `rm -rf .exec-plan/<slug>/cache`.

The report's `whole tree:` line is followed by what was freed, `df -k` before and after.

Then run `scripts/audit.py <slug>` from the main checkout. Its count goes into the report's
`audit:` line, and its findings follow that line as they were printed, up to twenty; past
that, the count per rule.

Then the run report, in chat, no file:

```
run:       <branch> @ <sha>, base <sha>, <worktree path>
tasks:     <n>, all closed, in <m> waves
review:    <n> rounds (<run>: <profile>, ...); <n> fixed, <n> dropped, <n> open
history:   <n> commits → <m> commits, backup/<slug>-<stamp>
whole tree: green, <n> fixes | <the checks and their result>
plan:      docs/plans/completed/<file>
audit:     <n> findings in <n> commands of <n> agents | no transcript found
logged:    <every [decision] and [deviation] line, verbatim>
open:      <every finding not fixed: a minor left, a finding dropped and why, an open
            question and where the plan answers it, a finding of the third round; every check
            red at the base as well; every ADR a lane or a fixer set to `Proposed`, waiting
            for the owner to accept it>
next:      revdiff | `/ship <branch>`, revdiff is not installed
```

**revdiff.** The owner is back, and from here questions are allowed again. When `revdiff` is
on `PATH`, load the `revdiff:revdiff` skill and open it from the run's checkout on the whole
branch, `<base>...HEAD`: not the last commit, not the working tree. When it closes, read the
annotations by the refs of this run, never by the newest history file: parallel reviews of
other branches write there too. Every annotation gets one line in the reply,
`<file>:<line> <the comment, shortened> -> answered | fixed in <sha> | disagree: <why>`. A
question is answered and changes nothing. A change is made by this session, gated, and
committed through `commit.sh` on top of the regrouped history, as `fix(<scope>): ...` or
`docs(<scope>): ...`. An annotation that is unclear is quoted back with two readings. None is
skipped, and none becomes a backlog item, a plan or an ADR unless it says so. No annotations:
say so and name the history file that was read. Reopen revdiff on the fixes only when the
owner asks. A gate run here builds the run's caches again: remove them once more after the
last fix. End on one line: the count of annotations, how many were fixed, answered and
disagreed with, and that `/ship <branch>` is next. Without `revdiff`, the run report is the
end and `/ship <branch>` is the owner's next step.

## Common mistakes

| Mistake | Fix |
|---|---|
| Cut the worktree before the premises were rechecked | Premises, Owner Sign-off, waves, go, then the cut; a false premise leaves nothing to remove |
| Took a branch `<type>/<slug>` or a worktree for a continuation | `.exec-plan/<slug>/base` says a run exists; without it, the question of Step 1 |
| Cut the worktree from `master` as it stood after the go, or attached a branch `<type>/<slug>` as it stood | From the `master` commit the premises were checked on; a branch `<type>/<slug>` on any other commit is a stop |
| Sent a mid-run answer through `/make-plan` on `master` | The copy in the run's checkout, through `commit.sh`; a refresh on `master` restarts the run |
| Cut the branch from `origin/master` | From the recorded local `master` commit, plan commit included; `/ship` brings origin |
| Merged or fast-forwarded `master` in the main checkout | Never; other sessions stand there. Count, ask, then cut |
| Wrote git commands for the three scripted operations | `commit.sh`, `base.sh`, `progress.sh` |
| Ran `git rm` or `git mv` before `commit.sh` | `rm` or `mv`; the script stages a path gone from the tree as its removal |
| Ran the tasks one after another because the plan has `After:` lines | Every task whose `After:` is met runs in the same wave |
| Took the plan's file order as the order of execution | The ready set; file order only breaks a tie for `Needs:` |
| Cut a lane from `master` or from the previous wave's tip | From the run branch's `HEAD` at the start of the wave |
| Cut a second worktree for a stopped lane | Its worktree exists; merge the run's branch into it and rerun |
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
| Ticked the main checkout's plan from a worktree | Only the copy in a lane's worktree, brought to the run's checkout by the integrator |
| Wrote the report to a file | The report is in chat; the journal is the file |
| Ran `make test` in every lane or integration, or not at all | A lane tests what it touched, an integrator what its wave touched; `make test` runs once, in the whole-tree check after the last wave |
| Left a red whole tree to the finalize | The check's own subagent fixes it; the finalize runs no gate |
| Took a failed or degraded round as clean | Exit code, then `sources.degraded`, then the findings; a partial round stops the run |
| Ran revmux from the worktree | From the main checkout with `--workdir`; the project layer is read from the process directory |
| Fixed a finding in this session | The fixer subagent, one per round; it sorts before it fixes |
| Ran a fourth round, or one on an unchanged diff | Three at most over the whole run; what the third leaves, and what a fixer dropped, goes to the report |
| Ran `comprehensive` again after the owner answered a finding | The fixer on the last round's findings, then `final` on its commits |
| Passed a `model` to a subagent | None; every subagent runs on the session's model |
| Ran `compose-down`, removed an image by name or a named volume to free space | Only what the run made: its e2e stack, dangling layers, its own caches |
| Ran `go clean -cache` or `golangci-lint cache clean` | Those clear the caches every session on the host shares; the run removes `.exec-plan/<slug>/cache` |
| Built, tested or linted Go without `. scripts/cache.sh` in the same shell call | The command writes into the shared caches, and the lint leaves there the paths of a worktree that will be gone |
| Went to the finalize from a clean round with simple minors left open | The minor pass: one fixer run over the minors, then Step 6 with no round after it |
| Ran another round on the fixes of the minor pass | None; minors arrive at about three a round, and a loop on them does not end |
| Regrouped without the backup, or with `--soft` | `backup/` at the tip, `git reset <base>`, groups through `commit.sh`, an empty diff |
| Merged `master` into the branch at finalize | Never here; `/ship` brings the branch onto `master` |
| Read the newest revdiff history file | By the refs of this run; other reviews write there too |
| Opened revdiff on the last commit | The whole branch, `<base>...HEAD` |
| Cut lanes or ran `comprehensive` for a plan whose Execution says light | One executor in the run's checkout, the light check, two rounds at most on the lens set |
| Moved a light run onto the full path when the executor outgrew it | Stop with the report of Step 4; the owner decides |
