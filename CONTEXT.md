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

> Log records and events are **not** the same thing. They have different
> readers and different lifetimes: a log record is read once by a human, an
> event is aggregated across many runs.

### Evaluation

**Eval**:
A judgement of how good an explanation is, scored against rating axes. Answers
"is this any good?"
_Avoid_: test, benchmark, check

**Rating axis**:
One dimension an explanation is scored on, such as accuracy of interpretation,
clarity of interpretation, or quality of the rendered HTML.
_Avoid_: criterion, dimension, metric

**Golden set**:
The growing collection of codebases, paired with explanations judged good, used
as the input to evals.
_Avoid_: fixtures, test data, corpus

**Snapshot test**:
A check that output has not changed since last recorded. Answers "is this the
same?", never "is this any good?" — which makes it not an eval.
_Avoid_: eval, regression test

> **"Ticket" never appears on its own.** It is always _decision ticket_ or
> _build ticket_. All three of map, decision ticket, and build ticket are
> GitHub issues, so "issue" never distinguishes between them either.
