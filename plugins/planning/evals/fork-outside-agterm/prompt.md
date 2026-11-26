---
name: fork-outside-agterm
description: Outside agterm brainstorm gives a fork as a chat message, with no page fragment and no diagram-design drawing. Run with --allow-tools Write --ablation none.
tags: [brainstorm, pictures]
runs: 2
max_turns: 30
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write]
---

Run `/planning:brainstorm` on the design below.

Context for this check:
- This session is not inside agterm.
- No peer.
- The frame and the facts are settled and listed below. Do not read the tree, do not propose research, ask no question.
- Go straight to the first fork and give it to me the way the skill gives a fork in this session. If the skill writes a fragment, it goes to `./fork-1.html`. Then stop.

The design: what happens to a camera recording when its upload to storage fails.

Facts:
- Today a recording passes these states: recording, finalizing, uploading, stored. A failed upload leaves it in uploading for ever, and the operator sees a spinner.
- The recorder uploads each finished file to the archive storage once and keeps no retry.

The one fork left: how a failed upload gets out of uploading.
- Option retry: a new state, retrying, with up to five retries; after the fifth the recording goes to failed.
- Option failed: a failed upload goes straight to a new state, failed, and the operator restarts the upload by hand.
