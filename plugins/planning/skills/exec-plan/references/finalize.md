# Finalize prompt

The prompt the finalize subagent gets once every repository's review has ended clean or after
its third round. One subagent regroups the history of every repository of the plan and then
closes the plan once. Substitute every placeholder before sending it: the subagent runs in a
fresh context and sees nothing of this session or of the rounds.

| Placeholder | Value |
|---|---|
| `REPOS` | every repository of the plan, one per line, in the order of the journal's `repos`: `<repo>`, run worktree `<path>`, branch `<name>`, base `<sha>`, the content of `<journal>/base.<repo>`, trunk `<name>`, the trunk the run resolved for it |
| `PLAN` | absolute path of the plan, the one the journal's `plan` names |
| `MODE` | `tracked`, the plan is the copy in the home repository's run worktree and is closed by a commit there, or `untracked`, the plan is closed by a plain `mv` and never committed |
| `HOME` | in a tracked plan, the absolute path of the home repository's run worktree, which holds PLAN; `none` in an untracked plan |
| `SLUG` | the plan's slug, the journal's directory name |
| `JOURNAL` | absolute path of the run's journal |
| `SCRIPTS` | absolute path of the skill's `scripts/` in the plugin, `${CLAUDE_PLUGIN_ROOT}/skills/exec-plan/scripts` expanded |
| `RULES` | absolute path of the plugin's `scripts/rules.sh`, `${CLAUDE_PLUGIN_ROOT}/scripts/rules.sh` expanded |
| `PREFLIGHT` | the block Step 2 of the skill produced |
| `OPEN` | absolute path of the plan before the close, the same path as `PLAN` |
| `CLOSED` | absolute path of the plan after the close: in a tracked plan, the closed-plans directory the `Plans` section names inside HOME, plus the plan's file name; in an untracked plan, the closed-plans directory beside the plan, as the plan form places it, plus the file name |

## Prompt

You are closing a plan run: the history of every repository's run branch is regrouped, and then
the plan moves from OPEN to CLOSED. No human is available: never ask
a question, never pause for input, never call a tool that asks the user. You have no Agent
tool.

Paths, absolute, used as written:

- the repositories list, each repository with its run worktree, branch, base and trunk; every
  command of a repository runs from its run worktree:
REPOS
- plan: PLAN, a MODE plan; in a tracked plan its run worktree is HOME
- the close: OPEN → CLOSED
- journal: JOURNAL. Every shell call that runs or sources a file of SCRIPTS sets it first,
  `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh '<line>'`: the scripts refuse without it
- scripts: SCRIPTS/commit.sh and SCRIPTS/progress.sh
- project rules: `bash RULES` from a repository's run worktree prints the rules of that
  repository, or nothing. A section is read by its heading; a section the file leaves out takes
  the default that `$(dirname RULES)/../references/rules.md` gives it
- preflight of this run:
PREFLIGHT

### Read first

1. The commit rules of the root `CLAUDE.md` of each run worktree in full: the message format,
   the split where a reviewer's attention splits, the staging rules, the body and the lines a
   commit made from a plan carries. `SCRIPTS/../references/commit.md` says what holds where
   the project states none.
2. Each branch: in its run worktree, `git log --oneline <base>..HEAD`,
   `git diff --stat <base>...HEAD`, then the diff itself, once, to see which kinds of change it
   holds and which components they touch.
3. PLAN: `## Decisions`, and the `Result:`, `Decision:` and `Repo:` lines of every task. The
   reset below drops the bodies of the branch's commits, and the plan is where the reason of
   each change is kept, so the bodies of the new commits are written from it.

### Regroup the history

Each branch's commits are the shape the work was executed in: one or more per task, the
commits that marked the plan, then the fixes of the review rounds. The reader of the pull
request reads it in another shape, by kind. Regroup every repository of the repositories list,
one after another, each from its own base, in its own run worktree:

1. `git status --porcelain` prints nothing. Anything printed is a stop:
   `[blocker] finalize: <repo>: dirty tree: <paths>`.
2. Keep the tip before anything moves: `git branch backup/SLUG-<yyyymmddHHMM> HEAD`, at the
   current tip and not an earlier one, because the check below compares against it. Note
   `git rev-list --count <base>..HEAD`, the count before.
3. `git reset <base>`. The working tree keeps every change of the branch and the index is the
   base, so each group is staged from nothing. Never `--hard`, and never `--soft`: a soft
   reset leaves the whole branch staged, and `commit.sh` refuses an index that holds more than
   the paths it is given.
4. Commit each group with `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <path>...`
   from the run worktree, naming the paths of that group and nothing else. The staging and
   message rules are in `SCRIPTS/../references/commit.md`: read it before the first commit.
   Here the index starts empty, so there is no `git add` of any kind. A group that changes
   behaviour gets a body: what is now true, from the `Result:` of the tasks whose changes the
   group holds; why this way, from their `Decision:`; then any line the project's commit rules
   add to a commit made from a plan, with the plan's path after the close: CLOSED relative to
   HOME in the home repository of a tracked plan; in another repository of a tracked plan, the
   home repository's name, a slash, and CLOSED relative to HOME; in an untracked plan, which no
   repository holds, the plan's file name alone. No absolute path goes into a commit.
5. Prove nothing moved: `git diff backup/SLUG-<stamp> HEAD` prints nothing, and
   `git status --porcelain` prints nothing. Anything printed is a stop:
   `[blocker] finalize: <repo>: the regroup lost <paths>`. The backup branch holds the tip.

A stop in one repository leaves the repositories after it as they are and the plan where it
is. A stop after the reset of step 3 leaves that branch part way, the rest of its changes
uncommitted: do not put it back yourself. Name the backup branch in the `[blocker]` line and
the report, since `git reset --hard backup/SLUG-<stamp>` in that run worktree is how the
owner restores the tip before the run continues.

The groups follow the project's commit rules, and where they say nothing: a semantic edit per
component, a mechanical move, generated artifacts, a large documentation rewrite, each apart
wherever they can be separated, each in the project's message form. In the home repository of
a tracked plan, the plan with its ticks is a documentation change and travels with the
documentation group, or alone as `docs(plans): …` when the branch has no other. One commit for
the whole branch is wrong unless the branch is one small change; a commit per plan task is
wrong too, because that is the shape the work was executed in and not the shape it is read in.
The bar is the reader's attention, and it is a count: past a dozen or so commits the branch is
regrouped, however well each commit is worded on its own. A branch that is already few and
already split by kind keeps its commits; the backup and the check of step 5 are still made,
and "already reads that way" excuses nothing else.

A repository's trunk is not merged into its branch and the branch is not rebased onto it:
bringing the branch onto the trunk is the pull request's step, after the run, and a merge
commit between the base and `HEAD` is what `base.sh` refuses on the next run.

### Close the plan

Once every repository is regrouped, close the plan by MODE. Its text does not change: no
status, no date, no note.

- `tracked`: from HOME, `mkdir -p "$(dirname CLOSED)"` when the directory does not exist yet,
  then `mv OPEN CLOSED`, a plain `mv`, then
  `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "docs(plans): close the SLUG plan" <OPEN
  relative to HOME> <CLOSED relative to HOME>`, the message in the project's commit form: the
  old path, gone from the tree, is staged as its removal and the new one as its addition, in
  one commit. Then `git status --porcelain` in HOME prints nothing.
- `untracked`: `mkdir -p "$(dirname CLOSED)"`, then `mv OPEN CLOSED`, a plain `mv`, and
  nothing else: no `git` command touches it and nothing is committed.

### Journal

Only through `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/progress.sh '<line>'`, one call per line, never
a redirect into the file. The line goes in single quotes, a single quote inside it written
as `'\''`: in double quotes a backtick or a `$(…)` in the line runs as a command. The lines:

- `finalize: <repo>: history <n> → <m> commits, backup/SLUG-<stamp>`, one per repository
- `finalize: plan closed, CLOSED`, with CLOSED as the absolute path
- `[decision] finalize: <repo>: <what you decided>, because <why>`, one per judgement call, the
  grouping included when the kinds were not plain
- `[deviation] finalize: <repo>: <what differs from the plan's letter>, because <why>`
- `[blocker] finalize: …` when you stopped early

The bracketed prefixes are exact; the run collects them verbatim for the owner. Log only what
happened.

### Report

Finish with, per repository: the commit count before and after and the backup branch; each
group commit's SHA and subject; the diff check and what it printed. Then the plan's new path;
every `[decision]`, `[deviation]` and `[blocker]` line verbatim; any error you hit and how it
ended.

After the close and the journal, STOP.
