# Events record counts and tokens, never content or dollars

repo-explainer emits **events** to a single append-only `events.jsonl` so one question can be
answered months later: **how much is the grounding rule throwing away?** A dropped path, snippet,
or claim leaves no trace on the rendered explanation, so a model drifting toward invention produces
a page that quietly gets thinner — the drop counts are the only place that is visible.

Four choices in the event shape look wrong at a glance and are deliberate.

## Counts, not content

`grounding.completed` records **how many** paths, snippets, and claims were dropped, never which
ones. The trend line only needs the number; the names are only wanted while actively debugging a
bad run, and are then available by re-running with `--record-paths`.

Recording them by default would put file paths from private repositories into a plaintext file on
disk, which is the kind of thing that is awkward later. File contents, snippet text, explanation
prose, and anything from the model's output verbatim never appear in an event at all.

The `repo` URL and `commit` **are** recorded, on `run.started`. Without them, "which repositories
does this do badly on" is unanswerable. The cost — private repository names on disk — was accepted
knowingly.

## Tokens, not dollars

`llm.completed` records `model`, `input_tokens`, and `output_tokens`. It does **not** record
`cost_usd`.

Model prices change. A dollar figure written to disk in September is wrong by December, and worse,
it is *silently* wrong — the number still looks authoritative. Token counts are a fact that never
expires; the price list is a lookup applied when something reads the file.

The cost: answering "what did last month cost" needs a price table at read time rather than a
`sum()` over a column.

## Writer failures are swallowed

A failed event write — full disk, bad permissions, missing directory — never fails the run. At most
it produces a log record on the way past. Telemetry must never be able to break the product; a full
disk should not cost you your explanation.

The cost is that gaps in the file are ambiguous. A missing `run.completed` means the run failed
**or** the writer did, and the file itself cannot tell you which.

## Eval runs are tagged, not suppressed

`run.started` carries `trigger: "cli" | "eval"`. Eval runs sweep the golden set and would otherwise
drown the handful of real runs on repositories anyone cared about. Suppressing them was rejected
because eval runs are where drop counts are *most* comparable — the golden-set repositories do not
change between runs, so a moving number is the model moving, not the input.

## Shape

A five-field envelope on every event — `v`, `run_id`, `ts`, `event`, `stage` — with event-specific
fields **flat alongside it**, never nested under a `data` object. A flat line loads straight into
DuckDB or pandas as columns. The cost is that two events could disagree about what a field name
means, so field names are fixed once in `foundation` and reused everywhere.

`v` is the schema version. When the shape changes, bump it; never reinterpret old lines.

Stages emit only `.completed`, never `.started` — a stage's duration rides on its own completion
event. Only the run itself gets a start event. If the process is killed mid-stage rather than
failing cleanly, the file therefore shows the last stage that *finished*, not the one that hung.

## Claim drops are self-reported

Path and snippet drops are checked mechanically: is this path in the downloaded file list, and for a
snippet, does that path exist, is the line range inside the file, and is it ten lines or fewer. The
model hands back a snippet as a **line range, never as text**, and the text is then sliced out of the
real file — so a snippet cannot be wrong by construction, rather than being caught after the fact.
Accepted cost: a model is worse at line numbers than at copying text, so more snippets get dropped
for a bad range.

Claim drops are not mechanical. The model returns each claim with the file it came from, and a claim
citing no file is dropped and counted.

This is **self-reported**, so it is a weaker signal than the other two — the model could cite a file
it did not really use. Watch it as a trend; do not trust it as a fact. A second model call to grade
the first one's prose was rejected: it doubles the cost, and grading output quality is what the
evals are for.

## Where this came from

[What events do we emit, and what do they answer?](https://github.com/laneandsons/repo-explainer/issues/3)

The snippet check was tightened from a text search to a line-range check by
[What interfaces does the foundation freeze?](https://github.com/laneandsons/repo-explainer/issues/5),
which also placed the grounding check itself in `foundation`.
