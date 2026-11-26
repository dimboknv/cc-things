---
name: fork-states-diagram-design
description: A fork about the states an object passes goes to diagram-design, not to the page's flow. Run with --allow-tools Write --ablation none.
tags: [brainstorm, pictures]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write]
---

Run `/planning:brainstorm` on the design below.

Context for this check:
- Treat this session as running inside agterm: in the real terminal `AGTERM_SESSION_ID` is set. This sandbox has no agterm, so do not run `fork.py` or `agtermctl`.
- No peer.
- The frame and the facts are settled and listed below. Do not read the tree, do not propose research, ask no question.
- Go straight to the first fork. Write its fragment to `./fork-1.html` in the markup of the skill's `page.md`, with its pictures drawn as the skill's picture rules say; a drawing those rules write as a file goes beside the fragment, under the name they give. Then stop, and say in one line which fork the fragment holds.

The design: what happens to a camera recording when its upload to storage fails.

Facts:
- Today a recording passes these states: recording, finalizing, uploading, stored. A failed upload leaves it in uploading for ever, and the operator sees a spinner.
- The recorder uploads each finished file to the archive storage once and keeps no retry.
- The archive service reads only recordings in stored.

The one fork left: how a failed upload gets out of uploading.
- Option retry: a new state, retrying, with up to five retries; after the fifth the recording goes to failed.
- Option failed: a failed upload goes straight to a new state, failed, and the operator restarts the upload by hand.
