# Commit rules

What every subagent of a run does when it commits. Its own prompt says what it commits and
which message type it uses; this file says how. `SCRIPTS` and `JOURNAL` are the values of that
prompt, and "the checkout" is the one its prompt names for the commit: CHECKOUT, or the run
worktree of a repository when the prompt works in several.

- Commit with `EXEC_PLAN_JOURNAL=JOURNAL SCRIPTS/commit.sh "<message>" <path>...` from the
  checkout, naming every path you changed in it, relative to it. A commit is made in one
  repository: a change in another is its own commit, from that repository's checkout. The
  script sources the run's caches for the pre-commit hooks, so it needs the journal like every
  other script. It stages exactly those paths and refuses an index that holds anything else. A
  foreign staged path is another session's work: do not stage it, do not unstage it, report it
  and name your own paths.
- The script commits without a pathspec, so the hooks run on the real index and what they
  stage lands in the commit.
- Delete with `rm` and move with `mv`, never `git rm` or `git mv`: the script stages a tracked
  path that is gone from the tree as its removal, and a path `git rm` or `git mv` has already
  taken out of the index matches nothing, so the script fails before it commits. A renamed
  path is named twice, its old path and its new one, in the same commit.
- No `git add -A`, no `git add -p`, no `git commit` of your own, no `git stash`.
- The message follows the commit rules of the root `CLAUDE.md` of the checkout, and a
  commit-message hook of the project, when it has one, rejects anything else. Where the
  project states no form, the form `git log` of the branch's recent commits shows; with none
  there either, `type(scope): description`, `type` from
  feat|fix|refactor|docs|test|chore|build|ci|perf|revert, the scope the affected component,
  the description imperative, lowercase, without a trailing period.
- A commit that changes behaviour carries a body: what is now true, and why this way, with
  any line the project's commit rules add to a commit made from a plan. A lane takes both
  paragraphs from the `Result:` and the `Decision:` of its task.
- Split where a reviewer's attention splits: semantic edits, mechanical moves, generated
  output and a document fix are separate commits.
- End the message with the attribution line your session's instructions give, when they give
  one.
- Pass the message as one argument with real newlines inside the quotes. Never pipe it through
  `git commit -F -`: the hooks hang on it.
- A hook that fails names its cause. Fix the cause and commit again. A hook is never bypassed:
  no `--no-verify`, no variable that turns the hooks off (`LEFTHOOK=0`, `HUSKY=0`), no edit to
  a hook so that it passes.
