"""PROTOTYPE — throwaway. Answers issue #5.  Build ticket B6 fills this in."""

from __future__ import annotations

from pathlib import Path

from domain import Case, GateResult, Judge, Page, Scores
from run import RunContext


def load_cases(cases_dir: Path) -> tuple[Case, ...]:
    """Read evals/cases/*/ — a hand-built repo plus a hand-written golden checklist."""
    raise NotImplementedError("build ticket: evals")


def gate(page: Page) -> GateResult:
    """Mechanical pass/fail on PageFacts alone. No judgement, no model, no HTML parsing."""
    raise NotImplementedError("build ticket: evals")


def score(page: Page, case: Case, *, judge: Judge, ctx: RunContext) -> Scores | None:
    """Three numbers, never blended. Returns None for a page that failed the gate."""
    raise NotImplementedError("build ticket: evals")
