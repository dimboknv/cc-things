---
name: make-plan
description: >
  Use when a piece of work needs a plan, which `/planning:exec-plan` runs in parallel lanes:
  writing one from a description of the work, or refreshing an existing plan against the tree
  before it runs. Not for a mechanical edit one session makes in place. Triggers: "make a
  plan", "write a plan", "plan this", "new plan", "refresh the plan", "update the plan", "is the
  plan still valid", "parallel plan", "составь план", "напиши план", "нужен план", "новый план",
  "актуализируй план", "обнови план", "план ещё актуален".
user-invocable: true
---

# Write a plan

A plan says what is true when it is closed, the choices the work applies, the facts it rests
on, and the tasks that get there. It stops above signatures, file lists and values; those are
the executor's. The form, the sections, the shape of a task, the addresses, what a plan never
carries, is [`references/form.md`](references/form.md), and this skill does not restate it.
This skill is the procedure between a request and a plan the owner hands to
`/planning:exec-plan`, which runs the tasks in waves of parallel lanes by their `After:` lines.

The argument is a description of the work, the summary a `/planning:brainstorm` session ended
on, or the path of a plan in the plans directory. A path selects the refresh mode at the end of
this file.

## The project rules

Load them once, at the start:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh
```

It prints the project's rules file, its path on the first line as `<!-- rules: <path> -->`, or
nothing. The sections, and the default each takes when the file is absent or leaves it out, are
[`../../references/rules.md`](../../references/rules.md). This skill reads:

- `Plans`: the default directory of a new plan, the file name, where a closed plan goes;
- `Gates`: where the gate of each surface is written, which Execution links;
- `Environment`: what a checkout needs, which Execution does not repeat;
- `Records`: the records that bind a design, the records that only explain one, and the
  judgements only the owner makes;
- `Consumers`: where to search for the readers and writers of a shape, the other repositories
  included;
- `Plan form`: what a plan of this project carries beyond `references/form.md`, and what
  discovery checks beyond Step 2;
- `Review`: the profiles and lenses of the plan rounds.

A heading the schema does not list is an addition to this skill's rules too. Keep the rules
file's path: the review rounds and the `plan-review` agent get it.

## Step 1: is this a plan?

A mechanical edit is not. A rename with a grep behind it, a value in one artifact, a fix one
session makes and gates in place: answer "no plan needed", name the edit in one line, and
stop. The owner asks for the edit if that is what they want.

Everything else is one plan. Never propose a series, a first phase or a follow-up plan as a
way to keep this one small. What the owner leaves out goes to Out of Scope with where it goes;
a hole found while designing goes into the plan with its price (Step 3). A plan runs full or
light; Step 4 chooses, and light is the way a small piece of work stays cheap, never a cut.

Between the request and the menu, the questions are the forks and the go for discovery,
nothing else. What the form or the tree already settles is not asked: the file is named and
headed from its Goal, the executor's gate is linked in Execution and only a departure from it
is written there, the language is the request's.

A confirmed `/planning:brainstorm` summary, in the chat above or in the file the owner names,
is settled input, and nothing it settled is asked again. Its decisions go into Decisions in the
summary's words, with the reason the summary records. What it lists as the agent's own
proposals, and what it lists as unresolved, are forks of Step 3, asked before the plan is
written. Discovery still runs its anchors: a summary carries the owner's choices, not the
tree's state.

## Step 2: discovery is verification

Discovery does not collect context. It checks the facts the design will rest on against the
tree, and it checks what the reviews check later, the lens in
[`../../revmux/lenses/plan.md`](../../revmux/lenses/plan.md):

- premises: each fact a decision or a task depends on, with its anchor run now, a file with a
  quoted string `rg` finds or a command with the line of its output;
- consumers of the old shape: every reader and writer of a contract or a stored shape the
  plan changes, found with `rg` over the places the `Consumers` section names, tests included:
  the tests and specs that pin the old behaviour, the test suites of a binary, the end-to-end
  suites, the seeds and fixtures, the build and deploy scripts, and the code written by hand
  beside a generated client. Their areas go into `Where:`. When the `Consumers` section names
  other repositories, the search runs in each of them too, and a reader or writer found in
  another repository is a task of that repository, with its `Repo:` line;
- outside systems: a claim about how a system the repository does not own behaves (an engine,
  a library, a vendor's device or protocol, a browser API) is a premise like any other. Its
  anchor is the vendor's document or the source of the version the tree pins, in the
  dependency cache of its language (`go env GOMODCACHE`, `node_modules`, the virtualenv); what
  no anchor confirms is a fork, not a premise;
- the owner of each fact: the artifact that owns a value or a vocabulary, as the project's
  `CLAUDE.md` or the `Records` section names it, else the artifact that applies it (a
  migration, a schema, a contract file, a module), so the plan names it and does not restate
  it;
- processes with state: a consumer window, a cache, a map in one replica, a key-value bucket,
  a queue, a scheduled job the plan touches, so each gets an invariant and a bound;
- lists across a boundary: a list or a batch the plan sends to another service, an engine or a
  device, so each gets the receiver's limit with its anchor and what the sender does past it;
- pairs of tasks that could run together: for every two tasks with no path between them in
  `After:`, the files both would edit, found the same way as the consumers above. A file both
  edit goes into the Shared files table of Execution with the task that is second, or the
  second task gets an `After:` on the first; a shared file in neither is what the integrator
  meets as a conflict. A task that uses something one at a time on the machine, a stand or an
  end-to-end suite, gets a `Needs:` line;
- the edge of the domain: the work of one domain stays in one plan and is not cut by the
  services that read it or by the routes of an API. `## Out of Scope` points only at the
  plan of another domain, and one way. A piece cut out of this plan is checked to have a
  taker: a plan file that exists and says so;
- what the project adds: a check the `Plan form` or `Records` section gives discovery runs
  here too, and its findings become premises and forks like the rest.

Read first what the request names: the areas, the records of the domain the `Records` section
names, the skills of the surfaces. Then grep those records by the words of each mechanism a
decision applies, not by the area: `version`, `etag`, `if-match`, `idempot`, `lock`, `retry`,
`outcome`, the mechanism's own name. A record in force that already decided the opposite sits
under another domain's title. Grep them also by the words of each consequence of a decision,
what it stops keeping, raising, checking or recording: `evict`, `age out`, `retention`,
`raised`, `audit`, `shard`, `exit`. A conflict reaches a plan through a consequence more often
than through a mechanism's name. A binding record's text that this plan's Owner Sign-off
rewrites is read as in force: every decision about the same kind of record is held to the new
text. The same search runs over the conventions of the surfaces, the skills the project holds
under `.claude/skills/` and the installed plugins hold for its surfaces, with their
`references/`: the run's review holds the branch to them, so a decision that departs from one
cites it and says why.

Every hit is cited by the decision it touches. A record the `Records` section names as
rationale does not bind the choice: a decision that goes against one carries a task rewriting
it in place, in the way that section says, and its acceptance goes into Owner Sign-off, not
into a separate question. A record it names as binding does bind, and a decision against one
is a fork. That fork offers, beside the mechanism that obeys the record, a clause added to the
record at no cost in machinery, with the clause's exact words: changing a binding record is the
owner's, and the owner decides by the words. With no `Records` section, a claim is checked
against the code and the vendor's document only, and every choice is the owner's fork.

When the tree is wider than one session reads, name the wave before launching it: how many
`Explore` agents, one to three, and what each verifies, one line each. Launch them after the
owner's go, never before. Their output becomes premises and forks; what no decision depends on
is not written into the plan.

## Step 3: forks, one at a time

Before the first fork, the owner gets the list: how many forks discovery left, each named in a
few plain words. Every fork then opens with its place, "fork 2 of 5", in the language of the
conversation. A fork that an answer settles or adds changes the count, and the next message
says so: "after this answer 3 are left, one added: …".

Ask one fork, wait for the answer, then ask the next. A fork is a choice the tree does not
settle: a false premise, a mechanism, a boundary, a hole found in discovery. It opens with the
problem in one or two sentences, what breaks or stays unsettled without the choice, and then
takes the form of [`brainstorm`](../brainstorm/SKILL.md), "A fork", "The fork page" and "The
shape of a message": plain words by role before any option, two or three options with the
simplest first, one scenario with concrete names for each, whether an option follows the
industry's way and whose, the price as what it adds at run time, one recommendation, and
inside agterm a page in the overlay rather than a message. That form has one home, and this
file does not repeat it.

A hole found while designing is a fork with its price, and the answer goes into the plan,
never to a backlog item or to "decide during implementation". A choice the owner alone makes,
the judgements the `Records` section reserves to the owner, accepting a rewritten record,
taking a tool out of the loop, is asked the same way, and the answer is written into Owner
Sign-off with the consequence the owner accepts. When the owner takes the recommended option
without comment, restate it in one line ("so X, because Y") so the plan carries the reason.
When the owner asks what a word means, or says "explain", explain and ask again without
choosing. Something the skill adds on its own, a monitor, a lock, a name, is its own fork.

## Step 4: write

Write the plan where the owner said, else into the directory the `Plans` section gives, under
the file name that section gives, in the form of [`references/form.md`](references/form.md) with
what the `Plan form` section adds, in the language of the request. Its place decides whether it
is tracked or untracked, as "The plan's place" in the form says: `git check-ignore -q <plan>`,
run from the plan's directory, exits 1 for a tracked plan, and 0 (ignored) or 128 (no work
tree) for an untracked one. Every task that changes a repository other than the home one
carries `Repo:`, and in an untracked plan every task does.

Before the menu, hold it to the lens yourself, once: every anchor runs, every decision is an
assertion with a reason, the alternative it rejects and an acceptance that can fail, no detail
the executor settles from the tree is written as a decision, no choice is left to the executor,
every rename or removal names in `Where:` each surface its inventory runs over, Skills in
Execution name skills the project and the installed plugins hold today, every `After:` names a
task that exists by its title and gives a reason, every file two tasks edit is in the Shared
files table or behind an `After:`, no two tasks that can run together carry the same `Needs:`,
and every task changes one repository, the one its `Repo:` names or the home one. Every
`acceptance:` command is run on the tree as it stands, and it must fail there, because the work
is not done yet: a check that something is gone still finds it today, and a check that something
is there does not find it today. One that already passes today proves nothing and is rewritten
until it fails. What that pass finds is edited in now, not left for a review to find.

The search commands run through
[`scripts/acceptance.py`](scripts/acceptance.py), from the directory the session started in,
the one `Repo:` lines are relative to:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/make-plan/scripts/acceptance.py <plan>
```

It runs every `rg`, `grep`, `awk` or `git grep` inside an `acceptance:` item from the root of
the task's repository, groups the hits by file and marks a file outside the task's `Where:` as
`outside Where:`. A task it skips for want of a repository lacks its `Repo:` line. Gates
(`make`, `go`, `npm`) it skips; run those by hand. Every marked file is read: it is the task's
own and `Where:` gains its area, or the term matches a name the task keeps, another task's file
or a foreign meaning, and the term is narrowed or the foreign meaning is named in the
acceptance. An inventory term that matched what the task keeps was the most frequent major
finding of the plan rounds.

Choose the mode before the menu, by the conditions of the Mode item of Execution in
[`references/form.md`](references/form.md). When every one holds, write the Mode line with its
reason; when one is in doubt, the plan is full and carries no Mode line. The owner sees the
mode in the plan and changes it by editing the line. A light plan is the same form, shorter
where nothing real fills a section, never padded with a decision nobody had to make.

## Step 5: the menu

One question, five items for a tracked plan, the recommended item first and marked:

1. revmux `plan`, the two-model round;
2. agent `plan-review`, the one-model pass;
3. webrev, the owner's own reading;
4. commit;
5. done.

An untracked plan is never committed, so its menu has four items: commit is not offered.

The menu is a closed question, asked as
[`../../references/questions.md`](../../references/questions.md) says; the free line takes an
edit the owner wants first. In AskUserQuestion the five items of a tracked plan drop done, which
the owner gives in the free field. A verdict the menu comes back with is said in the reply
before it opens.

For a plan no review has read, the round is the recommendation; for a light plan it is the
agent, listed first, and the round stays on the menu for the owner to pick. After a review
(items 1 to 3) the menu comes back with the verdict from "Review findings" below and the item it
recommends next: a `plan-recheck` round after edits, or on `ready` commit for a tracked plan and
done for an untracked one.

### The lens and the profiles

The plugin ships the lens `plan` and the profiles `plan` and `plan-recheck` in
[`../../revmux/`](../../revmux/): `lenses/plan.md`, `prompts/profiles/plan.md`,
`prompts/profiles/plan-recheck.md`. revmux reads a lens or a profile from three layers, its
built-in set, the user layer `~/.config/revmux/` and the project layer `.revmux/` of the working
directory, and the project layer wins by name. The plugin's README has the user link the
plugin's `revmux/` files into the user layer; that link is how a round finds them. A project's
own `.revmux/lenses/plan.md` or `.revmux/prompts/profiles/plan.md` replaces the plugin's whole.
The `Review` section may name other profiles for the plan round and the recheck; its names win.

The lens is read by agents that never see this skill, so the round hands them two paths: the
form, `${CLAUDE_PLUGIN_ROOT}/skills/make-plan/references/form.md` expanded to its absolute
path, and the rules file the loader printed. The lens takes both from `scope.md`.

### 1. revmux `plan`

Load the `revmux:revmux` skill and follow it, with what a plan changes:

- The subject is a proposal, not a diff. `scope.md` names the plan file, says to read it in
  full, and lists the areas its `Where:` lines name as the tree to read it against. It names the
  form by its absolute path as "the form", and the rules file by its absolute path as "the
  project rules", or says "project rules: none". In a plan with more than one repository it
  lists the areas by repository, each repository by its path. `goal.md` is the plan's Goal in
  two lines; the criteria are the lens's and are not restated.
- The task id is `plan-<slug>`, the slug being the file name without its date and extension,
  as `.revmux/tasks/` names a plan's rounds. The branch's rounds under `/planning:exec-plan`
  run under the bare slug, and the two are never joined. Rounds are `01-initial`,
  `02-after-fix`, `03-final`.
- The first round's profile is `plan`: two models at xhigh, each carrying the plan, impl and
  adversarial lenses. Preflight with that profile. When revmux does not know the profile, the
  user layer lacks the link: say so, point at the README's step, and offer item 2. When a
  binary the profile needs is missing, say which and offer item 2.
- Every later round of the task is `plan-recheck`: did the edits close the last round's
  findings, and did they break anything they touch, with nothing below major. Its `scope.md`
  lists every section edited since the previous round, each with the finding it answers, beside
  the form and the rules file. A full `plan` round is not run twice on one plan: a full pass
  over text already read digs one level deeper each time, and across the plan rounds of the
  project these skills were written in, the later ones raised more majors than the first (307
  against 244). At most two rechecks: a critical or major still standing after the second goes
  to the owner as a fork in the form of Step 3, not to a third recheck.
- Where the round runs. The project layer with the profile and the lens is read from the
  process working directory, and the run archive lands in its `.revmux/tasks/`, which git
  should ignore. A tracked plan's round runs from the main checkout of its home repository, the
  first entry of `git worktree list`, with `--workdir` the checkout the plan sits in, that main
  checkout or a worktree. An untracked plan's round runs from the directory that holds the
  repositories, the one the session started in, with `--workdir` that same directory. Headless,
  unless the owner asks to watch.
- Read `sources.degraded` before the findings. A round with a degraded source is partial: say
  so and offer to rerun the missing source. Its silence is not a verdict.

### 2. agent `plan-review`

Dispatch the [`plan-review`](../../agents/plan-review.md) agent. An agent gets no plugin
variables, so its prompt carries four absolute paths:

- the plan;
- the lens: the project's `.revmux/lenses/plan.md` when it exists, else
  `~/.config/revmux/lenses/plan.md` when it exists, else
  `${CLAUDE_PLUGIN_ROOT}/revmux/lenses/plan.md`, the order revmux reads them in;
- the form, `${CLAUDE_PLUGIN_ROOT}/skills/make-plan/references/form.md`;
- the rules file the loader printed, or "none".

It runs in the session's working directory, so a task's `Repo:` names the same directory for it
as for this skill. It reads the lens, the form and the rules, applies them once on one model,
and returns findings by section, each `fact:`, `fork:` or `question:` with a severity, and a
verdict of its own. Its findings are handled like a round's; the verdict this skill gives is its
own.

### 3. webrev

Load the `webrev` skill and open the plan file itself as a page in the agterm overlay. Every
annotation gets one line in the reply,
`<line> <the comment, shortened> -> edited | answered | disagree: <why>`. A question is
answered and changes nothing. A change is an edit to the plan. A disagreement is quoted back
with the reason. The owner's annotation is never noise and never dropped without a word.
After edits the page opens again on the plan, as `webrev` says, until a review comes back
empty or cancelled. Outside agterm the page cannot open: say so and return to the menu.

### 4. commit

Offered for a tracked plan only. Into the current branch, whatever it is; never create or
switch one. The commit goes through the script `/planning:exec-plan` commits with, run from the
root of the checkout the plan sits in:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts/commit.sh "<message>" <plan>
```

It stages the plan by its explicit path, refuses an index that holds anything else, and
commits without a pathspec, so the hooks run on the real index and what they stage lands in
the commit. A refusal is a stop: the paths it lists are another session's work in the same
checkout. Show them to the owner, stage nothing, unstage nothing, commit nothing; the item
runs again once the index holds nothing else.

The message is in the commit format of the project's `CLAUDE.md`, a docs commit that says what
the plan does. A red pre-commit hook is fixed, never bypassed. Pushing is the owner's. Then
print `/planning:exec-plan <plan>` and stop.

### 5. done

Stop. For a tracked plan, say in one line that the plan is in the working tree and not
committed. For an untracked plan, say where it lies and print `/planning:exec-plan <plan>`.

## Review findings

A finding, from a round, from the agent or from an annotation, is input, not authority. Each
is one of three things and gets one of three answers:

- a fact, the plan says one thing and the tree another: check the tree, edit the plan, say
  what was edited;
- a fork, the plan needs a choice it does not make: a question to the owner in the form of
  Step 3, and the plan waits for the answer;
- noise, a demand the lens says not to make (a test checkbox, a file list, a commit order, a
  value the owning artifact carries), a style preference, or a claim the tree refutes:
  dropped, with the reason in the reply.

Then the verdict, one line, on the severities the lens defines. `ready` when no `critical`
or `major` finding is left: every such fact edited, every such fork answered. A `minor` is
edited when the edit is one line at the place it names and noted in the reply otherwise; it
never holds the verdict. Otherwise `another round: <reason>`, naming the critical or major
finding that weighs most (`another round: two forks in Task 5`). The verdict is this skill's:
the round's schema carries a severity and no verdict, the lens defines the severities and
carries no verdict, and the agent's is one more input.

## Refresh: `/planning:make-plan <existing plan>`

The argument is a plan that is not among the closed ones. The plan is brought to the tree as it
stands and reads afterwards as if written today: no "was", no "now", no note of what moved. It
keeps its language, and a closed task keeps its ticks. Not the usual removal of a done task.

1. Since when. The mark is a time. For a tracked plan it is the date of the last commit that
   touched it, `git log -1 --format=%cI -- <plan>` in the home repository; for an untracked
   plan, or a tracked one no commit has touched yet, it is the file's modification time. Then,
   in each task's repository, `git -C <repository> log --since=<mark> -- <area>` for every area
   its `Where:` names. What moved there is what the refresh reads; the rest of the tree is not
   reread.
2. Every premise, by its anchor. Run each. In place: nothing. The fact holds but the quote is
   gone: the anchor is rewritten to what `rg` finds today. The fact is false: a fork for the
   owner in the form of Step 3, and the decisions and tasks that rest on it wait for the
   answer. A fact the log shows the plan now depends on is a new premise with its anchor.
3. Decisions. Each record a decision cites still exists, is still in force and still says what
   the decision leans on; one that does not is a fork. A decision the tree already applies, or
   can no longer apply, is a fork too.
4. Skills in Execution against the skills the project and the installed plugins hold as they
   stand: a skill renamed, split or added for a surface the plan touches is renamed, replaced
   or added in the list.
5. Open tasks whose `Where:` area moved are reread against the tree, and a checkbox the tree
   no longer matches is edited.
6. Every `After:` still names a task that exists; every file of the Shared files table is still
   edited by the tasks it names, and no new shared file has appeared, found by the search of
   Step 2; every `Needs:` still names something one at a time on the machine.
7. A light plan's Mode still holds: a reader or writer of a changed shape that the log brought
   in, or a choice the tree reopened, makes the plan full, and the Mode line goes.

Everything is edited in place. Then the menu of Step 5, as for a new plan.

## Common mistakes

| Mistake | Fix |
|---|---|
| Asked a question the tree answers | Run the `rg`, write the premise with its anchor |
| Re-asked what the `/planning:brainstorm` summary settled | Its decisions are Decisions; only its proposals and its unresolved are forks |
| Wrote a premise without running its anchor | Run it now; a premise is a checked fact |
| A premise about an engine or a library from memory | Its anchor in the vendor's document or the pinned source; none, a fork |
| Read the records of the area only | Grep the records the `Records` section names, and the skills, by the words of each mechanism and each consequence |
| Consumers searched in production code only | Tests, binary suites, end-to-end suites, seeds, build and deploy scripts and the code beside a generated client too |
| Launched the wave before the go | Name the agents and what each verifies, then wait |
| Two forks in one question | One fork, one answer, then the next |
| Options without a price, or the new mechanism first | Price each; the simplest first |
| A hole sent to the backlog or left to the executor | It joins the plan, as a fork with its price |
| Proposed a series of plans | One plan; the rest is Out of Scope with where it goes |
| Ignored the project rules | Load them at the start; a section the project leaves out takes its default |
| Took a degraded round as clean | Lead with `sources.degraded`; offer the rerun |
| Applied a finding without checking the tree | Fact, fork or noise, and only a fact is an edit |
| Dispatched `plan-review` with the plan path alone | The plan, the lens, the form and the rules file, each by its absolute path |
| A refresh that says what changed | Edit in place; the plan reads as written today |
| Committed with its own `git add` and `git commit` | `commit.sh`; a refusal names another session's paths and is a stop |
| Made a branch for the plan | The current branch, whatever it is |
| Offered commit for a plan outside git or in an ignored directory | An untracked plan's menu has no commit; the run closes it with a move |
| A task of another repository without `Repo:`, or one task across two repositories | `Repo:` on the line after `Where:`; two repositories are two tasks joined by `After:` |
| Two tasks share a file and neither waits for the other | The Shared files table with who is second, or an `After:` |
| An `After:` by number | By title, with the reason |
| Ran the acceptance commands and read only the exit code | `scripts/acceptance.py`; every file `outside Where:` is read |
| Ran a second full `plan` round after edits | `plan-recheck`, its scope the edited sections and the findings they answer; two at most, then the owner |
| Marked a plan light because its diff will be small | The Mode conditions of `form.md`: one executor, no open choice, every reader and writer of a changed shape named; in doubt, full |
| Padded a light plan with decisions to fill the sections | One line saying the section holds nothing real |
