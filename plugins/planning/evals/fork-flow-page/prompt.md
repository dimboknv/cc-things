---
name: fork-flow-page
description: A fork about who asks whom between roles is drawn by the page's own flow markup, and diagram-design is not called. Run with --allow-tools Write --ablation none.
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

The design: how the gateway finds the recorder that holds a camera's archive.

Facts:
- Today the operator opens the archive of a camera, the gateway asks every recorder in turn, and the first that answers serves the archive.
- The camera registry knows which recorder writes each camera.
- The gateway does not talk to the camera registry today.

The one fork left: who tells the gateway which recorder to ask.
- Option registry: the gateway asks the camera registry, then asks that one recorder.
- Option cache: the gateway keeps its own map of camera to recorder, filled from the answers it got before.
