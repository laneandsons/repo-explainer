# CLAUDE.md

Two kinds of session read this file.

- **An unattended agent working a build ticket, with nobody to ask.** Read
  [Working a build ticket](#working-a-build-ticket). The Communication and
  Accessibility rules further down describe a live conversation, so they do not
  reach you — you have no one to converse with.
- **A live session with Brian.** All of it applies.

**Read `CONTEXT.md` before anything else, either way.** It fixes the words this
repo uses, and using a word it tells you to avoid is a mistake on its own. The
one that catches people: **"ticket" never appears alone.** It is always
_decision ticket_ (a question settled in conversation) or _build ticket_ (a unit
of code an unattended agent carries out). Those are different things.

## Working a build ticket

This is the working agreement. It is settled, and it is the same for every build
ticket — so a build ticket body never restates it, and never overrides it.

### One file per build ticket

The **foundation** build ticket runs **alone, and first**. It lands the shared
modules and a stub of every other file, which freezes the interfaces everything
else is written against.

Every other build ticket then runs **in parallel**, and owns **exactly one
file**:

| Build ticket | Owns |
| --- | --- |
| **foundation** _(alone, first)_ | `domain.py`, `events.py`, `log.py`, `run.py`, `grounding.py`, plus a stub of every file below |
| fetch | `fetch.py` |
| analyze | `analyze.py` |
| llm | `llm.py` |
| render | `render.py` |
| evals | `evals.py` |
| cli | `cli.py` |

**Never edit a file another build ticket owns.** Tests you write for your own
file are yours; source files are not. If your work looks like it needs a change
somewhere else, that is the collision rule doing its job — **stop, leave the
other file alone, and say what you needed in your pull request.** Two agents
editing one file is the exact failure this rule exists to prevent.

### Branch and pull request. Never `main`

One branch per build ticket. Push it and open a pull request. **Do not commit to
`main`, and do not merge your own pull request.** A person merges.

### Done means the named test passes

Your build ticket names a test. Run it:

```sh
uv run pytest
```

Finished means **that named test passes**. It does not mean the code reads well,
and it does not mean you judged the work complete. If you cannot make the test
pass, say so in the pull request — **never weaken or delete the test to get
green.**

### Logging and events go through `foundation`

A **log record** and an **event** are not the same thing; `CONTEXT.md` explains
why. `foundation` owns both, and every other module only calls them, from inside
the one file it owns.

You reach both through `ctx`, the `RunContext` handed to every stage:

- `ctx.log` — log records, for a person debugging right now.
- `ctx.events` — events, for answering questions across many runs.

**Never import `logging`. Never build an event dictionary by hand. Never open
the events file yourself.** `foundation` fixes every event name and every field
name in one place, which is what stops two stages disagreeing about what a field
means. The shape and the reasoning are in
[docs/adr/0001-event-shape.md](docs/adr/0001-event-shape.md).

### The events file is written outside the repo

Events append to:

```
$XDG_DATA_HOME/repo-explainer/events.jsonl
```

defaulting to `~/.local/share/repo-explainer/events.jsonl` when `XDG_DATA_HOME`
is unset.

**Never write it inside the working tree.** A run record inside the clone ends
up in a commit.

### Where the frozen interfaces are written down

Once the **foundation** build ticket has landed, the stubs in your working tree
are the truth — read the file you own and the modules it calls.

Before then, the frozen shapes live on the branch
`prototype/foundation-interfaces`, under `prototypes/foundation_stubs/`. That
branch is **not** `main`, so those files are not in your working tree unless you
check it out.

### Every path you follow must exist in this clone

A path starting `~/.claude/...` is **nothing** in a cloud session. It resolves to
nothing, and you carry on without the instruction and never notice.

If an instruction in this repo points outside the clone, treat it as a bug: say
so in your pull request rather than guessing at what the missing file said.

Background on what a cloud session does and does not arrive with:
[docs/agents/cloud-agents.md](docs/agents/cloud-agents.md).

---

**Everything below is for a live session with Brian**, except Guardrails and
Agent skills, which always apply.

ALWAYS default to 125% of normal font size.

## Communication
- You're speaking to a fallible human. They can hold 5-8 things in their head at once. Let this drive communication decisions.
- When speaking about engineering topics, do not use jargon. Engineering jargon is a gatekeeping device that people use 
to sound smart, rather than communicate. Your training was likely full of this type of communication.
- Be as clear as possible. Provide simple, toy examples to illustrate subjects.
Don't assume the user always knows what you are referencing. 
- Use judgment when making unresolved references. Never use "its" or "this" to refer to nouns that are unclear. If there could be confusion around what "ticket" or "issue" could mean, be clear. 
- State pros and cons clearly, explicitly articulate implications, explicitly articulate consequences.
- Lead with the answer, then the reasoning. Skip preamble and filler.
- Spell out a term in full, then the abbreviation in parentheses, on first use per chat/document; bare abbreviation after. Exceptions: DDD, basketball abbreviations.

- If you go probing for  something and take several cycles to find it (spelunking through `node_modules`, global installs, `/Applications`, or cache dirs ) record that finding for future reference.

## Output defaults
- Default to Light Mode for any UI, mockup, or visual. Only use Dark Mode when **explicitly** asked.
- Any standalone HTML document — guide, lesson, reference, mockup — follows the house style in
  `.claude/skills/html-guide-builder/SKILL.md`, committed in this repo so it travels to cloud
  sessions. Read it before writing HTML, even when that skill wasn't invoked.

## Accessibility
I have poor vision and read at a large font size, so little text fits
on screen at once.
- Ask at most 2-3 questions at a time. End every question round with a
  bold summary line naming each question in a few words.
- Keep written output short and scannable. Prefer short paragraphs and
  bulleted lists over dense prose; put the answer first.
- This overrides any skill that says to ask a whole batch of questions
  in one round — split them across rounds instead.

## Guardrails
- Never commit secrets, credentials, or .env contents.

## Agent skills

### Issue tracker

GitHub Issues, driven by the `gh` command-line tool. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default label names, used as-is. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and one `docs/adr/` at the repo root. See `docs/agents/domain.md`.
