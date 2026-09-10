"""Build ticket B5 (#16) fills this in."""

from __future__ import annotations

from repo_explainer.domain import Explanation, Page, Repo
from repo_explainer.run import RunContext


def render(explanation: Explanation, repo: Repo, *, ctx: RunContext) -> Page:
    """One fixed five-section template. Emits render.completed.

    Returns HTML **and** PageFacts. The facts are not a convenience: ADR 0002 says
    the gate must read them as data rather than re-parse this function's own HTML.
    `repo` is here for the GitHub links and the footer commit stamp.
    """
    raise NotImplementedError("build ticket: render")
