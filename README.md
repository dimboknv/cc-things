# cc-planning

A Claude Code marketplace with one plugin, `planning`: three skills that form one loop of work.

- `/planning:brainstorm` — a design session: facts from the tree first, then one fork at a time,
  ending in a summary the owner confirms.
- `/planning:make-plan` — a plan whose premises are checked against the tree and whose tasks carry
  `After:` lines, reviewed before it runs.
- `/planning:exec-plan` — runs the plan: every task whose `After:` is met runs as a lane in its own
  worktree, one integrator merges each wave, then the whole-tree check and the review rounds.

The skills assume agterm for the fork page, the peer and the
status page, and [revmux](https://github.com/umputun/revmux) for review rounds. Outside agterm a fork
goes to the chat as a message; without revmux the `plan-review` agent reviews a plan.

## Install

```
/plugin marketplace add dimboknv/cc-planning
/plugin install planning@cc-planning
```
