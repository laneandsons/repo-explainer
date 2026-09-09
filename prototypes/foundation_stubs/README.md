# PROTOTYPE — the stub tree `foundation` would freeze

Throwaway. Answers [What interfaces does the foundation freeze?](https://github.com/laneandsons/repo-explainer/issues/5).

```
uv run python prototypes/foundation_stubs/walkthrough.py
```

The walkthrough carries one worked example across all five seams and prints the value
at each boundary. Nothing is implemented; the shapes are the point.

## The pipeline, as five seams

| Seam | Signature | Crosses |
| --- | --- | --- |
| 0 | cli or evals builds a `Source` | kind (GITHUB / LOCAL), location |
| 1 | `fetch(source, ctx) -> Repo` | files, url, commit sha |
| 2 | `analyze(repo, ctx) -> RepoStructure` | tree, entry points, manifests, ecosystem |
| 3 | `draft(structure, provider, ctx) -> Draft` | **ungrounded** claims + snippet line ranges |
| 4 | `ground(draft, repo, ctx) -> Explanation` | grounded claims + real snippet text + drop counts |
| 5 | `render(explanation, repo, ctx) -> Page` | html **and** PageFacts |

`ctx: RunContext` is the only argument every stage shares. It carries `run_id`, the event
sink, the logger, and the `--record-paths` flag — it is how any module reaches foundation.

## One file per build ticket

`foundation` owns `domain.py`, `events.py`, `log.py`, `run.py`, `grounding.py`, and lands
every other file as a stub. Then `fetch.py`, `analyze.py`, `llm.py`, `render.py`,
`evals.py`, `cli.py` go to one agent each. No two agents touch the same file.

## Three calls, now settled

### 1. `grounding.py` is foundation-owned

Issue #3 left "which module owns the grounding check" open. It is foundation's: it is
the mechanism the entire event design exists to measure, it makes no model call, and it
is the single place that decides what *grounded* means. Rejected: putting it in `llm`
(one agent would hold both a model call and the tool's central rule), and putting it in
`render` (render would delete content as well as lay it out).

### 2. A `SourceKind` enum, so `fetch` has one door

```python
class SourceKind(StrEnum):
    GITHUB = "github"   # ask GitHub for the files, and for the sha
    LOCAL  = "local"    # read a folder; the caller supplies url and commit
```

`fetch(source, ctx) -> Repo` branches on the kind. Rejected: two functions
(`fetch_github` / `fetch_local`), which hides the fiction at the call site, and having
the eval harness build a `Repo` itself, which means `fetch` is never exercised offline.

A LOCAL source carries a **pretend** url and sha, committed in the eval case, so a
golden-set page is shaped exactly like a real one and no stage after `fetch` ever asks
which kind it was. `__post_init__` refuses a LOCAL source missing either one.

This is **not** a user-facing flag. Whether the command line should accept a folder is
still fog on the map; the enum is what would make that cheap if it graduates.

### 3. The model returns snippet **line ranges**, never snippet text

`SnippetRequest(path, start_line, end_line)`, and `ground` slices the real file. A
snippet cannot be wrong by construction. ADR 0001 currently describes the weaker
version — "does this text appear character-for-character in that file" — and needs
amending. Accepted cost: a model is worse at line numbers than at copying text, so more
snippets get dropped for a bad range.
