"""PROTOTYPE — throwaway. Answers issue #5: what interfaces does `foundation` freeze?

Everything that crosses a module boundary. `foundation` owns this file; no other
build ticket may edit it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from enum import StrEnum
from typing import Literal, Protocol

# --- The five sections, fixed. See issue #2. -------------------------------

SectionId = Literal[
    "what_this_is",
    "how_its_laid_out",
    "where_to_start_reading",
    "how_to_run_it",
    "what_would_surprise_you",
]

SECTION_ORDER: tuple[SectionId, ...] = (
    "what_this_is",
    "how_its_laid_out",
    "where_to_start_reading",
    "how_to_run_it",
    "what_would_surprise_you",
)

SECTION_TITLES: dict[SectionId, str] = {
    "what_this_is": "What this is",
    "how_its_laid_out": "How it's laid out",
    "where_to_start_reading": "Where to start reading",
    "how_to_run_it": "How to run it",
    "what_would_surprise_you": "What would surprise you",
}

WORD_BUDGET: dict[SectionId, int] = {
    "what_this_is": 80,
    "how_its_laid_out": 250,
    "where_to_start_reading": 200,
    "how_to_run_it": 100,
    "what_would_surprise_you": 170,
}

MAX_SNIPPETS_PER_PAGE = 4
MAX_SNIPPET_LINES = 10
SNIPPETS_ALLOWED_IN: frozenset[SectionId] = frozenset(
    {"where_to_start_reading", "what_would_surprise_you"}
)

Stage = Literal["run", "fetch", "analyze", "llm", "grounding", "render"]
Trigger = Literal["cli", "eval"]


# --- what to explain -> fetch ----------------------------------------------

class SourceKind(StrEnum):
    """Where the files come from. One enum, so `fetch` has one door, not two."""

    GITHUB = "github"   # ask GitHub for the files, and for the sha
    LOCAL = "local"     # read a folder already on disk; the caller supplies url + commit


@dataclass(frozen=True, slots=True)
class Source:
    """What to explain.

    A LOCAL source has no url and no sha of its own, but the page links every path
    to GitHub and stamps a commit in the footer. So a LOCAL caller supplies both.
    For an eval case they are deliberate fiction, committed in the case, which is
    what lets a golden-set page be shaped exactly like a real one.
    """

    kind: SourceKind
    location: str                # a GitHub URL, or a folder path
    url: str | None = None       # LOCAL only. Ignored for GITHUB, which discovers it
    commit: str | None = None    # LOCAL only. Ignored for GITHUB, which discovers it

    def __post_init__(self) -> None:
        if self.kind is SourceKind.LOCAL and not (self.url and self.commit):
            raise ValueError("a LOCAL source must carry the url and commit the page needs")


# --- fetch -> analyze ------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SourceFile:
    """One text file downloaded from the repo."""

    path: str          # repo-relative, posix separators, e.g. "src/cli.py"
    text: str
    lines: tuple[str, ...]   # text.splitlines(), precomputed: grounding slices it a lot


@dataclass(frozen=True, slots=True)
class Repo:
    """Everything fetched, plus the two facts the page footer and links need."""

    url: str           # "https://github.com/owner/name" — the page links against this
    commit: str        # full sha — the footer stamp
    root: Path         # where the files landed on disk
    files: tuple[SourceFile, ...]
    skipped: tuple[str, ...] = ()   # binaries, vendored dirs — named so analyze can say so

    def by_path(self) -> dict[str, SourceFile]:
        return {f.path: f for f in self.files}


# --- analyze -> llm --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TopLevelEntry:
    path: str          # "src/", "tests/", "README.md"
    is_dir: bool
    file_count: int


@dataclass(frozen=True, slots=True)
class RepoStructure:
    """What `analyze` found. This is also, in practice, the prompt payload."""

    tree: tuple[str, ...]                    # every path fetched, sorted
    top_level: tuple[TopLevelEntry, ...]
    entry_points: tuple[str, ...]            # "src/cli.py", "main.py"
    manifests: tuple[SourceFile, ...]        # pyproject.toml, package.json — full text
    test_paths: tuple[str, ...]              # empty tuple means "no tests found"
    ecosystem: str | None                    # "python" | "node" | None if unrecognised


# --- llm -> grounding ------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Claim:
    """One assertion. `source_path` is SELF-REPORTED by the model (ADR 0001)."""

    text: str
    source_path: str | None


@dataclass(frozen=True, slots=True)
class SnippetRequest:
    """The model CHOOSES a snippet by pointing at lines; it never writes one."""

    path: str
    start_line: int    # 1-based, inclusive
    end_line: int      # 1-based, inclusive


@dataclass(frozen=True, slots=True)
class DraftSection:
    id: SectionId
    claims: tuple[Claim, ...]
    snippets: tuple[SnippetRequest, ...] = ()


@dataclass(frozen=True, slots=True)
class Draft:
    """Ungrounded model output. Never reaches `render`."""

    sections: tuple[DraftSection, ...]       # all five, in SECTION_ORDER
    paths_named: tuple[str, ...]             # every path the model mentioned anywhere


# --- grounding -> render ---------------------------------------------------

@dataclass(frozen=True, slots=True)
class Snippet:
    """A snippet whose text came out of the real file, not the model."""

    path: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True, slots=True)
class Section:
    id: SectionId
    claims: tuple[Claim, ...]                # every one has a source_path
    snippets: tuple[Snippet, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.claims


@dataclass(frozen=True, slots=True)
class DropCounts:
    paths_proposed: int = 0
    paths_dropped: int = 0
    snippets_proposed: int = 0
    snippets_dropped: int = 0
    claims_proposed: int = 0
    claims_dropped: int = 0
    dropped_paths: tuple[str, ...] = ()      # populated only under --record-paths


@dataclass(frozen=True, slots=True)
class Explanation:
    """Grounded. Everything here traces to a downloaded file."""

    sections: tuple[Section, ...]
    paths_kept: frozenset[str]
    drops: DropCounts


# --- render -> gate --------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SectionFacts:
    id: SectionId
    present: bool
    word_count: int
    snippet_count: int
    snippet_line_spans: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class PageFacts:
    """The gate's inputs, as data. ADR 0002: the gate must never re-parse our HTML."""

    sections: tuple[SectionFacts, ...]
    total_words: int
    total_snippets: int
    commit_stamp: str | None


@dataclass(frozen=True, slots=True)
class Page:
    html: str
    facts: PageFacts


# --- evals -----------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class GateResult:
    passed: bool
    failures: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    id: str
    requirement: str


@dataclass(frozen=True, slots=True)
class Case:
    name: str
    checklist: tuple[ChecklistItem, ...]
    source: Source        # kind=LOCAL, carrying the case's pretend url and sha


@dataclass(frozen=True, slots=True)
class Scores:
    """Three numbers. Deliberately not blended (ADR 0002)."""

    coverage_hit: int
    coverage_total: int
    false_claims: int
    clarity: int          # 1-5, the only rating


class Judge(Protocol):
    """A model judges every run; a mock judge keeps the eval test offline."""

    def score(self, page: Page, checklist: tuple[ChecklistItem, ...]) -> Scores: ...
