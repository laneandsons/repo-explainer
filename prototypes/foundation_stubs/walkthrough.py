"""PROTOTYPE — throwaway. Answers issue #5.

Run me:  uv run python prototypes/foundation_stubs/walkthrough.py

Nothing here is implemented. What this does is carry one worked example across
every seam by hand, printing the value at each boundary, so the question
"is this the right shape to hand the next agent?" can be answered by looking.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from domain import (  # noqa: E402
    SECTION_ORDER,
    Claim,
    Draft,
    DraftSection,
    DropCounts,
    Explanation,
    Page,
    PageFacts,
    Repo,
    RepoStructure,
    Section,
    SectionFacts,
    Source,
    SourceKind,
    Snippet,
    SnippetRequest,
    SourceFile,
    TopLevelEntry,
)

BAR = "=" * 72


def show(seam: str, produced_by: str, value: object) -> None:
    print(f"\n{BAR}\n  {seam}\n  produced by: {produced_by}\n{BAR}")
    print(value)


def src(path: str, text: str) -> SourceFile:
    return SourceFile(path=path, text=text, lines=tuple(text.splitlines()))


# --- 0. what to explain -> fetch -------------------------------------------

source = Source(kind=SourceKind.GITHUB, location="https://github.com/laneandsons/tiny")
show("SEAM 0  the ask -> fetch", "cli, or the eval harness, builds a Source", source)

eval_source = Source(
    kind=SourceKind.LOCAL,
    location="evals/cases/tiny/repo",
    url="https://github.com/example/tiny",          # fiction, committed in the case
    commit="0000000000000000000000000000000000000000",
)
print("\n  An eval case builds the same type, with the other kind:")
print(f"  {eval_source}")
print("  ^ No stage after fetch ever asks which kind it was.")

# --- 1. fetch -> analyze ---------------------------------------------------

CLI_PY = "import sys\n\ndef main():\n    print(sys.argv)\n"
repo = Repo(
    url="https://github.com/laneandsons/tiny",
    commit="a4f1c9e2b7d3f0a1c8e5b2d9f6a3c0e7b4d1f8a5",
    root=Path("/tmp/repo-explainer/a4f1c9e"),
    files=(
        src("pyproject.toml", '[project]\nname = "tiny"\n'),
        src("src/cli.py", CLI_PY),
        src("README.md", "# tiny\n"),
    ),
    skipped=("assets/logo.png",),
)
show("SEAM 1  fetch -> analyze", "fetch(source, ctx=ctx) -> Repo", repo)

# --- 2. analyze -> llm -----------------------------------------------------

structure = RepoStructure(
    tree=("README.md", "pyproject.toml", "src/cli.py"),
    top_level=(
        TopLevelEntry("README.md", is_dir=False, file_count=1),
        TopLevelEntry("pyproject.toml", is_dir=False, file_count=1),
        TopLevelEntry("src/", is_dir=True, file_count=1),
    ),
    entry_points=("src/cli.py",),
    manifests=(repo.by_path()["pyproject.toml"],),
    test_paths=(),                    # empty means "no tests found" — the page must say so
    ecosystem="python",
)
show("SEAM 2  analyze -> llm", "analyze(repo, ctx=ctx) -> RepoStructure", structure)

# --- 3. llm -> grounding ---------------------------------------------------

draft = Draft(
    sections=(
        DraftSection("what_this_is", (
            Claim("tiny is a command line tool.", "pyproject.toml"),
            Claim("It is widely used in production.", None),        # <- will be dropped
        )),
        DraftSection("how_its_laid_out", (
            Claim("All source lives under src/.", "src/cli.py"),
        )),
        DraftSection("where_to_start_reading", (
            Claim("Start at src/cli.py.", "src/cli.py"),
        ), (
            SnippetRequest("src/cli.py", 3, 4),
            SnippetRequest("src/core.py", 1, 5),                    # <- path does not exist
        )),
        DraftSection("how_to_run_it", (
            Claim("Run it with `uv run tiny`.", "pyproject.toml"),
        )),
        DraftSection("what_would_surprise_you", (
            Claim("There are no tests at all.", "pyproject.toml"),
        )),
    ),
    paths_named=("pyproject.toml", "src/cli.py", "src/core.py"),
)
show("SEAM 3  llm -> grounding", "draft(structure, provider=..., ctx=ctx) -> Draft", draft)
print("\n  ^ UNGROUNDED. One invented claim, one invented path. Neither reaches render.")

# --- 4. grounding -> render ------------------------------------------------

explanation = Explanation(
    sections=(
        Section("what_this_is", (Claim("tiny is a command line tool.", "pyproject.toml"),)),
        Section("how_its_laid_out", (Claim("All source lives under src/.", "src/cli.py"),)),
        Section("where_to_start_reading",
                (Claim("Start at src/cli.py.", "src/cli.py"),),
                (Snippet("src/cli.py", 3, 4, "def main():\n    print(sys.argv)"),)),
        Section("how_to_run_it", (Claim("Run it with `uv run tiny`.", "pyproject.toml"),)),
        Section("what_would_surprise_you", (Claim("There are no tests at all.", "pyproject.toml"),)),
    ),
    paths_kept=frozenset({"pyproject.toml", "src/cli.py"}),
    drops=DropCounts(
        paths_proposed=3, paths_dropped=1,
        snippets_proposed=2, snippets_dropped=1,
        claims_proposed=6, claims_dropped=1,
    ),
)
show("SEAM 4  grounding -> render", "ground(draft, repo, ctx=ctx) -> Explanation", explanation)
print("\n  ^ The snippet text came out of the real file, not the model.")
print("  ^ drops is what grounding.completed carries. This is the whole point of events.")

# --- 5. render -> gate -----------------------------------------------------

page = Page(
    html="<!doctype html><html>...three hundred lines of page...</html>",
    facts=PageFacts(
        sections=tuple(
            SectionFacts(sid, present=True, word_count=w, snippet_count=s, snippet_line_spans=spans)
            for sid, w, s, spans in (
                ("what_this_is", 7, 0, ()),
                ("how_its_laid_out", 5, 0, ()),
                ("where_to_start_reading", 4, 1, ((3, 4),)),
                ("how_to_run_it", 5, 0, ()),
                ("what_would_surprise_you", 6, 0, ()),
            )
        ),
        total_words=27,
        total_snippets=1,
        commit_stamp="a4f1c9e",
    ),
)
show("SEAM 5  render -> gate", "render(explanation, repo, ctx=ctx) -> Page", page.facts)
print(f"\n  html: {len(page.html)} chars, not shown.")
print("  ^ The gate reads facts. It never parses the html we just produced.")

# --- what each build ticket owns -------------------------------------------

print(f"\n{BAR}\n  ONE FILE PER BUILD TICKET — the collision rule, made real\n{BAR}")
for owner, files in (
    ("B1 foundation (runs alone, first)", "domain.py  events.py  log.py  run.py  grounding.py  + every stub below"),
    ("B2 fetch", "fetch.py"),
    ("B3 analyze", "analyze.py"),
    ("B4 llm", "llm.py"),
    ("B5 render", "render.py"),
    ("B6 evals", "evals.py"),
    ("B7 cli", "cli.py"),
):
    print(f"  {owner:36} {files}")
print(f"\n  Sections, fixed by foundation: {', '.join(SECTION_ORDER)}")
