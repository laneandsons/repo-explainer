# Evals count what can be counted, on repos built by hand

An **eval** judges whether an explanation is any good. Three other mechanisms already cover ground
that usually gets handed to evals, and keeping them out is what makes this design small: the
grounding rule deletes ungrounded paths and snippets before render, drop counts ride on events
(see [ADR 0001](0001-event-shape.md)), and snapshot tests answer "is this the same?". What is left
for the evals is the only question none of those can answer: **would this page actually get someone
started in this repo?**

Four choices in the design look wrong at a glance and are deliberate.

## The golden checklist is a list of requirements, not a page

Each case pairs a repo with a **golden checklist** — "a good explanation should identify the project
as X from `pyproject.toml`; should start the reader at `src/cli.py`; should say plainly that there
are no tests." It is not a reference explanation to be matched against.

Two explanations can word the same claim differently and both be right, so scoring against a
reference page punishes valid divergence. A checklist turns coverage into a per-item yes/no, which
is a far more reliable question to put to a judge than "rate completeness out of five" — and it is
much cheaper for a person to write, which is what decides whether the golden set actually grows.

The cost is that a checklist only catches what someone thought to list. A page can cover all ten
items and still read badly, which is why clarity stays a separate judged axis.

## Counts where a count exists, a rating only where it does not

Coverage is reported as *8 of 10 checklist items*. Accuracy is reported as *2 false claims*. Only
clarity is a 1–5 rating.

"Three claims are wrong" is a fact that names its own follow-up work. "Accuracy: 4 out of 5" is
mush — it cannot be argued with, reproduced, or acted on. Where the thing being measured is
genuinely countable, a rating throws that away in exchange for looking tidy.

The consequence is that **there is no single blended score**. A count of false claims cannot be
averaged with a rating, so a run produces three numbers per case and the baseline comparison is per
axis. A regression is false claims up, or coverage down, or clarity down by more than a point. The
earlier Gleam version of this tool did have one `corpus_overall` mean, which was only possible
because all four of its dimensions were 1–5 ratings; one number is convenient and hides which axis
moved.

## "The HTML is well-formed" is a gate, not an axis

Five sections present and in order, prose inside the ~800 word budget, at most four snippets of at
most ten lines in sections 3 and 5 only, footer commit stamp present, HTML parses. All of it is
mechanical, and a page that fails is **not scored at all**.

A malformed page is a bug, not a bad explanation. Scoring it would let a rendering fault show up as
a quality regression, sending you to read the prompt when the fault is in `render`.

The cost lands on `render`, which must expose the gate's inputs — the section list, word counts,
snippet count and line spans — as data rather than only as HTML, or the gate has to re-parse the
tool's own output.

## Case repos are built by hand, not cloned

Version one's golden set is two or three small repos committed into `evals/cases/`, not real
repositories pinned to a commit sha.

The map exists to produce build tickets an **unattended cloud agent** can run alone. An agent may
have no API key and no network, so the eval harness's own test has to pass offline — which it can
against committed repos and cannot against clones. Runs are also deterministic and free, so a moving
number is the model moving rather than the input.

The cost is real and known: a repo of a few files cannot tell you how the tool handles a genuinely
messy codebase, which is the case anyone actually cares about. Real repositories pinned to a sha are
the natural second step — `fetch` already returns the sha, so the mechanism exists.

## Who judges

A model judges every run; a person hand-scores one case, once, and that is committed as the
calibration. Hand-scoring every case on every prompt change does not happen, which means evals do
not happen. But an uncalibrated judge is a second opinion nobody checked — the earlier Gleam version
never calibrated, and so had no way to notice a judge drifting. One sitting, no ongoing obligation.

The calibration goes stale if the explanation format changes.

## Where this came from

[What do the evals measure?](https://github.com/laneandsons/repo-explainer/issues/4), which took the
harness shape, the 1–5 anchoring, the tagged judge reply, and the mock provider from the earlier
Gleam version of this tool.
