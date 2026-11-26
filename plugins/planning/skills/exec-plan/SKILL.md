---
name: exec-plan
description: >
  Use when a plan `/planning:make-plan` wrote is to be run, or a run of one continued. The skill
  starts a branch in every repository the plan names and runs every task whose `After:` is met
  as a lane in its own worktree. It integrates each wave through one subagent and checks the
  whole tree of each repository once after the last wave. Then it reviews each branch, regroups
  its history and closes the plan. A plan marked light runs with one executor, a
  narrower check and one review agent. With `peer` after the path, a second agent in the
  split pane reads the plan before the go and every wave after it is integrated. Not for a
  mechanical edit one session makes in place.
user-invocable: true
disable-model-invocation: true
---

# Run a plan

This skill takes a plan in the form of
[`make-plan/references/form.md`](../make-plan/references/form.md) to a closed plan. On the way
it makes a branch in every repository the plan names, runs the tasks in waves of parallel lanes
and keeps one journal. Then come the review rounds, the regroup of the history, the move to the
closed-plans directory and the owner's revdiff. The argument is the path of the plan. A path
that does not exist is the first stop. A plan that already sits in the closed-plans directory
is such a path.

A run may have a peer: a second agent in the split pane of the same agterm session. The peer
reads the plan before the go. It reads every wave after the wave is integrated, while the next
wave runs, and keeps the notes the later lanes get. A run with a peer is a trial, and its
report says what the peer found. The owner says who the peer is after the path: `peer` or
`peer claude`, `peer codex`, `no peer`. Or the owner answers when Step 1 asks. Read
[`references/with-peer.md`](references/with-peer.md) with the Read tool before the rest of
Step 1 in two cases: a run with a peer, and the continuation of a run whose journal holds
`review/`. That file adds to the steps below and changes none of them. A run without a peer is plain and does not read that file.

A wave is every open task whose `After:` tasks are closed. Each task of a wave runs as a lane: a
subagent in its own worktree on its own branch in its task's repository. The lanes of a wave
run at the same time. When every lane of the wave has ended, one integrator subagent merges the
lanes that ticked every checkbox of their task into the run's branch of their repository. The
next wave starts from the new tips of the run branches. A plan with no `After:` line
runs every task in the first wave. A plan whose `## Execution` carries the Mode line
`light` runs as "A light run" below says.

## The project rules

Load them once, at the start of Step 1, before the question about the peer:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh
```

The script prints the project's rules file, with its path on the first line as
`<!-- rules: <path> -->`, or it prints nothing.
[`../../references/rules.md`](../../references/rules.md) lists the sections, and the default
each section takes when the file is absent or leaves the section out. The script looks from
the checkout it runs in and from each directory above it. So in a plan of several
repositories, run it once more from the main checkout of each repository. When one of these
runs finds another file, the `Trunk`, `Gates` and `Environment` of that repository come from
its own file. This skill reads:

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
subagent, the peer and a script get no plugin variables. So every prompt under `references/`
names the plugin's files through placeholders. The lead substitutes absolute paths when it
builds the prompt: `SCRIPTS` is `${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts` and `RULES`
is `${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh`, each expanded to the absolute path. The same holds
for a command this file shows as `scripts/<name>`: the command runs as
`${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts/<name>`. A subagent runs `bash RULES` from its
checkout and reads the sections its prompt names.

Every script reads the run's journal from the variable `EXEC_PLAN_JOURNAL`, the journal's
absolute path. A script refuses with one line when the variable is unset or not absolute. No
script finds the journal by itself. This session sets the variable for every call:
`EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh '<line>'`. Every prompt under `references/`
gets the path as the placeholder `JOURNAL` and sets the variable the same way. The line given
to `progress.sh` goes in single quotes, and a single quote inside that line is written as
`'\''`. In double quotes, a backtick or a `$(…)` in the line runs as a command. A placeholder
is replaced only where it stands as a whole word: `EXEC_PLAN_JOURNAL` is the variable's name,
not `PLAN` or `JOURNAL`, and stays as written.

Three operations are scripts under `scripts/`, and this file never spells out their git
commands:

- `scripts/commit.sh <message> <path>...` stages the named paths in the checkout it runs in
  and refuses an index that holds anything else. It commits without a pathspec, so the hooks
  run on the real index and a file a pre-commit hook stages lands in the commit. A tracked path
  gone from the tree is staged as its removal. So a file is deleted with `rm` and moved with
  `mv`, never with `git rm` or `git mv`. Those two commands take the path out of the index
  before the script can name it, and the script fails;
- `scripts/base.sh <repo> <trunk>` is run from inside that repository's run worktree. It computes the
  base commit of the repository and records it as `base.<repo>` in the journal, or checks the
  one recorded;
- `scripts/progress.sh <line>` appends one timestamped line to the journal.

Each script exits non-zero with one line of reason on a refusal. A refusal is a stop: the line
goes into the report, and nothing is tried around it.

A fourth file there is sourced, not run, and it matters when the project builds Go.
`. scripts/cache.sh` sets `GOCACHE` and `GOLANGCI_LINT_CACHE` to the run's own caches for the
commands that follow in the same shell call. The next call sources it again. Every command of
a run that builds, tests or lints Go starts by sourcing `cache.sh`, in a subagent and in this
session alike: `EXEC_PLAN_JOURNAL=<journal> . scripts/cache.sh && make lint`. `commit.sh`
sources `cache.sh` itself, for the pre-commit hooks, so `commit.sh` gets the variable too. A
project with no Go never runs a command `cache.sh` covers. Sourcing `cache.sh` there changes
nothing.

`EXEC_PLAN_JOURNAL=<journal> scripts/audit.py` reads the run back. Claude Code keeps the
transcript of every subagent. The script lists the shell commands in those transcripts that
break a rule of the prompts: Go built outside the run's caches, a commit made around
`commit.sh`, a bypassed hook. A finding is a place to look, not a verdict, and it changes
nothing in the run. A finding tells the owner which line of a prompt an agent did not follow.

`EXEC_PLAN_JOURNAL=<journal> scripts/status.py [--open | --watch]` draws the run as one page,
`<journal>/status.html`. The page shows the
phase; this session and the peer of a run that has one, with their turns, their tokens and
the mail between them; every wave with its tasks and its integrator under it, each with its
time, model, context, turns and tokens in and out; the waves still ahead, as the `After` chains
of the open tasks allow them at the earliest; the whole-tree check with the gates it
ran; the review rounds; and the stops nobody has answered. The script reads everything from
the journal: the plan through `plan` and the line `finalize: plan closed, <path>`, the repositories
through `repos`, the ticks of a running lane from its progress file, and the ticks of a closed
task from the plan. The times, the turns, the tokens
and the steps come from the transcripts Claude Code keeps: one of every subagent, one of this
session, whose id the script records in `<journal>/lead`, and one of the peer. `progress.sh`
runs `status.py` after a line that changes what the page shows, so nobody calls `status.py` by
hand. In an agterm session, the line that starts or continues a run opens the page as a
companion row under the session. That line also starts one watcher for the run,
`status.py --watch`, which redraws every ten seconds. So the tokens and the checkboxes of a
working lane move between journal lines. The watcher ends when the run stops or closes, and
when its page is gone. The open page pulls `status.js`, written beside the page, every five
seconds and replaces its content in place. So the page is never reloaded and keeps the
reader's scroll position. The page is a view of the journal, the plan, the lanes' progress
files and the transcripts. The run reads nothing from the page, and a page that cannot be
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
  `Where:`. `<dir>` is the repository's directory relative to the session's working directory.
  The task's `Where:` paths are relative to that repository. A task without the line belongs to the home
  repository, the one whose checkout holds the plan file. A plan outside every git checkout has
  no home repository, and each of its tasks names its own. `<repo>` below is the repository's
  directory name. The repositories of the plan are the ones its tasks name and, for a tracked
  plan, the home repository, which holds the plan's commits. A plan of several repositories runs
  in a session whose working directory holds all of them.
- **The plan's mode.** The place of the plan decides the mode, by the same test make-plan uses.
  A plan in a repository's work tree that git does not ignore (`git -C <the plan's directory>
  check-ignore -q <plan>` exits 1) is tracked. A tracked plan must be committed before a run
  starts, because the run's worktree is cut from a commit: Step 1 checks it. A tracked plan is read,
  ticked and closed in the copy in the home repository's run worktree. Every change to that
  copy is a commit there through `commit.sh`. Any other plan, outside git or in a directory git
  ignores, is untracked. An untracked plan is read, ticked and closed at its own path, and
  nothing of it is ever committed. "The plan" below is that one file. Its absolute path is
  `PLAN` in every prompt. Nobody edits the copy of a tracked plan in a main checkout.
- **The journal** is one directory per run, `<journal>` below. For a tracked plan it is
  `.exec-plan/<slug>/` in the main checkout of the home repository, the first entry of
  `git worktree list`. For an untracked plan it is `.exec-plan/<slug>/` in the plan's
  directory. The journal is not a run block committed in the plan. It holds:
  - `progress.md`, the log;
  - `plan`, one line: the plan's absolute path as the run reads it, the copy in the home
    repository's run worktree or the untracked file;
  - `repos`, one line per repository of the plan:
    `<repo> <main checkout> <run worktree> <branch>`, absolute paths, written in Step 1 after
    the branches are cut;
  - `base.<repo>`, the base commit of each repository, written by `base.sh`;
  - `trunk.<repo>`, the name of each repository's trunk, and `stands`, the stands a task's
    `Needs:` names that were down when Step 1 looked, one per line, empty when none was, both
    written in Step 1;
    `preflight`, the block of Step 2. A continuation reads the three here, since the session
    that found them is gone;
  - `lanes/task-<N>.md`, a lane's progress file: the plan's `### Task N:` section, which this
    session copies there before the lane starts. The lane ticks `[x]` and appends
    ` ⚠️ <reason>` there and never edits the plan;
  - `lead`, `status.html` and `status.js`, the status page's own files, and `review/` in a run
    with a peer.

  The project's `.gitignore` lists `.exec-plan/` and `.claude/worktrees/`. Where the
  `.gitignore` does not list them, both show as untracked in the main checkout, and nothing of
  the run stages them.
- **Per repository.** The run's branch, `<branch>` below, has one name in every repository of
  the plan, named as Step 1 says. Its checkout, the run worktree, is
  `.claude/worktrees/<slug>` in the repository's main checkout. The trunk is never run on, and
  neither is a branch another checkout stands on. Each repository has its own trunk, its own
  `base.<repo>`, its own lane worktrees and its own lint caches.
- The run builds into its own caches, `<journal>/cache/`, and the `Environment`
  section may name more of them there. For Go: `go-build/` is one Go build
  cache for every checkout of the run, in every repository, so a dependency is compiled once.
  `lint/<repo>/<the checkout's directory name>/` is a golangci-lint cache per checkout, `<repo>`
  the directory name of the repository's main checkout. A golangci-lint cache keeps the
  absolute path of every file it read, and an entry of a worktree that is gone comes back as an
  issue no exclusion matches. Nobody else builds into the run's caches, so the run deletes them
  without asking who is building. A cold build costs the next wave one compile, which is
  cheaper than a cache that grows by a copy of the tree per lane. The Go build cache goes after
  every wave, a lane's lint cache with the lane, and the rest when the run ends. A stop leaves
  what is there for the continuation. Downloaded modules stay in the shared `GOMODCACHE`.
- A lane is named after its task: the branch `<slug>-task-<N>`, the worktree
  `.claude/worktrees/<slug>-task-<N>` in the main checkout of its task's repository, the
  progress file `<journal>/lanes/task-<N>.md`, and the subagent's name the same string as the
  branch. A subagent's name longer than 64 characters is cut to its last 64 characters: the
  Agent tool takes no longer name.
  The lane's branch is cut from the tip of its repository's run branch at the start of its wave.
  A lane's branch is local and removed after its wave, so it keeps the bare slug.
- The state of a run is the plan's checkboxes, the lanes' progress files, the `base.<repo>` of
  each repository, and the lane worktrees that exist, nothing more: no phase marker, no lock, no
  dirty-tree check. A task is closed when every checkbox of its section is `[x]` in the plan.
  That happens only after its lane was integrated. A lane worktree that exists for an open task is a lane that stopped: its
  branch holds what it committed, and its progress file what it ticked.
- A `base.<repo>` file in the journal is also what says a run exists: Step 1 then continues it.
- The trunk of a repository is the branch the `Trunk` section names, resolved once per
  repository in Step 1 and named `<trunk>` below. With no `Trunk` section it is the branch
  `origin/HEAD` of that repository points at, else `main`, else `master`.
- The integrator of the wave carries the marks of each lane's progress file into the plan. The
  checkbox lines of each lane's task take the state its progress file holds, for a lane the
  integrator merged and for a lane that stopped alike. Only the merged lanes' code reaches the
  run's branches. The owner's answer to a stop goes where Step 4 says. Nobody else edits the
  plan.
- The run is one session. Between the go of Step 1 and a report, the run asks the owner
  nothing, and this session reads no code, fixes nothing, merges nothing, runs no gate, regroups nothing
  and closes no plan itself: a subagent does. The one merge it makes is the run branch into a stopped lane, which
  [`continuation.md`](references/continuation.md) describes. The run ends on the run report,
  or on the stop report of Step 4 when it meets an owner's judgement or an environment it
  cannot repair. A stop is an ordinary end of a session:
  `/planning:exec-plan <plan>` continues the run.
- No Agent call of the run names a `model`: every subagent runs on the model of this session.

## A light run

A plan whose `## Execution` carries `- **Mode.** light — <reason>` runs with one executor, a
narrower check and at most two review rounds, and with no peer. Read
[`references/light-run.md`](references/light-run.md) with the Read tool before the peer
question of Step 1 when the plan carries that line. That file changes Step 1, Step 2, Step 3,
the whole-tree check, Step 5 and Step 6, and the rest of this file holds. A plan without the
line does not read it.

## Step 1: where the run happens

The only step with questions. After the question about the peer, the order of this step is the
point. The premises are rechecked in every repository, the environment is checked and the go
is given before a branch, a worktree or a base exists in any of them. So a plan that fails the
recheck goes back to `/planning:make-plan` with nothing to remove. And what the run would stop
on an hour later is said before the run starts.

**The journal.** Find the plan's mode and the journal's place as "Names and state" says.

**Continuation.** The run is continuing when the journal holds a `base.<repo>` file. Nothing
else says so: a branch `<branch>` or a worktree without one is a first run, a checkout the
owner made by hand included. On a continuation, read
[`references/continuation.md`](references/continuation.md) with the Read tool now, before the
peer question. It says what Step 1, Step 3 and Step 5 do on a continuation, a light run's
included, and the rest of this file holds. A first run does not read it.

**The peer.** The peer question is the first question of a new run. It is not asked when the
request already answers it or outside agterm, where no peer can run. Read "The peer question"
in [`../../references/questions.md`](../../references/questions.md) with the Read tool before
you ask it: it holds the three answers, their costs and the form of the question.
Here a Claude Code peer reads the plan and every wave, and the status page does not count the
tokens of a Codex peer.

A continuation asks nothing: the journal says whether the run has a peer.

**The repositories.** Read every task's `Repo:` line and list the repositories of the plan as
"Names and state" defines them. The home repository is found from the plan's path: the
repository whose checkout holds the plan file, its main checkout the first entry of its
`git worktree list`. A plan with no `Repo:` line has that one repository, and the session runs
wherever it runs today. A repository a `Repo:` line names must be the main checkout of a git
repository at `<the session's working directory>/<repo>`. A repository that is not there is a
stop that names it. The session runs from a directory that holds every repository of the plan,
and the owner starts the session again from there. A plan outside git whose task has no
`Repo:` line is the same stop, and the plan goes back through `/planning:make-plan <plan>`. Resolve the
trunk of each repository here, from its rules as "The project rules" says.

**The plan is committed.** For a tracked plan,
`git -C <the plan's directory> ls-files --error-unmatch <plan>` must succeed, and the plan file must exist at the local `<trunk>` of the home repository. For every
repository of the plan, the commit its `<trunk>` stands on,
`git -C <main checkout> rev-parse <trunk>`, is kept in the session and in no file. A tracked
plan is read at the home repository's commit. The anchors run in each main checkout as it
stands at its repository's commit. Each branch is cut from its repository's commit. So a trunk that moves
while the owner reads changes nothing the run stands on. When a tracked plan is not committed,
stop and say that the plan is not committed. The commit item of `/planning:make-plan` is how
the plan gets committed. When the plan is committed but not at the local `<trunk>`, stop and
say that. Name the branch it is committed on, the one the plan's checkout stands on
(`git -C <the plan's directory> branch --show-current`). Name also what the owner does: merge
that branch into the trunk, or start the run from a plan committed at the trunk. The commit
item cannot do this, since it commits on that same branch. An untracked plan is read from its file
and has no commit to check.

**Behind origin.** For each repository that has a remote `origin`: `git fetch origin`, then
count how far the local `<trunk>` is behind `origin/<trunk>`. Behind by anything: say by how
many commits and in which repository. The go below is then the answer to whether the run goes
on with the local trunks as they are. Each branch is cut from its recorded commit, the plan's
commit on the home one. The freshness against `origin` is the pull request's job, after the
run.

**Premises, Owner Sign-off, waves, go.** Read the plan as the paragraph above says, with each
anchor run in the main checkout of the repository it names, at that repository's recorded
commit. Run every anchor in `## Premises` the way the refresh mode of
[`make-plan`](../make-plan/SKILL.md) does, and report each as in place, moved, or false. A
moved anchor is reported and the run goes on. A false premise is a fork for the owner. It
stops the start with no branch, no worktree and no journal made in any repository. The plan
goes back through `/planning:make-plan <plan>`, and `/planning:exec-plan <plan>` starts again
from the plan. Then show `## Owner Sign-off` as it is written. Every line there is settled,
and the run does not reopen it. A subagent that meets an owner's judgement not written there
stops the run. Then print the waves. Read every task's `After:` and `Needs:`, and list wave by
wave which tasks run together, each with its repository and the reason its `After:` gives. An `After:`
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
  stop. Say which stand is up. The owner's go decides whether the run starts beside it;
- disk: the free space of each volume that holds a main checkout of the plan (`df -k`) and, on
  a host that runs Docker, what Docker holds (`docker system df`). A lane is one more copy of
  its repository's checkout, plus the packages the `Environment` section installs for the
  surfaces its `Where:` names. When free space is below two copies per lane of the widest wave,
  the run cleans before it stops: what can be rebuilt and nobody else holds. The caches a
  stopped run of this plan left, `rm -rf <journal>/cache`, then `docker image prune -f` and
  `docker builder prune -f`. Never a build cache the host shares, an image by name, a
  named volume or a stand: those are other sessions' work. Measure again. Still below: a stop
  before the go, with the numbers;
- a barrier `## Execution` names: an open plan whose merge this one waits for;
- in every repository, a branch `<branch>` or a worktree `.claude/worktrees/<slug>` that
  already exists: it stands on that repository's recorded commit, or it is the stop that
  "Worktrees" below names. This check runs in every repository before the go, so the cut never
  stops halfway.

The same message names the branch the run will cut in every repository, `<branch>`, and the
trunk and the recorded commit of each. The name follows the `Trunk` section. By default it is
`<type>/<slug>`, its type the commit type the plan's Goal reads as: `feat` for new behaviour,
`fix` for a defect, `refactor`, `docs` or `chore` when nothing a user sees changes.

Then wait for the owner's go. The go confirms the schedule, the branch and what the
environment check said.

**Worktrees.** On the go, in every repository of the plan, from its main checkout, `<sha>`
being that repository's recorded trunk commit:

```bash
git worktree add .claude/worktrees/<slug> -b <branch> <sha>
```

Each branch starts from the tree the premises were checked on, wherever the trunk stands by
then. A branch `<branch>` that already exists without a worktree gets the worktree without `-b`
when `git rev-parse <branch>` is `<sha>`. On any other commit, the start is a stop. Such a
branch was made outside the skill and holds commits the premises never saw, and the owner
deletes or renames it. A worktree already at `.claude/worktrees/<slug>` is taken by the same rule, its
`HEAD` at `<sha>` or the same stop. A main checkout is not touched beyond that: no merge
into the trunk, no checkout, nothing that moves what the other sessions there stand on.
What a fresh worktree needs is Step 2.

Then write the journal's `repos`, `plan`, `trunk.<repo>` for each repository, and `stands`, in
the forms "Names and state" gives.

**Base.** In every repository of `repos`, run `EXEC_PLAN_JOURNAL=<journal> scripts/base.sh
<repo> <trunk>` from its run worktree. The script records `<journal>/base.<repo>`, the trunk
commit the branch was cut from, or checks the one recorded. The script refuses a merge commit
between the base and `HEAD`, and a recorded base the tree no longer matches: a branch rebased
or merged by hand since the run started. The review range, the regroup and the revdiff of the
repository all start at the base commit, so the refusal is the stop and its line is the
reason. On a continuation a
repository of `repos` without its `base.<repo>` gets it recorded here: its branch has not moved
since the cut.

Then log the run with `EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh 'run started: <plan>,
<repositories>, base <repo> <sha>, ...'`, or `run continued` when the journal already holds
a base.

## Step 2: preflight, once

Once per run, before the first wave: what only a worktree can be given, in each repository of
the plan. The result of this step goes into the prompt of every lane and of every integrator as
the `PREFLIGHT` block.

- **The worktree's own environment**: what the `Environment` section of each repository asks a
  fresh checkout to install for each surface a task's `Where:` names, and what `## Execution`
  asks for beyond it. Also the files git ignores that a gate needs, model weights first of all,
  linked from the main checkout the way Execution says. A repository that builds against the
  run branch of another is set up the way its `Environment` section says. An item that cannot
  be met is a stop before the first wave, with the report of Step 4.
- **The block.** Three to seven lines: what is present, what was done and where (which
  install in which path, in which repository), which profiles the review rounds will use,
  `claude-only` when Step 1 found no `codex`, what Execution named and how it was met, which
  stand is up and whose it is when the owner said so, and the free space the check of Step 1
  found. Write the block to `<journal>/preflight` as well: a continuation takes it from there.

## Step 3: the wave loop

Repeat until no task section holds an open `[ ]`:

1. **The ready set.** Re-read the plan. A task is ready when its section holds an open `[ ]`,
   every task its `After:` names has no open `[ ]`, and either no checkbox of it carries a
   `⚠️` or its lane worktree exists. A stopped lane whose marks the integrator carried into the
   plan is resumed on a continuation, and its `⚠️` is the question the continuation answers.
   Two ready tasks with the same `Needs:` value do not run together: the one earlier in the
   file runs now, the other waits. An empty ready set with open tasks left is a stop. The open
   tasks wait on a task that stopped, or on the owner, and the report of Step 4 says which. No
   open task left: go to the whole tree, below.
2. **Announce the wave** in one block: its number, one past the highest `wave N` in the
   journal, and each task with its repository and its open checkboxes. Log
   `EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh 'wave N: started, tasks <numbers>'` with
   the task numbers alone, comma-separated, as in `wave 2: started, tasks 3, 4, 7`. The status
   page reads the wave's tasks from that list.
3. **Cut the lanes.** For each task of the wave, from the main checkout of its repository,
   `<tip>` being the `HEAD` of that repository's run branch:

   ```bash
   git worktree add .claude/worktrees/<slug>-task-<N> -b <slug>-task-<N> <tip>
   ```

   Then copy the task's section of the plan, from its `### Task N:` line to the line before
   the next heading, into its progress file `<journal>/lanes/task-<N>.md`. The lane ticks that
   file from then on.

   A lane worktree that already exists is a stopped lane continuing, and
   [`continuation.md`](references/continuation.md) says how it is brought onto the run branch.
   Before the lane starts, a task gets in its worktree what the `Environment` section of its repository asks a fresh
   checkout to install for each surface its `Where:` names. That includes a surface a
   generator writes from what the task changes: a generator that runs without the packages of
   the surface it writes stops there. The ignored files of Step 2 are linked into the lane the same
   way. A lane that continues keeps both.
4. **Launch the lanes**, all of them in one message, each a subagent (the Agent tool,
   `general-purpose`, `name` the lane's name, in the background) with the prompt of
   [`references/task.md`](references/task.md), every placeholder substituted. `WAVE` lists every
   task of the wave, and `PROGRESS` is the lane's progress file. Then wait for all of them.
   A lane that comes back red goes to a fresh subagent, not to this session. A lane logs a line before every command
   that runs for minutes, with the time it expects. When the owner asks how the run stands,
   answer from the journal: which lane is in which command and since when. A lane whose last
   such line is older than twice the time it named is not waited for further. Look at its
   worktree and at its processes. Look also at `pmset -g log` for a sleep of the host, which
   stops Go timers and makes a live test look hung. A lane that went idle with its task open,
   saying it waits for a command, is not woken when that command ends. Watch the command's
   output file. When the command ends, send the lane by name, with the SendMessage tool,
   «your command has ended: read <the file> and go on».
5. **Read what came back**, lane by lane, as each ends: the lane's progress file and the
   journal lines it appended.
   - Every checkbox of the task is `[x]`: say "Task N done" in one line; the lane has logged
     the details.
   - `[blocker] environment task N` in the journal and no `⚠️` of another kind: when every
     other lane of the wave has ended, resume this lane once by its name, with the SendMessage
     tool and the words «rerun now». The SendMessage tool is deferred in a fresh session and is
     loaded with ToolSearch first. Read the lane again when it ends. Still red: the lane stopped, as below.
   - A `⚠️` on a checkbox, or an `[owner]` or `[blocker]` line of another kind: the lane
     stopped. Its worktree, branch and progress file stay. The wave goes on without it.
   - Open checkboxes and no `⚠️`: one retry. The retry is a fresh subagent on the same lane,
     the same worktree, branch and progress file, not a clean worktree cut again. `RETRY`
     carries the errors of the first attempt, its report and the journal lines it wrote. One
     retry, not two. Still open: the lane stopped, and this session
     logs `[blocker] task N: <what the two attempts left>`.
6. **Integrate.** When every lane of the wave has ended, spawn one subagent (the Agent tool,
   `general-purpose`) with the prompt of [`references/integrate.md`](references/integrate.md),
   every placeholder substituted. `REPOS` names each repository a lane of the wave runs in,
   with its run worktree, its branch, its base and the tip its lanes were cut from. `LANES`
   names only the lanes whose progress file has every checkbox `[x]`, each with its
   repository, worktree and progress file. `LANES` follows the order the Shared files table of
   the plan gives, the lane that is second after the one that is first, the rest in file order.
   `STOPPED` names the lanes that stopped, the same way as `LANES`. One integrator works
   through every repository of the wave: one agent writes the plan. Wait for the integrator.
   Read the journal lines it appended:
   - `wave N: integrated` and no `[owner]` or `[blocker]` line: remove the integrated lanes,
     `git worktree remove --force .claude/worktrees/<slug>-task-<N>` and
     `git branch -D <slug>-task-<N>` from the main checkout of each lane's repository, for the
     integrated lanes only. The removal takes `--force` since an untracked leftover makes it
     refuse and the lane's branch is merged. Then remove the lint cache of each,
     `rm -rf <journal>/cache/lint/<repo>/<slug>-task-<N>`, and
     the Go build cache of the run, `rm -rf <journal>/cache/go-build`. Go compiles the
     module's packages again under the path of every worktree, a copy of the compiled tree per
     lane. Nothing reads those entries once the lane is gone. No lane builds at this
     moment, and the next wave starts with a cold build. The progress file of an integrated
     lane stays in the journal: the status page reads it. The lint caches
     of the run worktrees stay. Then, when no lane of the wave stopped, the next pass of
     the loop. When one did, the report of Step 4, after the integration and not before it.
     The review and the finalize do not run after such a stop.
   - A red check the integrator could not make green: one retry of the integrator with `RETRY`,
     as for a lane. An `[owner]` line, a `[blocker] environment integration N` line, or a
     merge it could not resolve: a stop with the report of Step 4. Nothing of the wave is
     integrated twice. The integrator's own journal line says how far it got, and the lanes it
     merged have their commits on the run branch. The retry skips those lanes and drops what
     the first attempt left uncommitted, as [`integrate.md`](references/integrate.md) says.

A lane that cannot close an item leaves it open with its reason, and the owner reads the reason in the report, not a question mid-run.

**The whole tree.** A lane checks only what it touched: the build of the surfaces it changed
and the tests of the packages it changed, the generators and the docs check when it
moved them. An integrator builds and lints the whole tree of each repository its wave touched.
It runs the tests only of a surface two lanes of its wave changed, since a surface one lane
changed was tested by that lane. Once every task is closed, the whole tree of every repository
of the plan is checked once, before the first review round. An executor like the lanes' does
this check, not the finalize. What goes red there is fixed by the run, and the fix is reviewed
with the rest of the branch. For each repository, one after another, spawn one subagent (the Agent tool,
`general-purpose`) with the prompt of [`references/check.md`](references/check.md), every
placeholder substituted for that repository, and wait for it. The order is the one the
`Environment` section gives the builds across repositories, a repository another builds against
first. With no order given, the order of `repos`. A repository whose branch holds only the
plan's own commits has nothing to check and is skipped. The subagent runs the whole-tree checks
the `Gates` section names, the generators' drift check, the docs check, the build, the lint and
the tests, every component whatever the branch touched. It fixes and commits until they are
green.
Read what came back:

- `whole tree: <repo>: green` in the journal and no `[owner]` or `[blocker]` line: say so in
  one line and go to the next repository, then to the review. A
  `[deviation] … red at the base as well` line beside it is a failure the branch did not cause:
  the same check, run alone, is red at the base. The run goes on, and the line goes into
  `open:` of the run report.
- an `[owner]` or `[blocker]` line: stop with the report of Step 4.
- neither: one retry, a fresh subagent with the errors of the first attempt in `RETRY`. Still
  not green after it: this session logs `[blocker] whole tree: <repo>: <what the two attempts
  left>` and stops the same way.

Log the start of each with
`EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh 'whole tree: <repo>: started'`.

## Step 4: the stop report

In chat, no file. A stop in Step 2, 3, 5 or 6 ends on this report. Before the report, log
`EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh 'run stopped: <the value of stopped at>'`.
Until that line, the status page and its watcher take the run as running.

```
stopped at: preflight, <repo> | wave N: <tasks> | integration of wave N | whole tree, <repo> | review round <repo>/<run>, <profile> | finalize, <repo>, <regroup | close>
open:       <the checkboxes left open, each with its ⚠️ reason | the findings left, each with
            its sort | the gate that is red>
lanes:      <each lane worktree that still exists: its task, its repository, its branch @ <sha>,
            why it stopped>
journal:    <every [owner] and [blocker] line, verbatim>
logged:     <every [decision] and [deviation] line, verbatim>
branches:   <one line per repository: <repo>: <branch> @ <sha>, base <sha>, <worktree path>>
next:       <what the owner decides | for a [blocker] environment line, what on the host to
            repair>; after a stop of the finalize in a regroup, first put that repository's
            branch back on its tip, `git reset --hard backup/<slug>-<stamp>` in its run
            worktree, since the regroup left it part way, the rest uncommitted; an
            answer that changes the plan goes into the plan, <the plan's absolute
            path>: in a tracked plan committed there through `commit.sh` from the home
            repository's run worktree, in an untracked plan edited in place; then
            `/planning:exec-plan <plan>` continues: the stopped lanes are brought onto their
            repository's run branch and rerun, and the loop goes on from the ready set, or from
            the whole-tree check when every task is closed
```

The plan the run reads is the one the journal's `plan` names. An answer to an `[owner]` or a
`[blocker]` line that changes the plan lands there, as `next:` says. Then the run continues. A
tracked plan refreshed on the trunk through `/planning:make-plan <plan>` instead never reaches the branch,
because the trunk is not merged into the branch. For such a refresh, remove the run
worktrees, the lane worktrees and the branches in every repository, and the journal. Then
start the run again from the refreshed commit. A refresh that moves its premises to newer trunks needs the same restart: the branches
stand on the commits the old premises were checked on.

## Step 5: review rounds

Every task is closed. The branch of each repository from its `base.<repo>` now goes through
revmux rounds until one is clean or three have run. Each repository is reviewed on its own.
Its rounds, its fixer and its count of rounds are its own, and a plan of three repositories
starts with three first rounds. The repositories are reviewed one after another, in the order
of the whole-tree check. A stop in one is the stop of the run, and the repositories after it
wait for the continuation. A repository whose branch holds only the plan's own commits gets no
round. "The branch", "the task" and "the round" below are those of the repository under review.

The `Review` section names two profiles: the first round's, by
default `comprehensive`, and the profile of every round after it on the fixes, by default
`final`. Every round runs on `claude-only` when Step 1 found no `codex`, as the journal's
`preflight` records it. This file calls
the two profiles the first-round profile and the last-round profile.
The three rounds are counted over the whole run, by the round directories under the task in
the repository's main checkout, `.revmux/tasks/<slug>-<repo>/`, not per session. A round that
failed or was degraded, the stops of 1 and 2 below, is not counted. Such a round holds no
`findings.json`, or its `sources` show the gap. The first-round profile runs once on a branch.
It is the round with both models and every lens, and a second one reads a diff that was
already read. Load the `revmux:revmux` skill and follow it, with what
a run changes:

- The subject is the branch: `git diff <base>...HEAD` in the repository's run worktree, the
  whole range in every round. The lanes are already in it, and no lane worktree exists by now.
  `scope.md` carries that range and the repository's name. It says to read the plan at its
  absolute path in full before the diff. On a round after the first, it names the fix commits
  since the previous round. `goal.md` is the plan's Goal in two lines and the criteria: the
  `Result:` of every task of this repository holds, nothing under `## Out of Scope` moved, the
  rules of the project hold. On a round of the last-round profile it is the merge gate, as the
  revmux skill asks of the last round before a merge. The round answers whether anything in the
  branch should not ship, and finding nothing is a valid answer. `profile.md` names the root
  `CLAUDE.md` of the repository, the `CLAUDE.md` of each surface the branch touches, the rules
  file the repository's rules come from when it has one, with the rules its `Review` section
  holds a branch to, and the plan's `## Decisions`
  as where the rules live. `profile.md` also says a Decision is settled: that the branch does
  what a Decision says is not a finding, and that a Decision is wrong is an open question.
- The task id is `<slug>-<repo>`, whatever the branch is called, also in a plan of one
  repository. The plan's own review ran under `plan-<slug>` and is another subject. The two
  subjects are never joined. The rounds are `NN-initial`, `NN-after-fix` and `NN-final`, `NN` one past the
  highest round already under the task.
- Rounds run from the repository's main checkout with `--workdir <its run worktree>`, headless
  (`--no-tui`), in the background. The project layer,
  `.revmux/prompts/` and `.revmux/lenses/`, is read from the process working directory. The
  archive lands in that main checkout's `.revmux/tasks/`. `revmux new` runs from there
  too. The round's command starts with `caffeinate -i`. Claude Code keeps the host awake
  while a subagent runs and drops that hold while a background shell is all that runs. So a
  host on battery sleeps in the middle of a round.
- The revmux skill's questions are not asked, and its loop is not entered: headless is
  settled, the fixer below decides what is fixed, and this step is the loop.

**A continuation** of the review goes on from the rounds the task already holds, as
[`continuation.md`](references/continuation.md) says.

Read the result in this order; the first line that applies decides:

1. The exit code. `0` and `1` are finished rounds. `2` is a failed one: read the stderr log.
   When the round directory holds `findings.json`, the round finished and only its write to
   stdout failed. Read the findings there. Otherwise stop with the report of Step 4. A failed
   round is not evidence.
2. `sources.degraded`. Non-empty, or `sources.expected` not equal to `sources.reported`: stop
   with the report of Step 4. A partial round says nothing about the branch, and its silence
   is not a clean round.
3. `findings`. No `critical` and no `major`: the round is clean. With no `minor` either, log
   it and go to the next repository, or to Step 6 after the last. With a `minor`, the fixer
   runs once more, in its minor pass, and the repository is done with no round after. A round
   over the fixes of minors brings about as many new minors as it closes, so a loop on them
   never ends. Otherwise the fixer, then the next round. After the third round no fixer runs
   and no round follows, unless the third is clean and holds minors. Those minors get the
   minor pass like any clean round. What the third round leaves goes into the run report as
   open findings, and the repository is done.

Log every round with `EXEC_PLAN_JOURNAL=<journal> scripts/progress.sh 'review round
<repo>/<run>: <profile>, <n> critical, <n> major, <n> minor, degraded <none | names>, <clean |
clean, minor pass | fixer | stop>'`.

**The fixer.** One subagent (the Agent tool, `general-purpose`) with the prompt of
[`references/fixer.md`](references/fixer.md), every placeholder substituted for the repository,
and wait for it. The fixer sorts every finding into fact, fork or noise. A fact is fixed,
gated and committed through `commit.sh`. A fork is logged as `[owner]` with the question in
plain words. Noise is dropped with its reason in the journal. Read what came back, the journal lines the fixer appended and its report:

- an `[owner]` or `[blocker]` line: stop with the report of Step 4, the same stop as after a
  wave. The branch waits on the owner's answer. `/planning:exec-plan <plan>` after that answer
  continues the review as [`continuation.md`](references/continuation.md) says.
- no commit, because every finding was noise or an answered question: no round follows. A
  round on an unchanged diff reads the same diff again. The dropped findings go into the run
  report with their reasons, and the repository is done.
- after the minor pass: the repository is done, whatever was committed. The minors the fixer
  left go into the run report as open, each with its reason or its question. So do the open
  questions the fixer could not settle. The minor pass logs no `[owner]` and no `[blocker]`, because a
  minor does not hold the branch.
- otherwise: the next round, on the fixes.

When every repository is done, Step 6.

## Step 6: finalize

One subagent (the Agent tool, `general-purpose`) with the prompt of
[`references/finalize.md`](references/finalize.md), every placeholder substituted, and wait
for it. In every repository of `repos`, the subagent regroups the history from that
repository's base behind a `backup/` branch and proves the tree did not move. Then it closes
the plan by its mode and logs `finalize: plan closed, <the plan's absolute path after the close>`, the line
the status page follows, and reports. It runs no gate, not the usual last check on the final
tip. The whole tree was checked before the review, and the regroup leaves the tree byte for
byte as it was. A `[blocker]` line from
the subagent, or a diff against a backup that is not empty: stop with the report of Step 4. The
history stays as the subagent left it, the backup branch holds the tip, and the plan stays
where it was. After a stop in the middle of a regroup, the report's `next:` names the reset
the owner runs first.

**Clean up after the run.** Before the report, from the main checkout of each repository,
remove what the run left on the disk and nothing it did not make:

- a stand the run's lanes raised that was down when Step 1 looked, by the journal's `stands`,
  taken down the way the
  `Environment` section says, its volumes with it. A stand that was up before the run is
  another session's and stays. A command that takes down every stand on the host, the stand
  of another checkout included, is never run here;
- the scratch worktrees of the base and tip checks, when one is left in any repository;
- on a host that runs Docker, `docker image prune -f`: every rebuild of a stand's images left
  the old layers dangling;
- the run's caches, `rm -rf <journal>/cache`.

The report's `whole tree:` line is followed by what was freed, `df -k` before and after.

Then run `EXEC_PLAN_JOURNAL=<journal> scripts/audit.py`. The script's count goes into the
report's `audit:` line. Its findings follow that line as they were printed, up to twenty; past
twenty, the count per rule.

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
pull request until the owner's steps of `owner:` are done. The report says so plainly, and the
run takes none of those steps.

**revdiff.** The owner is back, and from here questions are allowed again. When `revdiff` is
on `PATH`, load the `revdiff:revdiff` skill. Open revdiff from each repository's run worktree
in turn, in the order of `repos`, on the whole branch, `<base>...HEAD` with that repository's
base: not the last commit, not the working tree. When revdiff closes, read the annotations by
the refs of this run, never by the newest history file. Parallel reviews of other branches
write there too. Every annotation gets one line in the reply,
`<repo> <file>:<line> <the comment, shortened> -> answered | fixed in <sha> | disagree: <why>`. A
question is answered and changes nothing. A change is made by this session in that
repository's run worktree and gated. This session commits it through
`EXEC_PLAN_JOURNAL=<journal> scripts/commit.sh` on top of the regrouped history, as
`fix(<scope>): ...` or `docs(<scope>): ...`. An annotation that is unclear is quoted back with
two readings. No annotation is skipped, and none becomes a backlog item, a plan or a decision
record unless the annotation says so. No annotations: say so and name the history file that
was read. Reopen revdiff on the fixes only when the owner asks. A gate run here builds the
run's caches again: remove them once more after the last fix. End on one line. That line
gives the count of annotations and how many were fixed, answered and disagreed with. It also
says that the pull requests of `<branch>` onto each repository's trunk are next, after the
owner's steps of `owner:`. Without `revdiff`, the run
report is the end and the pull requests are the owner's next step.

## Common mistakes

| Mistake | Fix |
|---|---|
| Ran `go clean -cache` or `golangci-lint cache clean` | Those clear the caches every session on the host shares; the run removes `<journal>/cache` |
| Built, tested or linted Go without `. scripts/cache.sh` in the same shell call | The command writes into the shared caches, and the lint leaves there the paths of a worktree that will be gone |
| Ran another round on the fixes of the minor pass | None; minors arrive at about three a round, and a loop on them does not end |
