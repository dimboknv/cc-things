# Commit rules

What every subagent of a run does when it commits. Its own prompt says what it commits and
which message type it uses; this file says how. `SCRIPTS`, `CHECKOUT` and `BRANCH` are the
values of that prompt.

- Commit with `SCRIPTS/commit.sh "<message>" <path>...` from CHECKOUT, naming every path you
  changed. It stages exactly those paths and refuses an index that holds anything else. A
  foreign staged path is another session's work: do not stage it, do not unstage it, report it
  and name your own paths.
- The script commits without a pathspec, so the hooks run on the real index and what they
  stage lands in the commit.
- Delete with `rm` and move with `mv`, never `git rm` or `git mv`: the script stages a tracked
  path that is gone from the tree as its removal, and a path `git rm` or `git mv` has already
  taken out of the index matches nothing, so the script fails before it commits. A renamed
  path is named twice, its old path and its new one, in the same commit.
- No `git add -A`, no `git add -p`, no `git commit` of your own, no `git stash`.
- The message follows the root `CLAUDE.md` Git section: `type(scope): description`, `type`
  from spike|feat|fix|refactor|docs|test|chore|build|ci|perf|revert, the scope the affected
  component (`skills`, `api-gateway`, `deploy`, ...), the description imperative, lowercase,
  without a trailing period. `tools/hooks/commit-msg.sh` rejects anything else.
- A commit that changes behaviour carries the body the root `CLAUDE.md` Git section asks for:
  what is now true, why this way, and the `Plan:` line. A lane takes both paragraphs from the
  `Result:` and the `Decision:` of its task.
- Split where a reviewer's attention splits: semantic edits, mechanical moves, generated
  output and a document fix are separate commits.
- End the message with the attribution line your session's instructions give, when they give
  one.
- Pass the message as one argument with real newlines inside the quotes. Never pipe it through
  `git commit -F -`: the hooks hang on it.
- A hook that fails names its cause. Fix the cause and commit again. A hook is never bypassed:
  no `--no-verify`, no `LEFTHOOK=0`, no edit to a hook so that it passes.
