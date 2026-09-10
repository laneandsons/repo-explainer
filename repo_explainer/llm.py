"""Build ticket B4 (#15) fills this in."""

from __future__ import annotations

from typing import Protocol

from repo_explainer.domain import Draft, RepoStructure
from repo_explainer.run import RunContext


class Provider(Protocol):
    """A mock provider is what lets `llm`'s own test pass with no API key."""

    def complete(self, prompt: str) -> tuple[str, int, int]:
        """Returns (raw model text, input_tokens, output_tokens)."""
        ...


def draft(structure: RepoStructure, *, provider: Provider, ctx: RunContext) -> Draft:
    """One model call. Returns an UNGROUNDED draft. Emits llm.completed.

    Every claim comes back with the file it came from, or with None. That is a
    shape requirement on the model's structured output, not just telemetry.
    Snippets come back as line ranges, never as text (OPEN CALL 3 — see README).
    """
    raise NotImplementedError("build ticket: llm")
