"""PROTOTYPE — throwaway. Answers issue #5.  Build ticket B2 fills this in.

`foundation` freezes the one signature below and nothing else in this file.
"""

from __future__ import annotations

from domain import Repo, Source
from run import RunContext


def fetch(source: Source, *, ctx: RunContext) -> Repo:
    """Turn a Source into a Repo. Emits fetch.completed.

    One entry point, branching on `source.kind`:

      GITHUB — download the default branch head, and read the sha off the response.
      LOCAL  — read the folder off disk, and take the url and sha from the Source.

    LOCAL is why the eval harness needs no network and no API key (ADR 0002): a case
    repo is committed under `evals/cases/`, and its case file carries the pretend url
    and sha. Everything downstream of this function is identical either way — no
    stage after `fetch` ever asks which kind it was.

    LOCAL is NOT a user-facing flag. Whether the command line should accept a folder
    is still fog on the map; this enum is what would make that cheap if it graduates.
    """
    raise NotImplementedError("build ticket: fetch")
