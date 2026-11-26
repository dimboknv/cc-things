# A continuation

What a run does when its journal already holds a `base.<repo>` file. Everything in
[`SKILL.md`](../SKILL.md) holds, and its steps are named here by their numbers. This file says
what Step 1, Step 3, Step 5 and a light run do on a continuation.

A second `/planning:exec-plan` on the same plan goes the way the first went: the wave loop from
the ready set, then the whole-tree check, then the review. The review goes on from the rounds
each repository's task already holds and never starts over (Step 5). With every task already
closed the run goes straight to the whole-tree check.

## Step 1

On a continuation, the repositories are the lines of `repos`, and
the checkout that runs in each is its run worktree. A run worktree that is gone is added back
by hand, `git -C <main checkout> worktree add .claude/worktrees/<slug> <branch>`, with the
branch the line names. The trunk of each repository is the one its `trunk.<repo>` names. The
`PREFLIGHT` block of every prompt, with the review profiles it names, is the content of
`preflight`. The stands the clean-up of Step 6 may take down are the ones `stands` lists.
Step 2 runs again only when `preflight` is missing: the run stopped before Step 2 ended. The
one check of a branch is the base check of Step 1. A checkout that does not stand on the recorded
base fails there, with the line of `base.sh` as the reason. Go to the base check. The premises
were rechecked and the go given when the run started, and nothing is asked.

On a continuation, list the lane worktrees under `.claude/worktrees/<slug>-task-*` in the main
checkout of every repository of `repos`. One whose task is closed in the plan was integrated
before a stop: remove it and its branch. One whose task is open is a lane that stopped, and
Step 3 resumes it.

## Step 3

A lane worktree that already exists is a stopped lane continuing. It keeps its branch and
its commits. Before its lane runs, its repository's run branch is merged into it from inside
that worktree, `git merge <run branch>`, so the lane sees the waves integrated since it
stopped. That merge is the one merge this session makes, and it resolves nothing. A
conflict in that merge is a stop with the report of Step 4. Files the stopped lane left
uncommitted stay in its tree for the lane to take up, and git merges around them. A merge
git refuses because it would overwrite one of those files is the same stop. Its `lanes:`
line names those files, and the owner commits or removes them. The lane's progress file is
written anew from the plan's section as it stands, which brings the owner's answer. Every
mark of the old file, a tick or a `⚠️`, is set again on the item whose text still stands
word for word. An item the owner rewrote comes without a mark.

A continuation with every task closed runs the whole-tree check again in every repository.
That check is the one state of the run no checkbox records.

## Step 5

The repositories are reviewed in a fixed order, so the journal says where
the review stopped. The repositories before the one whose `review round <repo>/…` line or
fixer stopped the run are done. The ones after it have not started. A repository that is
done is not reviewed again. In the repository that stopped, its task already holds a round,
and its review does not start over. The last round may have stopped on an `[owner]` line, and
the plan now holds the answer. It may have stopped on a `[blocker] review <round>:` line, a
gate the fixer could not make green, and the owner has cleared what held it. Or it may have
stopped on a `[blocker] environment` line, and the owner has repaired the host. In each of
these three cases, give the fixer the findings of that round again, `findings.json` in its
directory. Then run the last-round profile on the commits the fixer makes. With three rounds
already under the task, the fixer runs and no round follows. When the last round failed or was
degraded, the stop of 1 or 2 in Step 5, run it again on the same profile as a new round, `NN` one
past the highest. Read the new round as any round. The fixer never gets the findings of a
failed or degraded round. The repositories after the one that stopped start at the
first-round profile.

## A light run

A continuation of a light run reads the same state: `base.<repo>` and the checkboxes. A `⚠️` the
executor left is in the plan itself, not in a lane's progress file. So here the mark does not
take its task out of the ready set. The executor runs again over every task with an open
`[ ]`, a marked one included, and removes the mark when it closes the item. Then the check.
Then the review, from the rounds the task holds. A last round that failed or was degraded,
the stop of 1 or 2 in Step 5, is not counted. The fixer never gets its findings. That round
runs again on the lens set as a new round, `NN` one past the highest, and is read as the
round it replaces. Then, with one round: the fixer on its findings, then `NN-after-fix` on
the lens set as [`light-run.md`](light-run.md) says. With two rounds: the fixer on the second
round's findings and no round after it, and what the fixer leaves goes into `open:` of the run
report. Never a round on the profiles of a full run and never a third counted one.
