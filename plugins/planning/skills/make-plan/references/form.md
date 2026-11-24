# The form of a plan

A plan is the one genre in the repo with a lifecycle: written, reviewed, executed, closed. This
file owns how one is written: the sections and what each carries, the form of a task, how an
address is cited, what a plan never carries, and its language. It does not own what "task done"
means. That is the gate, and the gate belongs to the `CLAUDE.md` governing the surface a task
touches: the root [`CLAUDE.md`](../../../../CLAUDE.md) for the architecture docs, the
requirements and the generated contracts, [`backend/CLAUDE.md`](../../../../backend/CLAUDE.md)
for Go, [`frontend/vartova/CLAUDE.md`](../../../../frontend/vartova/CLAUDE.md) for the console,
and [`ml/CLAUDE.md`](../../../../ml/CLAUDE.md) for the engine.
Nor does it own what a plan may contain at all: that is the placement table of
[`framework.md`](../../../../docs/architecture/framework.md), and the file's name and place
belong to [`docs/plans/README.md`](../../../../docs/plans/README.md).

`/exec-plan` runs a plan in waves of parallel lanes. Three parts of the form serve that: a
task's `After:` and `Needs:` lines, the Shared files table in Execution, and a task size that
ends on the tests of what the task touched, the whole tree's tests running once after the last
wave. A plan whose Execution names the light mode runs instead with one executor, a narrower
check and one review agent; the Mode item of Execution says when a plan may.

The form is shaped by where the expensive findings came from. A task that failed after
execution rested on a premise nobody had checked against the tree, or on a semantic question
the plan had left for the executor to settle. Signatures and file lists were what plans got
wrong most often, and the executor never needed them. So a plan is written at the level of
decisions, invariants and contracts, and everything below that level is the executor's.

## Sections

The headers are these English strings, in this order. Eight are always present. The two marked
conditional appear only when the plan has what they carry, and are absent otherwise, never
present with "none".

| Section | Carries | Present |
|---|---|---|
| `## Goal` | the state that is true when the plan is closed, what it replaces, and a `Closes:` line | always |
| `## Owner Sign-off` | what only the owner decides, already decided, with the consequences accepted | always |
| `## Decisions` | the choices between alternatives the tasks apply, numbered, each an assertion with its reason and the alternative it rejects | always |
| `## Premises` | the facts the plan rests on, each with an anchor in the tree | always |
| `## Invariants and Bounds` | what a process with state must keep, how much it may hold, and the limit of whoever receives a list or a batch | when the plan touches a process that holds state, or sends a list or a batch across a boundary |
| `## Contracts and Data` | each contract or stored shape that changes, its owner, and the consumers of the old shape | when the plan changes a wire contract or a stored shape |
| `## Out of Scope` | what was considered and is not done here, and where it goes | always |
| `## Execution` | the gate by link, what differs, the environment, barriers, the skills, the shared files | always |
| `## Implementation Steps` | the tasks | always |
| `## Post-Completion` | what only the owner or an interactive session can do, without checkboxes | always |

### Goal

One paragraph: the state of the tree and of the working loop when the plan is closed, and what
it replaces. When the plan replaces a way of working, a before and after pair says what goes
and what comes. The `Closes:` line names the `REQ-*` the plan proves and the `docs/backlog/`
items it closes, or says "nothing" and why (tooling, a refactor, an upgrade). A plan closes a
requirement only through a task whose `Result:` names it.

### Owner Sign-off

Everything the owner alone decides, written in plain words so the owner can answer without
opening the tree. That is the five judgements the root `CLAUDE.md` reserves (admitting,
deprecating or changing a requirement, its address, the admission bar), accepting or rewriting
an accepted ADR, deleting an artifact an accepted requirement addresses, taking a tool out of
the loop; with each, the consequence the owner accepts; and the steps the owner does by hand
before, around or after the run (pushing `master`, a config outside the repo). At execution
every line here is settled. The executor does not reopen it, and anything owner-level it meets
that is not here stops the run.

### Decisions

Numbered `D1`, `D2`, ... with a bold title, each an assertion: what is, never a menu of what
could be. Each names its reason. Where a simpler mechanism would also do, the decision names it
and says what it lacks. A decision is a choice between alternatives that the executor could not
make alone from the tree: it names the alternative it rejects. A detail the executor settles
with the code in front of it, an error's wording, a helper's place, the shape of a test, is not a
decision and goes into a task's checkbox or nowhere. Every choice of that first kind is here;
none is left to "decide during implementation" or to a backlog item. Decisions drew most of the
majors of the plan rounds, and every one is more text a round reads again. A decision that is the owner's goes in Owner
Sign-off. A decision that touches an accepted `REQ-*` or ADR cites it and does not contradict
it. A task cites the decisions it applies in its `Decision:` line, by number and not as a prose
paragraph, so a decision no task applies
is a finding. Every decision is proven by an acceptance in some task.

### Premises

The facts the plan rests on, checked against the tree while the plan was written. Each carries
an anchor: the file and a quoted string `rg` finds in it, or a command and the line of its
output. The anchor makes three later outcomes checkable: the anchor is in place; it moved, the
fact holds but the quote is gone; the fact is false. A false premise is a fork for the owner,
not a repair the executor makes. A fact that no decision or task depends on is not a premise;
it is discovery output and stays out. A premise may carry a measurement together with the
command that produced it.

### Invariants and Bounds

Present when the plan touches a process that holds state between requests: a consumer window, a
cache, a map in one replica, a KV bucket, a queue, a scheduled job. For each, the invariant
(what is never true while it runs) and the bound (how much it holds, for how long, how many
retries), stated so a check can fail on them. A bound this plan decides is stated with its
number; a bound that already exists is named with the artifact that applies it. Every invariant
is proven by an acceptance in some task.

Present too when the plan sends a list or a batch across a boundary: an RPC answer or request
that carries a list, a bulk call to an engine, a set of downloads or streams one press starts.
For each, the receiver's limit by its anchor (a size, an item count, a slot count, a range of
values), and what the sender does when the set is larger: pages, splits into batches, or
refuses. Example: «проверка подписок одним bulk-запросом к движку авторизации: лимит элементов
в одном запросе — в конфиге движка (якорь); больше — режем на пачки по лимиту». A list the
sender bounds below the limit by construction names that bound and needs nothing more.

### Contracts and Data

Present when the plan changes a wire contract (a proto, an OpenAPI fragment, a subject or a
message) or a stored shape (a table, a column, a KV value, a file on disk). For each: the
contract or shape by name; its owner artifact by link, the migration whose `CHECK` admits it,
the `contracts/openapi/src/` fragment the clients are generated from, the proto, the Go package
that provisions it; every reader and writer of the old shape that moves with it; and the task
that touches the artifact. Not the values, the DDL or the field list: those are the owner's,
and the plan names which task touches the artifact, not what the values are. The old shape
stops existing in the same task; the root `CLAUDE.md` keeps nothing backward compatible.

### Out of Scope

What was considered and is not done here, each with where it goes: a separate plan after this
one, the owner's config, nowhere. A hole found while designing the plan is not out of scope; it
joins the plan with its price. Out of Scope holds what the owner chose to leave.

### Execution

- **Gate.** A link to the `CLAUDE.md` of each surface the plan touches, then only what this
  plan does differently: docs-only (no Go, no `make generate`), deploy-only (verification is
  raising the contour, not tests), contract-only (honest `501` / `Unimplemented` stubs, no
  behavioural tests), or a per-task gate stricter than the default (test-first, reproducing a
  reported failure). A plan whose approach matches the gate says so in one line. The gate itself
  is never restated. The usual plan repeats the gate commands in each task.
- **Environment.** What a run needs beyond the tree: a stand, a container, a binary on `PATH`,
  credentials, `npm ci` in a fresh worktree, fetched model weights. The run's preflight reads
  this once.
- **Barriers.** A barrier is a point nothing crosses until it holds: an owner's step, a
  neighbour's merge. The order of tasks is not written here: a task that waits for another says
  so in its own `After:` line, and a task with no `After:` line waits for nothing. Every commit
  still builds, so a contract goes after its Go consumers or with them, inside one task, not in
  the usual barrier task that lands it first.
- **Shared files.** A table of every file two tasks of the plan edit: the file, the two tasks
  by title, and which one is second. The run merges the second task's lane after the first,
  and the integrator reads this table before it merges anything. Generated output and the
  coverage lines of the requirements are not listed: the integrator regenerates them. Two
  tasks that share a file and have no path between them in `After:` are a finding of the
  plan's review, not a case the run handles.
- **Skills.** By surface the plan touches, from `.claude/skills/` as it stands when the plan is
  written: `go-conventions` for Go, `add-migration` for a migration, `requirements`, `adr` and
  `chapter` for those genres, `ts-conventions` for the console. Most of the owner's remarks on a review are conventions, and the
  skills own them; the executor loads the skill of its task's surface before it edits.
- **Shared resources**, when the plan is one line of a parallel wave: the table of files another
  line of the same wave may touch, and the rule that serialises them (which line merges second
  and carries its edit onto the first's form; generated output is regenerated, never merged by
  hand).
- **Mode**, present only for a light run, as the line `- **Mode.** light — <reason>`. The
  reason says why the whole work fits one executor, not how small the diff is. A plan may be
  light when all of these hold:
  - it is one finished result in one domain;
  - no choice is open: every behaviour the work sets is a decision of the plan or settled by
    the tree;
  - one executor can close the tasks one after another in one checkout;
  - a contract or a stored shape it changes has every reader and writer named in Contracts
    and Data, and the tasks name the gates that prove the result on those paths.

  Files, lines and tasks are not counted: a one-line change to a permission check can need the
  full run, and a rename across a hundred files can be light. When one condition is in doubt,
  the plan is full. A light plan has the same sections as a full one. A section with nothing
  real in it says so in one line: a decision or an owner's line is never invented to fill it.
  `/exec-plan` says what the light run skips and what it keeps.

### Implementation Steps

The tasks, in the order they run. Nothing else lives between them.

### Post-Completion

No checkboxes. What only the owner or an interactive session can do once the run is closed: a
live run of an interactive tool, a config outside the repo, a memory note, the next plan. The
subagent that runs a task cannot ask a question and cannot drive an interactive step, and a
checkbox it cannot close stops the run. So a task holds only checks the subagent performs
itself, and what needs a person goes here.

## A task

```markdown
### Task 3: контракт и маршрут шлюза уходят одним коммитом

Result: в `contracts/` и в контроллере шлюза нет арминга; сгенерированное перегенерировано.

Decision: D2, D5.

Where: `contracts/proto/app-core/`, `contracts/openapi/src/`, `backend/internal/api-gateway/`.

After: «главы описывают систему без арминга» (код приводится к документам).

- [ ] фрагмент OpenAPI и сервис proto удалены; `make generate`
- [ ] контроллер шлюза без маршрута арминга, в том же коммите
- [ ] acceptance: `rg -n -i 'arming|арминг' contracts backend --glob '!**/generated/**'` пуст;
      гейт `backend/CLAUDE.md` зелёный
```

- **Header.** `### Task N:` with the English word `Task`, an integer `N` counting from 1 in
  file order, and a colon; the title after it, in the plan's language. A task loop finds a task
  by this header and by nothing else, so `### Задача 1:`, `### T1.` or a header without the colon is a task
  that never runs.
- **`Result:`** The state of the tree when the task is done, as something a reader can check.
  A `REQ-*` or a backlog item the task closes is named here.
- **`Decision:`** The decisions the task applies, by number. A task that needs a decision the
  list does not have has found a hole in the plan; the decision is written into Decisions, not
  into the task.
- **`Where:`** Packages, directories, areas: `backend/internal/device-gateway/`,
  `.revmux/lenses/`, `docs/architecture/chapters/`, the alarm ADRs. Not files. The refresh
  mode reads `git log` over these areas, and the executor finds the files. A rename or a
  removal names every surface its inventory runs over, `docs/architecture/` included when the
  `rg` covers `docs`: a hit there is the task's to remove. An area missing from `Where:` is one
  the Shared files table cannot see, and it is where most edits outside `Where:` in past runs
  landed.
- **`After:`** The tasks this one waits for, each by its title in guillemets with the reason in
  parentheses: a file both edit, a result this task builds on, a contract its code consumes.
  Absent when the task waits for nothing. The run starts a task when every task its `After:`
  names is closed, and starts together every task that is ready, so a task with no line runs in
  the first wave. Titles, never numbers: tasks are renumbered while the plan is reviewed, and a
  title survives it.
- **`Needs:`** Something one at a time on the machine that the task uses: the compose stand, an
  e2e lane. Absent for most tasks. The run never starts two tasks with the same `Needs:` in one
  wave.
- **Checkboxes.** As many as the task needs. Each names a resulting state or an edit the
  executor recognises as done. A task that closes audit or review findings points each item at
  the owning report (the domain report under `docs/architecture/reviews/`, the run archive of a
  review round) and verifies the fix against that report, not against the summary in the plan.
- **Acceptance.** The last checkboxes, each starting with `acceptance:`, each a check that can
  fail: a command and what its output must be. `rg ...` is empty; `rg` finds both paths;
  `make -C docs check` is green; `git check-ignore --no-index -v <path>` catches the path, or
  does not. "Verify it works" is not acceptance. That something exists or works is proven by a
  test or a gate, never by `rg` for a name: the executor chooses identifiers and files, and an
  acceptance that pins a name or a file the tree does not hold today goes red on a task that
  did what its `Result:` says. `rg` belongs to the inventory of a removal, and to a path that
  exists now.
- **Inventory**, for a rename or a removal only. The `rg` set of terms in every spelling the
  tree could hold: the identifier's casings and its snake, kebab and camel forms, the JSON and
  proto field names, the word in English and in the plan's language, plurals; the surfaces it
  runs over (`backend`, `frontend`, `contracts`, `deploy`, `docs`, `.claude`); and the globs
  that exclude generated output. The acceptance is that inventory empty, or reporting only the
  foreign meanings the plan names. A task that adds or changes something carries no inventory.
- **Size.** A task ends with the tree building and the tests of the packages it touched green,
  because it ends in a commit and the hooks run on that commit; and it fits one session of one
  executor. After every wave the run's integrator merges the lanes, builds and lints the tree
  and runs the tests of what the wave touched, and the next wave starts from that tip; the
  tests of the whole tree run once, after the last wave. A task that cannot end green is two tasks, or a wrong
  `After:`.
- **The executor's marks.** `[x]` on a closed checkbox, and `⚠️ <reason>` on the line it could
  not close. Nothing else is written into a plan during a run.

## Addresses

Every address in a plan is a quote `rg` finds: the file, and a quoted string from it.
`path.go:412` is right the day it is written and wrong by the time the task runs. A `:NNN` may
accompany the quote and never replaces it. The same holds for a command's output used as a
premise: quote the line, not its position.

## What a plan does not carry

- A `Files:` block, or any list of files to create or modify. `Where:` names the areas and the
  executor finds the files. The file list is what plans got wrong most often.
- Function signatures, type shapes, SQL text, field lists, config values. A decision or an
  invariant says what must hold; the value belongs to the artifact that applies it, and the
  migration, fragment or package that owns it is named in Contracts and Data.
- Test names. A task says what must be proven and which `REQ-*` a marker cites; the executor
  names the test.
- Counts: "14 files", "x4", "three readers". They are wrong after the first commit. Write the
  set, or the inventory command that finds it.
- `master@<sha>`, or "checked against commit X". Premises carry anchors, and the commit that
  carries the plan is its date.
- A discovery dump: quotes of the tree pasted as context. A premise is a fact with an anchor;
  the rest of what discovery read is not written down.
- An executor's narrative after a task, a "how it was done" block. The run's report goes to
  the chat, and the history is the commit messages; there is no report file.
- Status markers: a status line, a tick emoji, "in progress", "done". The checkboxes are the
  state.
- History: "previously", "was X, now Y", a changelog, a "v2" file. A plan is edited in place,
  and the refresh mode rewrites it in place.
- The executor and the model. The plan says what; the tool that runs it and the model it runs
  on are chosen at run time.
- The branch, the worktree and the shape of the pull request. Where a run happens is the run's
  first question, and a worktree run's branch is the plan's slug.
- A "verify acceptance criteria" task and a "move the plan to completed" task. Acceptance lives
  in each task, and closing the plan is the run's finalize.
- A reference to another task by number ("as in Task 3", "after Task 5"). Tasks are renumbered
  and reordered while the plan is reviewed; name the artifact or the result instead, and put
  the order in the task's `After:` line, by title.

## Language

The headers are the English strings above. The body is in the plan's language: recent plans
are Russian, older ones English. Match the document you are editing and never switch mid-plan;
a refresh keeps the language it finds.
