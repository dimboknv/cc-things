# Project rules

The skills of this plugin hold the procedure. What differs from one project to the next, the
place of the plans, the gates, the records that bind a design, the review tool, lives in one
rules file the skills read at their start.

## Where it is

Two places, read in this order. The first file that exists and is not empty is used whole; the
two are never merged.

1. `.claude/planning/rules.md` at the root of the checkout, the project's file.
2. `~/.config/cc-planning/rules.md`, the user's file for every project without its own.

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

Where plans live and where a closed one goes. Default: `docs/plans/`, closed plans under
`docs/plans/completed/`, a plan named `yyyymmdd-<slug>.md`.

### `## Trunk`

The branch a run starts from and a pull request lands on. Default: the branch `origin/HEAD`
points at (`git symbolic-ref --short refs/remotes/origin/HEAD`), else `main`, else `master`.

### `## Gates`

The command a change to each surface must pass, and the generators and their drift check. A
section may say only where the gates are written, such as "the Gates section of the root
`CLAUDE.md`". Default: the gates the project's `CLAUDE.md` files name; with none named, the
build, the lint and the tests the project's own build file defines.

### `## Environment`

What a checkout needs before it builds: dependencies to install per surface, caches to set,
services or stands used one at a time and how a run tears them down. Default: nothing.

### `## Records`

Where the records that bind or explain a design live, and which of them binds: requirements,
decision records, a glossary, vendor documents, the product requirements. Also the judgements
only the owner makes. Default: none; a claim is checked against the code and the vendor's
document only, and every choice is the owner's to answer as a fork.

### `## Consumers`

Where to search for the readers and writers of a shape a plan changes, tests and scripts
included. Default: the whole checkout, `rg` without a path.

### `## Plan form`

What a plan carries beyond the form in `skills/make-plan/references/form.md`: a section of its
own, a line per task, a check a decision must pass. Default: the form alone.

### `## Review`

The revmux profiles and lenses of a plan round, a plan recheck, a branch round and a light
run, and the conventions a review holds a branch to. Default: the profiles `plan` and
`plan-recheck` for a plan, `comprehensive` for a branch, `claude-only` with the lenses
`bugs,impl,tests` for a light run; without the `revmux` binary, the `plan-review` agent.
