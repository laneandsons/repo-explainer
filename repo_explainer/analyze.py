"""Build ticket B3 (#14) fills this in."""

from __future__ import annotations

from repo_explainer.domain import Repo, RepoStructure
from repo_explainer.run import RunContext


def analyze(repo: Repo, *, ctx: RunContext) -> RepoStructure:
    """Read the fetched files and report what is there. Emits analyze.completed.

    No model call. Everything here is mechanical, so it is the same every run.
    How far past Python `ecosystem` detection reaches is still fog on the map.
    """
    raise NotImplementedError("build ticket: analyze")
