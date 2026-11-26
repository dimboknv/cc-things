# A run with a peer

What a run of the skill adds when the owner asked for a peer: when the peer is asked, what it
is asked, and what the run does with its answer. Everything in [`SKILL.md`](../SKILL.md)
holds, and its steps are named here by their numbers. Load `mailbox-chat` before the first
step. Needs agterm.

The session that received the owner's request is the **lead**. The **peer** is a second agent,
Claude Code or Codex, in the split pane of the same agterm session. The lead runs the plan.
The peer reads, and writes only its two files in the journal, never the worktree. The owner
reads both panes.

## What the peer is for

A plain run reads the branch once, at the end. By then every wave stands on the waves before
it, and a defect of the first wave is fixed under all of them. Across the branches the skill
ran, the final rounds found two or three majors a branch, and most of them were behaviour at
the edges: a race, a receiver's limit, a failure halfway through an operation, a row not
scoped to its owner. The peer looks for those after every wave, while the next wave runs.

A plain run also lets every lane decide alone what the plan leaves open, and no lane sees
what another decided. The peer reads those decisions and keeps the notes the later lanes get.

Whoever the peer is, it fixes nothing. A subagent of the lead does, in a lane of its own:
`mailbox-chat` lets only the lead's side edit the worktree, and the Claude Code hooks and
skills of the project do not bind a Codex.

## State

Beside what a plain run keeps, in `review/` of the run's journal, which the lead creates after
the `base.sh` of every repository and never before the go:

- `notes.md`, the notes every lane gets. The lead writes it once, after the go; the peer
  rewrites it after every wave, starting from the file as it stands. Forty lines at most. A
  run with no `notes.md` gives its lanes an empty `NOTES`.
- `wave-<N>.json`, the peer's findings on wave `N`, in the shape the fixer reads:
  `{"findings": [{"repo", "file", "line", "severity", "title", "body", "fix", "sources":
  ["peer"], "verdict": "unverified"}]}`. `repo` is the repository the finding sits in, and
  `file` is relative to it. `severity` is `critical` or `major`; the peer reports nothing
  below.

A review lane is the branch `<slug>-review-<N>` and the worktree
`.claude/worktrees/<slug>-review-<N>` in the main checkout of one repository. Findings of one
wave in two repositories get two review lanes, one in each.

## Start: the council before the go

The owner picked the peer in the request or in the first question of Step 1: Claude Code or
Codex. The launcher is the one `brainstorm` keeps, given this skill's brief. `<plugin root>`
is `${CLAUDE_PLUGIN_ROOT}`, which SKILL.md names and the lead writes out as an absolute path:
this file is read with the Read tool, which substitutes nothing.

```bash
<plugin root>/skills/brainstorm/scripts/peer.sh <plugin root>/skills/exec-plan/references/peer.md claude
<plugin root>/skills/brainstorm/scripts/peer.sh <plugin root>/skills/exec-plan/references/peer.md codex
```

Either agent runs on the model its own configuration picks. A model id after `claude` is
passed only when the owner names one.

Step 1 runs to the end of its environment check. Before the message that
asks for the go:

1. Start the peer the owner picked. When the script refuses, give the owner its message as it
   is and offer the run without a peer. Do not start a peer by hand around a refusal. Tell the
   owner in one line what the right pane is, and that a permission prompt there waits for the
   owner: a peer that waits on one reviews nothing.
2. Send `plan`, below. In the same turn write your own answer to the same question into the
   scratchpad, before the peer's reply can arrive, and end the turn on one line saying what
   the peer was asked. The owner may answer that line with a go without the peer: the run is
   then a plain run.
3. When the reply arrives, set the two lists side by side. A point both have is kept. A point
   one has is checked with your own read before it is kept or dropped.
4. Sort what is kept. What only the owner decides goes into the message that asks for the go,
   each as a question with its options and what each costs: this is the one moment of the run
   when the owner answers. An answer that changes the plan sends it back through
   `/planning:make-plan <plan>`, as a false premise does. The rest stays in the scratchpad until the go.

The go covers the peer and every exchange with it. After the `base.sh` of every repository,
write `notes.md`: the notes kept in the scratchpad, and every answer the owner gave with the
go.

## The exchanges

The first line of a message is its tag. The last line says what reply is expected, or
`no reply needed`. The lead never waits for a reply inside a turn: it arrives on its own.

| Tag | The lead sends | The peer returns |
|---|---|---|
| `plan` | The path of the plan, the run's journal, every repository of the plan with its main checkout and the commit it is read at, the wave schedule. Nothing the lead concluded | Where an executor will stumble: a place that reads two ways, a task that cannot end green, a wave cut that puts two tasks on one file, a change one repository needs that no task makes, a question only the owner can answer |
| `wave N` | The path of the plan, for each repository the wave touched its run worktree and the range `<tip before the wave>..<tip after it>`, the titles of the wave's tasks, the journal path, the path `wave-<N>.json` is to be written at | One line: how many findings it wrote, that `notes.md` is rewritten, and `stop: <reason>` when a finding breaks what the later waves stand on |
| `end` | That the run is over | Nothing |

## The wave loop

Step 3, with four additions.

**The lane prompt.** `NOTES` of [`task.md`](task.md) is the content of
`notes.md` under the line «Notes of this run. A decision listed here is repeated, not made
again; a place marked as reading two ways is read the way the note says.» The notes of wave
`N` reach the lanes of wave `N+2`: wave `N+1` starts before the peer has read wave `N`.

**After `wave N: integrated`.** Send `wave N` and log
`review wave N: sent to the peer`. Then the next pass of the loop at once. A send that
answers `receiver: none` or an `error` is not retried: log
`[deviation] review wave N: no peer listening` and go on as a plain run.
The Go build cache, which Step 3 removes here, is removed only when no fixer is running: a
fixer builds from it while the next wave is cut, and the cache then waits for the next wave.

**When the peer's reply arrives.** `wave-<N>.json` with no finding: log
`review wave N: no findings`. Otherwise, for each repository its findings name, cut a review
lane in that repository from its run branch's `HEAD` as it stands now, give it what Step 3
gives a task lane whose `Where:` names the areas the findings sit in, the installs of the
`Environment` section and the linked ignored files, and launch one subagent in the background
(the Agent tool, `general-purpose`) with the prompt of [`fixer.md`](fixer.md): `CHECKOUT` and
`BRANCH` are the review lane's, `REPO` its repository, `PLAN` the plan and `JOURNAL` the
journal, `BASE` that repository's base, `ROUND` is `wave N, peer, <repo>`, `FINDINGS` the path
of `wave-<N>.json`. The fixer sorts only the findings of its repository. A reply that carries `stop:` is logged as
`[owner] review wave N: the peer asks to stop, not verified: <the peer's words>`: this
session reads no code, so the claim reaches the owner as the peer's. A reply that arrives
after a stop report starts nothing: the continuation takes it.

**The integrator.** `REVIEW` of [`integrate.md`](integrate.md) names
every review lane whose fixer has ended with a commit and whose repository and tip,
`git rev-parse <branch>` there, no `review wave …: merged, <repo>, <tip>` line of the journal
names, oldest first, each with its repository, and `REPOS` names the
repository of each. A fixer still running is not waited for: its lane
goes into the next integration. A review lane the fixer left without a commit is removed
with its branch. A merged review lane is removed the way an integrated task lane is.

An `[owner]` or a `[blocker]` line from a fixer, or the `[owner]` of a `stop:`, ends the run
on the stop report of Step 4 after the integration of the wave that is running. No lane is
cut short for it. In that report `lanes:` lists the review lanes too.

## After the last wave

Send `wave N` for the last wave and start the whole-tree check at once. When the check has
ended:

- the last wave's reply has not arrived: the run goes on without it. Its findings file, when
  it comes, is named under `open:` of the run report, and no fixer starts for it;
- a fixer still runs: wait for it. It is the lead's own subagent, and its end is announced;
- review lanes with a commit are left: one more integrator, `LANES` set to `none`, `REVIEW`
  naming them, `WAVE` set to `<last wave> review`, and `REPOS` naming the repository of each
  with its tip the run branch's `HEAD` after the check. Its `wave <last wave> review: integrated` line sends nothing to the peer.

Then Step 5 and Step 6, as written. The first round runs on the first-round profile whatever
the peer found: it is the measure of the trial.

## A continuation

A run whose journal holds `review/` is a run with a peer, whatever the request says, and its
continuation asks nothing, as Step 1 says of a continuation: the peer is the one the request
names, or Claude Code. Start it, then send `plan` with the same fields as at the start and
the last line `continuation, no reply needed`: the new peer learns the journal and the
repositories from it, and the council is not held again. The session kept the start's
commits in no file, so here the commit each repository is read at is the `HEAD` of its run
branch, with the base its `base.<repo>` holds beside it, and the wave schedule is built as
Step 1 builds it, over the tasks with an open `[ ]` alone.

- A review lane that holds a commit and whose repository and tip no `merged` line of the
  journal names goes into the next integration. A lane cut anew for a fixer run again has a
  new tip, so it is merged though its wave already has a `merged` line.
- A `wave-<N>.json` with findings and, for a repository its findings name, no
  `review wave N, peer, <repo>:` line of a fixer in the journal gets its fixer there.
- A wave whose fixer logged `[owner] review wave N, peer, <repo>`, `[blocker] review wave N,
  peer, <repo>` or `[blocker] environment review wave N, peer, <repo>` gets the fixer again, on
  the same file, now that the plan holds the owner's answer or the owner has cleared what held
  the gate or repaired the host: in its review lane when that lane
  still exists, else in one cut anew as "When the peer's reply arrives" says, since a merged
  lane was removed before the stop.
- A wave integrated with no findings file was not reviewed, and the run report says so.

## The end

After the run report, send `end` and leave the split open: the owner closes it.

This is a trial. The run report gains four lines:

```
peer:      <n> waves reviewed, <n> not (<which>)
findings:  <n> raised, <n> fixed, <n> dropped, <n> forks
council:   <n> questions asked before the go, <n> notes
round 1:   <n> critical, <n> major
```

The last line is what tells the owner whether the peer paid for its cost: a plain run leaves
two or three majors to the first round.
