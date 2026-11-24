# Project rules

The skills of this plugin hold the procedure. What differs from one project to the next, the
place of the plans, the gates, the records that bind a design, the review tool, lives in one
rules file the skills read at their start.

## Where it is

Read in this order; the first file that exists and is not empty is used whole, and no two
are ever merged:

1. `.claude/planning/rules.md` in the top of the checkout, then in each directory above it, up
   to and not including `$HOME`. A workspace that holds many repositories side by side keeps one
   file in its own directory for all of them, and a worktree under the checkout finds the
   checkout's file.
2. `~/.config/cc-things/planning/rules.md`, the user's file for every project without one.

`scripts/rules.sh` prints the file that wins, or nothing. A skill runs it once:

```bash
bash <plugin root>/scripts/rules.sh
```

With no file, every section takes its default below. A project file that leaves a section out
takes that section's default too, not the user file's: the user file is read only when the
project has none.

## Sections

The file is markdown with these second-level headings. A skill reads the section it needs by its
heading. A section is prose: it names commands, paths and rules the way a `CLAUDE.md` would. A
heading not listed here is read as an addition to every skill's rules.

### `## Plans`

Where a new plan goes by default, and where a closed one goes. The directory may be outside
git: a workspace directory that holds several repositories side by side keeps the plans that
span them, and its plans are never committed. A path the owner gives for one plan wins over
this section. Where the file lies decides whether it is committed: "The plan's place" in
`skills/make-plan/references/form.md`. Default: `docs/plans/` at the top of the checkout,
closed plans under `docs/plans/completed/`, a plan named `yyyymmdd-<slug>.md`; outside git,
`docs/plans/` in the directory the session starts in, and an untracked plan's closed plans
under `completed/` beside it.

### `## Trunk`

The branch a run starts from and a pull request lands on, and how a run names its own branch.
Default for the name: `<type>/<slug>`, the commit type of the plan's Goal and the plan's slug.
Default for the trunk: the branch `origin/HEAD`
points at (`git symbolic-ref --short refs/remotes/origin/HEAD`), else `main`, else `master`.

### `## Gates`

The command a change to each surface must pass, and the generators and their drift check. It
may also name the files the generators write, the lines a gate command rewrites in a
hand-written file, the order of the whole-tree checks, the test command of each component, and
which components a generator input touches. A section may say only where the gates are written,
such as "the Gates section of the root `CLAUDE.md`". Default: the gates the project's `CLAUDE.md` files name; with none named, the
build, the lint and the tests the project's own build file defines.

### `## Environment`

What a checkout needs before it builds: dependencies a fresh worktree installs per surface,
caches to set, services or stands used one at a time, how a run sees one up and takes it down,
a command that must never run because it takes down every stand, and the suites that act on a
stand with how to prove they build without running them. It also says how one repository builds
against another repository's run branch that is not pushed yet: a `go.work` or a `replace` to
the other repository's run worktree, a path dependency, and what comes out of the branch before
its pull request. Default: nothing; a repository builds only against the published versions of
the others.

### `## Records`

Where the records that bind or explain a design live: requirements, decision records, a
glossary, vendor documents, field notes, the product requirements, and a reference product whose
behaviour a design is compared against, with where its code lives. For each kind of record the
section says whether it binds a choice or only explains one. It also says what a change does
with an explaining record it goes against (rewrite it in place, mark it for the owner), how a
test proves a binding record, and which judgements only the owner makes. Default: none; a claim is checked against the code and the vendor's
document only, and every choice is the owner's to answer as a fork.

### `## Consumers`

Where to search for the readers and writers of a shape a plan changes, tests and scripts
included. Default: the whole checkout, `rg` without a path.

### `## Plan form`

What a plan carries beyond the form in `skills/make-plan/references/form.md`: a section of its
own, a line per task, a check a decision must pass, and a check discovery and the plan review
run. Default: the form alone.

### `## Review`

The revmux profiles and lenses of a plan round, a plan recheck, the first and the later
branch rounds and a light run, the conventions a review holds a branch to, and the findings a
review drops as noise. Default: the profiles `plan` and `plan-recheck` for a plan,
`comprehensive` for the first branch round and `final` for the rounds after it, `claude-only`
with the lenses `bugs,impl,tests` for a light run; without the `revmux` binary, the
`plan-review` agent.

The `plan` lens and the `plan` and `plan-recheck` profiles ship with this plugin under
`revmux/`, and revmux finds them once that directory is linked into its user layer (see the
README). A project's own `.revmux/` file of the same name replaces the plugin's.
