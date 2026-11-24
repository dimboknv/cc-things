---
description: plan fit, whether a plan rests on premises true of the tree, settles every choice itself, and can be run task by task by an executor with nobody to ask
---
## Lens: plan

The subject is a plan. An autonomous executor will run it task by task with nobody to ask, so
judge it against the tree it would change, never against itself. The expensive defect is the
one found after the run: a premise that was false of the tree, or a choice the plan left for
the executor to make.

`scope.md` names two files by absolute path. Read both first; this lens does not restate them.

- The form: the form of a plan, `references/form.md` of the `make-plan` skill. Hold the plan to
  it.
- The project rules: the project's rules file, or "none". Its `Plan form` section adds to the
  form, and the plan is held to both. Its `Records` section names the records that bind a
  design, the records that only explain one, and the judgements only the owner makes. Its
  `Consumers` section names where to search for readers and writers. A section the file leaves
  out, or a file that is "none", adds nothing: no record binds, and the search runs over the
  whole checkout. A heading the file carries beyond those is an addition to this lens.

A task's tree is its repository: the directory its `Repo:` line names, relative to the working
directory, or, for a task without the line, the repository the plan lies in. Run a task's
anchors, inventory and searches there.

Check each of these and report where one fails:

- Premises against the tree. Each premise carries an anchor, a file with a quoted string or a
  command with a line of its output. Run every anchor. Report a premise whose anchor is gone,
  one that is false of the tree, and a fact a decision or a task rests on that is not written as
  a premise at all. A claim about a system the repository does not own (an engine, a library, a
  vendor's protocol) is a premise too, anchored in the vendor's document or the source of the
  version the tree pins; check it there, and report one that rests on memory.
- Invariants and bounds for every process that holds state between requests: a consumer window,
  a cache, a map in one replica, a key-value bucket, a queue, a scheduled job. Each needs the
  invariant that is never broken while it runs and the bound on what it holds, for how long, how
  many retries, stated so a check can fail on it. A process the plan touches with neither is a
  finding. The same for a list or a batch the plan sends across a boundary: the receiver's
  limit with its anchor, and what the sender does past it.
- Decisions written as assertions. A decision that reads as a menu ("A or B"), as a question, or
  as "decided during implementation" is not one. A decision is a choice between alternatives the
  executor could not make alone from the tree, and it names the alternative it rejects; a task
  that needs such a choice the section does not carry has found a hole in the plan. A detail the
  executor settles with the code in front of it is not a decision, and its absence is not a hole.
- Consumers of the old shape. When a wire contract or a stored shape changes, every reader and
  writer of the old shape is named and moves with it, unless a decision says why the old shape
  stays and which task removes it. Look for the consumer the plan missed with `rg` over the
  places the `Consumers` section names, tests included: the tests and specs that pin the old
  behaviour, the test suites of a binary, the end-to-end suites, the seeds and fixtures, the
  build and deploy scripts, and the code written by hand beside a generated client.
- A rename or a removal carries an inventory: the `rg` set of terms in every spelling the tree
  could hold, and the surfaces it runs over. Run the inventory yourself. A term or a surface the
  set misses is a finding. A task that adds or changes something carries no inventory, and its
  absence there is not one.
- One owner per fact, and nothing against a binding record. A value, a vocabulary or a schema
  the plan states in prose while an artifact owns it, a migration, a contract file or a module,
  as the project's `CLAUDE.md` or the `Records` section names it, is a finding. So is a
  decision that contradicts a record the `Records` section names as binding, and a decision
  that goes against a record it names as rationale without a task that rewrites that record.
  Cite the one it contradicts. Search by what a decision stops keeping, raising, checking or
  recording, not only by its mechanism's name: a seven-day stream conflicts with a requirement
  that forbids eviction, and nothing in the stream's name says so. A binding record's text the
  Owner Sign-off rewrites counts as in force, and every decision about the same kind of record
  is held to it. A decision against a convention in a skill the project or an installed plugin
  holds for the surface, that does not cite it and say why, is a finding too, because the run's
  review holds the branch to the skills.
- Nothing deferred. No choice is left to the executor, to a backlog item or to later. What only
  the owner decides, the judgements the `Records` section reserves to the owner, accepting a
  rewritten record, taking a tool out of the loop, sits in Owner Sign-off in plain words with
  the consequence the owner accepts. An owner-level decision anywhere else in the plan is a
  finding.
- The simpler mechanism. Where a config value, a deletion, a tool already in the loop or a
  smaller shape would do what a decision proposes, the decision names it and says what it lacks.
  When it does not, name the simpler shape concretely. "Too complex" is not a finding.
- Task size and proof. Each task ends with the tree building and the gate of its surface green,
  because it ends in a commit and the hooks run on it, and it fits one session of one executor.
  A task that cannot end green is two tasks or a wrong `After:`. Every decision and every
  invariant is proven by an acceptance in some task, a check that can fail. A decision nothing
  proves, and an acceptance that cannot fail, are findings.
- Repositories, as "The plan's place" and the `Repo:` item of the form state them. A task with
  no `Repo:` line in an untracked plan, one outside every work tree or in a directory its
  repository ignores, is `major`: an open fork, since nothing in the tree says which repository
  the task changes. A task whose `Where:` or checkboxes reach into a second repository is
  `major`: its lane works in one repository's worktree, and a change across two repositories is
  two tasks joined by `After:`. Two tasks of different repositories never share a file, so a
  Shared files row that names two such tasks is a contradiction between the table and what the
  tasks edit. A `Repo:` that names no directory under the working directory is a fact the tree
  refutes.
- The light mode. A plan whose Execution carries a Mode line is held to the conditions the form
  gives under Mode. For such a plan, a reader or writer of a changed shape the plan does not
  name, an open choice, a task that needs a second executor, or tasks in more than one
  repository are `major`, because the run takes the light path on that basis and its one
  executor works in one checkout. A section filled with a decision nobody had to make is a
  finding too.
- The form, as the form and the `Plan form` section state it: the sections and their order, the
  task header, `Result:`, `Decision:`, `Where:`, `Repo:`, the addresses, what a plan does not
  carry, the language.

Do not demand:

- test checkboxes, test names or paths to tests; a task says what must be proven and the
  executor names the test
- a full list of files; `Where:` names areas and the executor finds the files
- an order of commits, or the shape of the branch and the pull request
- a signature, a type shape, a value or a field list that the owning artifact carries

Report against the plan file. `line` is the line the finding is about, and the title names the
section it sits in (`Premises`, `D4`, `Task 3`) so the author finds it without the line. Open
the body with one of three words, then the argument:

- `fact:` the plan says one thing and the tree says another. Quote both.
- `fork:` the plan needs a choice it does not make. Name the two or three ways to settle it and
  what each costs.
- `question:` the tree does not settle whether it is a fact or a fork. Say what would.

Every finding carries one of three severities, by what it costs the executor:

- `critical`: the plan cannot run as written. A premise the tree refutes, a decision that
  contradicts a binding record, an owner-level judgement the plan makes itself.
- `major`: an executor would act on it wrongly, and nothing in the tree would stop it. One of
  four: a fact a task or a decision rests on that the tree refutes; an open fork, a choice the
  executor cannot make from the tree; a contradiction between two decisions, two tasks, a
  decision and a task, or `After:` and the Shared files table and what the tasks edit; an
  acceptance that cannot fail.
- `minor`: worth fixing and blocks nothing, because the executor settles it with the tree in
  front of it, or the build, the inventory or the run's review rounds catch it. A consumer of the
  old shape the plan does not name (outside a light plan, where it is `major`), an invariant or
  a bound stated loosely, a `Where:` narrower than the work, a detail written as a decision,
  form, wording, an anchor that does not resolve on one line. Execution journals show executors
  settling these as a matter of course: most of their recorded deviations are edits like these,
  and the plan named a wrong path in two percent.

A finding is one of those three kinds with one of those three severities, or it is not a
finding. Findings are the whole output. A summary of the plan, or a judgement that it is
ready, is not one.
