---
name: brainstorm
description: >
  Use when the owner asks to design something: a choice between ways to build a feature, a
  service, a contract, a boundary or a mechanism in the VMS tree, before a plan exists. Not
  for operations or debugging: raising a stand, reading a log, chasing an error, or a
  mechanical edit one session makes in place. Triggers: "brainstorm", "let's design", "think
  this through", "how would we build", "which way", "explore the options", "брейншторм",
  "давай подумаем", "обсудим дизайн", "как это строить", "какой вариант", "прикинем
  варианты". With a peer when the owner asks for one, a second agent in the split pane that
  builds its own forks and argues each one out with the lead: "brainstorm with a peer",
  "brainstorm with two agents", "брейншторм вдвоём", "брейншторм с пиром", "брейншторм с двумя
  агентами".
user-invocable: true
---

# Brainstorm a VMS design

A design session ends in a summary the owner has confirmed: the decisions in the owner's
words, what stayed open, and what the agent proposed on its own. That summary is the input of
`/make-plan`. Everything before it is questions, and every question comes after the facts.
The skill runs when the owner asks for it, and a choice the tree or a rule the owner has
already stated settles is not a question.

A session may have a peer: a second agent in the split pane of the same agterm session, which
builds its own forks and options without seeing this session's and argues each fork out
before the owner gets it. A session with a peer is a trial, and it ends on a line saying what
the peer changed. Who the peer is the owner says in the request, in words or as `peer`,
`peer claude`, `peer codex` or `no peer`, or answers when the run asks. With a peer, read
[with-peer.md](with-peer.md) right after that answer: it adds to the run below and changes
none of it. A session without a peer is plain and does not read that file.

## The run

0. **The peer.** One question, asked first and alone, unless the request already answers it
   or the session is not in agterm, where no peer can run. Three answers, each with what it
   costs: no peer, the session as this file describes it, which a bare «ок» means; Claude
   Code, a second session of the same account that builds its own version of every fork, its
   turns paid like this session's; Codex, the same work by another model, which catches what
   two Claudes agree on by habit and which the skills of this repository do not bind.
   It is a question about the session and not about the design, so it does not wait for the
   facts.
1. **Frame.** What the owner wants to have at the end: a mechanism, a contract, a boundary, a
   removal. One question, skipped when the request already says it.
2. **Context and facts**, below. Nothing is asked before they are read.
3. **Forks**, one at a time, in the two-stage form below. Before the first one, the owner
   gets the list: how many forks the facts left, each named in a few plain words. Every fork
   then opens with its place, «развилка 2 из 5». A fork that an answer settles or adds
   changes the count, and the next message says so: «после ответа осталось 3, добавилась
   одна: …».
4. **Assembly.** Only when the answers add up to a design: sections of up to ~300 words, one
   per message, each ending in "does this hold?". A session that settled one fork has nothing
   to assemble and goes to the end.
5. **The end**, below.

## Facts before questions

Read first, in this order: memory, the `MEMORY.md` index the session loads and the notes it
points at, for the owner's decisions and the rules the owner has stated; the
[glossary](../../../docs/architecture/glossary.md) for the names; the tree, the areas the
request names with their requirements, ADRs and chapters.

- A claim about the code is made after a grep or a read. "The gateway already retries" without
  the read behind it is a guess, and a guess is not put to the owner. The path and the line
  stay with the agent: the owner reads a design, not the tree, and a file is named only when
  the owner asks where something lives.
- A claim about a system the repository does not own (an engine, a library, a vendor's camera
  or protocol, a browser API, Hik) is checked the same way: against a technical note under
  `docs/architecture/technical-notes/`, the vendor's document, or the source of the version the
  tree pins, in the Go module cache or the console's installed packages. A claim about Vartova
  is checked against `frontend/vartova/`. Where a PRD describes the feature (the root `CLAUDE.md` names
  where the PRDs live and how they are read), the option is read against its text before it
  goes into a question, and an option that departs from it
  says so in the fork. What was not checked carries the words «не проверено» beside it.
- Before an option goes into a question, `docs/architecture/adr/` and
  `docs/architecture/requirements/` are grepped by the words of its mechanism, not by the area:
  `version`, `etag`, `if-match`, `idempot`, `lock`, `retry`, `outcome`, the mechanism's own
  name. An accepted record that already decided the opposite sits under another domain's
  title. An ADR does not bind the choice: the option that goes against one says so and that
  the record is rewritten after it, with no question of its own. An accepted requirement does
  bind, and an option that breaks one says so.
- Research is proposed, not launched: how many `Explore` agents, or `thinking-tools:ask-codex`,
  or `thinking-tools:dialectic`, and what each is to find, one line each. It runs after the
  owner's go.
- Every option is checked against the rules the owner has stated before it goes into a
  question. An option a stated rule excludes is not offered; an option that bends one says so.

## A fork

A fork that changes the architecture, a new component, a table, a call between services, a
change of a contract or of a boundary, is asked in two stages, and the first is never skipped.

**First, in plain words.** What the operator sees on the screen, and what happens behind it
when they act: who asks whom, what is kept where, told by role — the gateway, the camera
registry, the status card, the problems table — never by package, type or RPC name. What the
tree does today, and what Hik or Vartova does where one of them is the reference, told the
same way. A term the owner has not used is explained by what it does, in the sentence that
needs it. A name the agent coined earlier in the session counts as such a term: «близнецы» or
«семь пар» mean nothing to the owner until a sentence says what they are. A picture from outside the system is welcome when it carries the point and dropped
when it needs a footnote. Someone who has never opened the repository understands this stage,
and the owner reads it before any option.

**Then the choice**, in the same words:

- two or three options, the simplest first: a config value, a deletion, a tool already in the
  loop, before a new mechanism — each told as what would happen at run time, not as what would
  be added to the code;
- one short scenario for each option, with concrete names: what the operator does, who asks
  whom by role, what the operator sees, e.g. «оператор открыл архив Park-Camera-02 → гейтвей
  спросил рекордер → …». The scenario shows where the options part, and it shows why the
  recommended one wins; a scenario that only retells the option is cut;
- where the industry has a settled way, Hik's, another VMS's or the engine's own, the option
  says whether it follows that way and names the product or the document that does it, and an
  option that departs from it says why. A "standard" with no name beside it carries
  «не проверено». Where there is no settled way, the line is left out;
- the price of each option: what it adds to the system, a component, a daemon, a table, a
  copy of data, a lock, a cache, a call between services, new behaviour at run time. A heavy
  component for a rare case is named as that. The size of the code change stands beside the
  price as a note, never as the price;
- a recommendation with its reason in one line.

A small question, a name, a default, a flag, is one line without the form.

## The fork page

Inside agterm (`AGTERM_SESSION_ID` is set) every fork with options goes to the owner as a page
in the overlay, not as a comparison in the chat, and the owner picks and comments on the page. Only a small question, a name,
a default, a flag, stays one line in the chat. A fork asked again goes as a page again: after
a comment, after «объясни», after a request for an example, after an option was corrected. A
request to go faster cuts the forks and the checks, never the page. The two stages stay: the
today block is the first, the option cards are the second. The markup, the pictures the shell draws
and the answer are in [page.md](page.md). Outside agterm the fork is a message, as below.

The owner is a backend developer who reads code fluently and may not know this subsystem. A
picture is there so that the difference between the options is seen before it is read. It is
drawn when the thing has a shape: who asks whom, where data lives, what follows what, which
states an object passes. A fork with no shape gets cards with text and no picture.

- **One picture answers the question of the fork**, and the question picks its kind: who asks
  whom is a flow between roles; where data lives is stores with their owners; what happens to
  an object is its states; what the operator sees is a sketch of the screen.
- **Today is drawn once, and every option is the same picture.** The same roles stand in the
  same places, and colour marks only what the option adds and what it removes. A picture of an
  option shows the roles the difference touches, not the subsystem.
- **The scenario is on the picture.** Its steps are numbered on the arrows and listed under
  it, with the concrete names the scenario uses.
- **The price is seen.** Every moving part an option adds is drawn and marked as new: the
  count of new marks is the price at a glance, and the price line says what the marks cannot.
- **The words are the message's words.** Roles and plain words, no paths, type or RPC names;
  «не проверено» stands on the element it belongs to.
- **Text says what the picture does not**: the price at run time, the reason of the
  recommendation. Text that retells the picture is cut.
- **Options stand side by side while their pictures read at that width.** A wide picture, a
  long chain or a screen, takes the `rows` layout. The page falls to rows on its own when the
  panel is too narrow for every option in one row.
- **Two or three cards.** A fourth is allowed. Past that the fork is two forks, or the weaker
  options go to the folded list of rejected ones, each with its reason in one line.

Before the page is shown, cover the titles in your mind: if the pictures alone do not tell the
options apart, the picture is decoration, and it is redrawn or dropped.

The chat stays the record. Before the page, one line: which fork it is and that the page is
open. After the answer, the owner's pick and every comment word for word, then the
restatement of "After the answer". A comment on the today block is a claim that a fact is
wrong: check it before anything else. `own` is the owner's own option, `explain` is "не знаю",
and a rejected option the owner marks comes back as an option of the same fork.

## The shape of a message

The gist is text above the question, not inside it. A preview, the shape of a call, a table,
a message on the bus, is up to ~10 lines or is left out. No paths, line numbers, type or RPC
names in the text: roles and plain words carry it, and an owner who wants the place asks for
it. One fork per message, even when several are ready: the next one waits for the answer.
A numbered batch of forks gets answered "1 — a, 2 — не понял, 3 — не понял", and the forks
left unclear are lost in it. A message stays under ~600 words; what does not fit waits for
the next one.

## After the answer

- The owner took the recommended option without a word: restate it, «значит, X, потому что
  Y», so the reason is on record before the next fork.
- "Не знаю" or "объясни": explain, on the same facts, plainer than the first time — the
  screen, then who asks whom, then the price as a consequence — and ask again. Nothing is
  chosen for the owner.
- What the agent adds on its own, a monitor, a lock, a cache, a name, a second table, is its
  own fork, asked before it appears in a design or in the summary.

## Ask first, then do

No agent is launched, no file is written, no summary is composed and no plan is started
without a question the owner answered or a request the owner made. The go for research, the
"no" to "ещё вопросы", the exit taken from the menu: each is such an answer.

## The end

When everything seems settled, ask «есть ли ещё вопросы, что осталось нерешённым?». Only
after "no" comes the summary, short: the decisions in the owner's words, the unresolved, and
the agent's own proposals apart from both. The owner confirms it, or edits it and confirms.
Then one question with three items:

1. stop;
2. `/make-plan` with this summary as its input;
3. save the summary to a file, at the path the owner names with the choice.

There is no fourth item, and "start now" is not one.

## Common mistakes

| Mistake | Fix |
|---|---|
| Asked before the facts were read | Memory, glossary, tree, then the question |
| A claim about code from memory | Grep or read first; the path stays with the agent |
| An engine, a library, Hik or Vartova from memory | The note, the vendor document, the pinned source or the console; otherwise «не проверено» |
| Checked the ADRs of the area only | Grep ADRs and requirements by the words of the mechanism |
| The fork opens with the mechanism | Plain words first: the screen, then who asks whom, by role |
| Options told in the abstract, the owner asks «на примере» | A scenario with concrete names in each option of an architectural fork |
| A name coined in the session used as if the owner knows it | Explain it in the sentence where it appears, or drop it |
| Paths, line numbers or type names in the message | Roles and plain words; a file is named when the owner asks where |
| «Так делает индустрия» with no product or document named | Name who does it, or «не проверено» |
| The departure from the PRD surfaced at the assembly | Read the PRD before the option is offered; the fork says it |
| The new mechanism first | The simplest first; a deletion or a config value before a component |
| The price given as lines of code | What it adds to the system; the code size is a note beside it |
| A picture per option, each laid out its own way | Today once; every option the same picture with the difference coloured |
| The whole subsystem in an option's picture | The roles the difference touches |
| A picture for a fork with no shape | Cards with text |
| A fork, or the same fork asked again, given as text inside agterm | A page; the chat carries only a name, a default, a flag |
| The answer of the page left in the tool output | The pick and every comment word for word in the chat |
| Chose for the owner on "не знаю" | Explain and ask again |
| Took a silent yes as a decision | «значит, X, потому что Y» |
| A lock, a cache or a name slipped into the design unasked | Its own fork |
| Launched a wave, wrote a file or opened a plan without a question | Ask first |
| The summary before "ещё вопросы?" | The question, the "no", then the summary |
