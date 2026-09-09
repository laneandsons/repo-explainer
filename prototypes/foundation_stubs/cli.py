"""PROTOTYPE — throwaway. Answers issue #5.  Build ticket B7 fills this in.

The only file that knows the pipeline order. Every other module is unaware of
what runs before or after it.
"""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """repo-explainer <github-url> [--out PATH] [--no-events] [--record-paths] [-v]

    fetch_github -> analyze -> draft -> ground -> render -> write the file.
    Builds the RunContext, emits run.started / run.completed / run.failed, and is
    the only place that catches an exception from a stage.
    """
    raise NotImplementedError("build ticket: cli")
