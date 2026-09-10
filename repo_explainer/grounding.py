"""The grounding check: delete everything that cannot be traced to a real file.

Foundation owns this, not `llm` and not `render`: it is the mechanism the whole
events design exists to measure, it is pure set membership and line slicing with
no model call, and it is the one place that decides what "grounded" means for the
whole tool.
"""

from __future__ import annotations

from repo_explainer.domain import (
    MAX_SNIPPET_LINES,
    Claim,
    Draft,
    DropCounts,
    Explanation,
    Repo,
    Section,
    Snippet,
    SnippetRequest,
    SourceFile,
)
from repo_explainer.events import grounding_completed
from repo_explainer.run import RunContext


def ground(draft: Draft, repo: Repo, *, ctx: RunContext) -> Explanation:
    """Delete everything that cannot be traced to a downloaded file, and count it.

    Three checks, two mechanical and one self-reported (ADR 0001):
      path     — is it in repo.by_path()?
      snippet  — does its path exist, is the range inside the file, is it <= 10 lines?
      claim    — did the model cite a file at all, and did that path survive?

    Then it slices the real file for every surviving snippet, so no snippet text
    ever originates with the model. Emits grounding.completed — the one event the
    other seven are scaffolding around.
    """
    files = repo.by_path()

    # De-duplicated first: a path the model happened to mention five times is one
    # path proposed, not five. Counting the mentions would make the drop numbers
    # move with how chatty a run was rather than with how much it invented, and a
    # comparable trend line is the whole point of the counts (ADR 0001).
    paths_named = _unique(draft.paths_named)
    paths_kept = [path for path in paths_named if path in files]
    paths_dropped = tuple(path for path in paths_named if path not in files)

    sections: list[Section] = []
    snippets_proposed = 0
    snippets_dropped = 0
    claims_proposed = 0
    claims_dropped = 0

    for draft_section in draft.sections:
        kept_claims = tuple(
            claim for claim in draft_section.claims if _claim_is_grounded(claim, files)
        )
        claims_proposed += len(draft_section.claims)
        claims_dropped += len(draft_section.claims) - len(kept_claims)

        kept_snippets: list[Snippet] = []
        for request in draft_section.snippets:
            snippets_proposed += 1
            snippet = _slice(request, files)
            if snippet is None:
                snippets_dropped += 1
                ctx.log.debug("dropped a snippet", path=request.path,
                              start_line=request.start_line, end_line=request.end_line)
            else:
                kept_snippets.append(snippet)

        # A claim or a snippet can cite a real file the model left out of
        # `paths_named`. It is still grounded — it traces to a downloaded file —
        # so the path joins `paths_kept`, which is what `render` links against.
        paths_kept.extend(claim.source_path for claim in kept_claims)
        paths_kept.extend(snippet.path for snippet in kept_snippets)

        sections.append(
            Section(id=draft_section.id, claims=kept_claims, snippets=tuple(kept_snippets))
        )

    named_drops = paths_dropped if ctx.record_paths else ()
    drops = DropCounts(
        paths_proposed=len(paths_named),
        paths_dropped=len(paths_dropped),
        snippets_proposed=snippets_proposed,
        snippets_dropped=snippets_dropped,
        claims_proposed=claims_proposed,
        claims_dropped=claims_dropped,
        dropped_paths=named_drops,
    )

    grounding_completed(
        ctx.events,
        paths_proposed=drops.paths_proposed,
        paths_dropped=drops.paths_dropped,
        snippets_proposed=drops.snippets_proposed,
        snippets_dropped=drops.snippets_dropped,
        claims_proposed=drops.claims_proposed,
        claims_dropped=drops.claims_dropped,
        dropped_paths=named_drops,
    )

    return Explanation(
        sections=tuple(sections),
        paths_kept=frozenset(paths_kept),
        drops=drops,
    )


def _unique(paths: tuple[str, ...]) -> tuple[str, ...]:
    """The same paths, in the order the model first named them, each one once."""
    return tuple(dict.fromkeys(paths))


def _claim_is_grounded(claim: Claim, files: dict[str, SourceFile]) -> bool:
    """A claim needs a cited file, and that file has to be one that was downloaded.

    That is the same test the path check applies, run against `repo.by_path()`
    rather than against the surviving names — a claim citing a real file the model
    forgot to list in `paths_named` is grounded, and gets its path added back.
    """
    return claim.source_path is not None and claim.source_path in files


def _slice(request: SnippetRequest, files: dict[str, SourceFile]) -> Snippet | None:
    """The real lines out of the real file, or None if the request does not hold up.

    The text is sliced here and never read off the model's output, which is what
    makes a snippet unable to be wrong.
    """
    file = files.get(request.path)
    if file is None:
        return None

    start, end = request.start_line, request.end_line
    if start < 1 or end < start or end > len(file.lines):
        return None
    if end - start + 1 > MAX_SNIPPET_LINES:
        return None

    return Snippet(
        path=request.path,
        start_line=start,
        end_line=end,
        text="\n".join(file.lines[start - 1 : end]),
    )
