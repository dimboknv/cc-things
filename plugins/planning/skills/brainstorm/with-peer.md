# A brainstorm with a peer

What a session of the skill adds when the owner asked for a peer: when the peer is asked,
what it is asked, and what of its answer reaches the owner. Everything in
[`SKILL.md`](SKILL.md) holds. Load `mailbox-chat` before the first exchange. Needs agterm.

The session that received the owner's request is the **lead**. The **peer** is a second agent,
Claude Code or Codex, in the split pane of the same agterm session. Only the lead asks the owner anything. The
owner reads both panes.

## What the peer is for

A brainstorm fails in four ways the lead cannot see from inside:

- an option nobody showed the owner, most often "do not build it at all" and "do it the way the
  neighbouring thing in this system already does";
- a guess told as a fact, and a number nobody recomputed;
- a recommendation that bends a rule of this repository, or a frame that stands on a premise
  nobody questioned;
- the lead's own jargon: a word the owner never used, an option told as a change to the code.

The peer exists to catch these four. It does not second the lead.

Two agents that read the same files in the same order reach the same answer, and their
agreement proves nothing. So they read in a different order and do not see each other's work
until both have written theirs down:

- the lead reads **from the tree outward**, as `brainstorm` says: memory, glossary, the code
  and its requirements, ADRs and chapters, then the outside systems the options touch;
- the peer reads **from the outside inward**: the PRD, the reference console, how the
  industry, the engine's own documentation, Hik or another VMS does the thing, and what the
  plainest shape would be if nothing existed yet. The tree comes last.

## Start

Picking a peer is the owner's go for the peer and for every exchange with it. Any other
agent or research still waits for a go of its own, as in `brainstorm`.

The owner picked the peer in the request or in the first question of the run: Claude Code or
Codex. After the frame is known, start it:

```bash
.claude/skills/brainstorm/scripts/peer.sh .claude/skills/brainstorm/peer.md claude
.claude/skills/brainstorm/scripts/peer.sh .claude/skills/brainstorm/peer.md codex
```

Either agent runs on the model its own configuration picks. A model id after `claude` is
passed only when the owner names one.

The script opens the split, starts the agent there, hands it [peer.md](peer.md), and prints
the mailbox status once the peer listens. A Claude peer runs under the same account.
When it refuses, give the owner its message as it is and offer the session without a peer. Do not
start a peer by hand around a refusal.

Then tell the owner in one line what the right pane is: a second agent that builds its own
version of every fork and argues with the lead, that the owner may read it and need not
answer anything there.

## The exchanges

The first line of a message is its tag, the body is in the language the owner writes in, and
the last line says what reply is expected and whether the lead waits for it, or
`no reply needed`. A reply that only agrees or thanks is never sent.

| Tag | The lead sends | The peer returns |
|---|---|---|
| `frame` | The owner's words, word for word: the request, the answer to the frame question, and what the owner said earlier in the session that bears on it. The path of the lead's transcript. Nothing the lead read or concluded | Its own list of forks with the facts behind each, what the tree or a stated rule already settles, and the zero fork: the premise the frame stands on |
| `options` | The merged, numbered list of forks, and which of them to build now: every fork whose question does not depend on an answer still to come. No draft and no hint | One message per fork, as each is ready: its options, scenarios, prices and recommendation |
| `clash N/M` | The lead's full draft of the fork as the owner would get it, for a fork page the path of its fragment file, and every difference from the peer's version | For each difference a concession or something new; the words and numbers of the draft checked; the attack on the recommendation |
| `answer` | Every reply of the owner that is more than a pick, word for word, and the pick itself with the lead's restatement. The answer of a fork page goes as the JSON the page returned | Depends on what the reply is, below |
| `defaults` | The batch of small questions the lead means to settle as defaults, before the owner sees it | Which of them is a fork |
| `assembly` | All sections of the design in one message, before the owner sees the first | Decisions that contradict each other, and parts nobody decided |
| `summary` | The summary, before the owner sees it | Every place where it differs from the owner's words |
| `end` | That the session is over | Nothing |

### Blind first

The lead writes its own version before it reads the peer's. A message from the peer arrives
only between turns, so the order is: send the request, do the same work, save the result to a
file in the scratchpad, end the turn. Blind work is done for the list of forks and for the
options of every fork that changes the architecture.

The peer works ahead. While the owner reads and answers fork 1, the peer's options for the
other independent forks arrive, and the lead has its own drafts of them in the scratchpad
already. The mailbox hands over everything that gathered during the lead's turn at once, so
several forks can arrive in one turn, and each is still a fork of its own with its own clash.
The owner waits for the peer once, before the first fork. That turn ends with one
line, what the peer was asked, and with no draft of the fork, no page and no part of either: the facts
about today are where a wrong claim most often sits, and they go to the owner only after the
peer has read them.

A fork the peer has that the lead does not goes into the owner's list only when it changes
the architecture by the definition in `brainstorm`. The rest join the defaults.

### The clash

The lead sets the two versions side by side and sorts every difference:

- **an option only one of them has.** It stays unless a rule the owner has stated excludes
  it. The lead does not drop the peer's option because its own looks better;
- **a fact they state differently.** Each reruns its check and the message carries the result.
  The one who was wrong says so in one line;
- **a different recommendation.** Each gives the scenario in which its option wins and the
  price the other option pays in it.

The `clash` message is sent for every architectural fork, also when the two versions match:
the lead is the side being checked and does not decide that there is nothing to check. The
peer reads the draft itself for what only a draft shows, the lead's jargon and the lead's
numbers. On a fork page it also reads the pictures: a role that changes place between today
and an option, an added part with no mark, a picture that does not tell the options apart.
The page opens for the owner only after the clash.

A round has to bring a new fact, scenario or price. Two rounds per difference and four
messages per fork at most. What the two still disagree on goes to the owner.

A fact from the peer reaches the owner only after the lead has checked it with its own read or
grep. Nothing the peer says is the owner's approval of anything. A label the two agents coined
in the chat, a number for a variant, a nickname for a mechanism, stays in the chat: the owner
gets the thing in plain words.

### The owner's reply

Every reply goes to the peer word for word. Whether the lead waits depends on what it carries:

- **a pick.** It rides with the next message. No reply.
- **a question about what was said.** The lead answers the owner at once and sends the peer
  the question with its answer. The peer writes only when the answer holds a wrong fact.
- **an option of the owner's own, a source the owner names, or an order to argue something
  out.** The lead waits. The peer returns the facts and the price of the owner's option, or
  the settled forks the new source touches, or a clash on the topic. The owner's option has
  had no outside check from anyone, and this is where the second reader is worth the wait.

## What the owner gets

The fork in the two-stage form of `brainstorm`, built from both versions, with one
recommendation. A dispute that is still open never replaces the recommendation with two
positions.

After the recommendation, one line: what the peer attacked and what stopped the attack.
«Пир согласен» alone is never written. A block «где мы с пиром разошлись» of up to ~100 words
appears only when a dispute is still open or the recommendation changed in the clash. It
carries the peer's position in the peer's words, who changed their mind and after which fact,
and for an open dispute the one check that would settle it and what that check costs. The
check is proposed, not run. The block follows the rules of the rest of the message: roles and
plain words, no paths, no type names.

## Waiting and order

- The lead never polls and never waits inside a turn. The reply arrives on its own.
- One fork at a time is in front of the owner, as in `brainstorm`. The peer is not held to
  that: it builds ahead.
- An answer of the owner can settle or change a fork the peer has already built. The lead
  says so in the `answer` message, and the stale options are dropped without a clash.
- When the peer's mail touches a fork the owner has already settled, the lead tells the owner
  and asks whether to reopen it. It does not reopen it on its own.

## When the peer is gone

A peer that crashed or lost its context to compaction is started again with `peer.sh`. The
lead sends `frame` again with the path of its transcript, and the new peer takes the owner's
replies from that file: they are the owner's words as typed, and no second record of them is
kept.

## The end

The `summary` exchange comes after the owner's "no" to «есть ли ещё вопросы», and before the
owner sees the summary. After the owner picks an exit, the lead sends `end` and leaves the
split open: the owner closes it, not the lead.

This is a trial. Below the exit menu the lead adds one line with four numbers: forks and
options the peer added, facts and numbers the peer corrected, recommendations that changed
after a clash, words the peer made the lead explain. They tell the owner whether the peer paid
for its cost.

## Common mistakes

| Mistake | Fix |
|---|---|
| Sent the peer the lead's reading of the tree with `frame` | The owner's words and the transcript path only |
| Sent the lead's draft with the `options` request | The numbered list and which forks to build |
| Read the peer's reply before writing the lead's own version | Write it to the scratchpad in the turn that sends the request |
| Showed the owner a draft, or its "today" part, while the peer was still working | One line on what the peer was asked |
| Skipped the clash because the two versions matched | The draft goes to the peer for every architectural fork |
| Dropped the peer's option because the lead's own looked better | It stays unless a stated rule excludes it |
| Passed the peer's fact to the owner unchecked | The lead's own read or grep first |
| A label from the chat in the message to the owner | The thing in plain words |
| «Пир согласен» in the message to the owner | The attack that was tried and what stopped it |
| An open dispute given to the owner as two positions | One recommendation, the dispute, and the check that would settle it |
| Made the owner wait for the peer on a question about what was said | Answer at once; the peer gets the question and the answer |
| The owner's own option taken or refused without the peer | `answer`, and wait |
| A fifth message on one fork | Two rounds per difference, four messages per fork |
| Took the peer's agreement as a go to write a file or start a plan | Only the owner's answer is a go |
| Reopened a settled fork because the peer's late mail disagreed | Tell the owner and ask |
