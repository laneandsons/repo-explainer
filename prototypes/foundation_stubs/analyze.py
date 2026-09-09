"""PROTOTYPE — throwaway. Answers issue #5.  Build ticket B3 fills this in."""

from __future__ import annotations

from domain import Repo, RepoStructure
from run import RunContext


def analyze(repo: Repo, *, ctx: RunContext) -> RepoStructure:
    """Read the fetched files and report what is there. Emits analyze.completed.

    No model call. Everything here is mechanical, so it is the same every run.
    How far past Python `ecosystem` detection reaches is still fog on the map.
    """
    raise NotImplementedError("build ticket: analyze")
