---
name: fork-screen-hand-drawn
description: A fork about what the user sees on a screen is drawn by hand as an inline svg, since diagram-design has no screen type. Run with --allow-tools Write --ablation none.
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
- Go straight to the first fork. Write its fragment to `./fork-1.html` in the markup of the skill's `page.md`, with its pictures drawn as the skill's picture rules say. Then stop, and say in one line which fork the fragment holds.

The design: how the operator sees that a camera has a problem.

Facts:
- Today the camera card shows the camera's name, its live picture and its archive button. A problem shows nowhere: the operator learns of it when the live picture is black.
- The camera registry already records each camera's last problem and when it happened.

The one fork left: where on the screen the operator sees the problem.
- Option badge: a red badge in the corner of the camera card, with the problem's text on hover.
- Option tab: a separate problems tab next to the cameras list, one row per camera with a problem.
