# repo-explainer

A tool that reads a codebase and produces a written explanation of it. The tool
is also the vehicle for a second goal: learning to write work that unattended
agents can carry out in parallel.

## Language

### Planning

**Map**:
A single effort being charted, holding its destination, the decisions made so
far, and what is still unknown. Exists as one GitHub issue.
_Avoid_: plan, roadmap, epic

**Decision ticket**:
A question whose resolution is a choice, worked through in conversation with a
person. A child of the map.
_Avoid_: ticket, issue, story

**Build ticket**:
A unit of code to be written, specified fully enough that an unattended agent
can carry it out with no one to ask. A child of a decision ticket.
_Avoid_: ticket, issue, task, work item

**Foundation ticket**:
The one build ticket that runs alone, before any others, because it establishes
the structure every later build ticket depends on.
_Avoid_: setup ticket, scaffold ticket

### The product

**Explanation**:
The account of a codebase that repo-explainer produces for a reader. The
thing the tool exists to make. **Ephemeral**: generated on demand and never
checked in, so it is never stale.
_Avoid_: summary, analysis, report, docs

**Grounded**:
Traceable to a file that was actually downloaded from the repo. A path, a
snippet, or a prose claim is either grounded or it is dropped — never hedged.
_Avoid_: verified, sourced, cited, attributed

> A hedge ("this appears to be a CLI tool") can never be wrong, so an eval can
> never score it. Dropping the ungrounded claim instead keeps every remaining
> claim scoreable.

### Observability

**Log record**:
A diagnostic line meant for a person reading output while debugging.
Disposable, and free to change shape at any time.
_Avoid_: log, message, trace

**Event**:
A durable record that a specific thing happened, with a fixed shape, collected
and assembled later to answer questions about behaviour over time.
_Avoid_: log, metric, telemetry

**Run**:
One end-to-end invocation of repo-explainer against a single repository,
producing a single explanation. The unit every event is tagged with.
_Avoid_: execution, job, session, invocation

**Drop**:
A path, snippet, or claim removed from an explanation for not being grounded.
Counting drops is how repo-explainer reports on itself at run time — a dropped
sentence leaves no trace on the page, so the count is the only place it shows.
_Avoid_: rejection, filter, exclusion

> Log records and events are **not** the same thing. They have different
> readers and different lifetimes: a log record is read once by a human, an
> event is aggregated across many runs.

### Evaluation

**Eval**:
A judgement of how good an explanation is, scored against rating axes. Answers
"is this any good?"
_Avoid_: test, benchmark, check

**Rating axis**:
One dimension an explanation is scored on: coverage, accuracy, or clarity.
_Avoid_: criterion, dimension, metric

**Gate**:
A mechanical pass/fail check on an explanation, made without judgement — the
five sections are present, the word budget holds, the HTML parses. A page that
fails the gate is not scored at all. A gate is never a rating axis.
_Avoid_: check, validation, lint

**Golden set**:
The growing collection of cases used as the input to evals.
_Avoid_: fixtures, test data, corpus

**Case**:
One member of the golden set: a small codebase paired with the golden checklist
for it. Lives in one directory under `evals/cases/`.
_Avoid_: fixture, test case, example

**Case repo**:
The codebase inside a case. Built by hand and committed, rather than cloned, so
an eval run needs no network and gives the same answer every time.
_Avoid_: fixture repo, sample, mock repo

**Golden checklist**:
The list of things a good explanation of a case contains — requirements, not a
reference page. Written by a person; it is the statement of what "good" means
for that case, which is why no agent can write one.
_Avoid_: golden output, expected output, reference explanation

> A golden checklist is **not** a page to be matched against. Two explanations
> can word the same claim differently and both be right, so the checklist lists
> what must be *covered*, and coverage is counted item by item.

**Snapshot test**:
A check that output has not changed since last recorded. Answers "is this the
same?", never "is this any good?" — which makes it not an eval.
_Avoid_: eval, regression test

> **"Ticket" never appears on its own.** It is always _decision ticket_ or
> _build ticket_. All three of map, decision ticket, and build ticket are
> GitHub issues, so "issue" never distinguishes between them either.
