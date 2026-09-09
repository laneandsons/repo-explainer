"""PROTOTYPE — throwaway. Answers issue #5.

OPEN CALL 1 — see README. This file is drawn as FOUNDATION-OWNED, not as a build
ticket of its own: it is the mechanism the whole events design exists to measure,
it is pure set membership and line slicing with no model call, and it is the one
place that decides what "grounded" means for the whole tool.
"""

from __future__ import annotations

from domain import Draft, Explanation, Repo
from run import RunContext


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
    raise NotImplementedError("foundation builds this")
