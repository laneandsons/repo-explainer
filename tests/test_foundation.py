"""The foundation build ticket's own tests (issue #12).

The `Repo` under test is built by hand. `fetch` is a stub owned by someone else,
so nothing here calls it.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from repo_explainer.domain import (
    MAX_SNIPPET_LINES,
    Claim,
    Draft,
    DraftSection,
    Repo,
    Source,
    SourceFile,
    SourceKind,
)
from repo_explainer.events import EVENT_NAMES, JsonlSink, run_started
from repo_explainer.grounding import ground
from repo_explainer.log import get_logger
from repo_explainer.run import RunContext

PACKAGE_MODULES = (
    "repo_explainer",
    "repo_explainer.domain",
    "repo_explainer.events",
    "repo_explainer.log",
    "repo_explainer.run",
    "repo_explainer.grounding",
    "repo_explainer.fetch",
    "repo_explainer.analyze",
    "repo_explainer.llm",
    "repo_explainer.render",
    "repo_explainer.evals",
    "repo_explainer.cli",
)


# --- hand-built fixtures ---------------------------------------------------

class RecordingSink:
    """An EventSink that keeps every write, so a test can read the fields back."""

    def __init__(self) -> None:
        self.writes: list[tuple[str, str, dict[str, object]]] = []

    def write(self, event: str, stage: str, **fields: object) -> None:
        self.writes.append((event, stage, fields))


def source_file(path: str, text: str) -> SourceFile:
    return SourceFile(path=path, text=text, lines=tuple(text.splitlines()))


def repo_of(*files: SourceFile) -> Repo:
    return Repo(
        url="https://github.com/owner/name",
        commit="a" * 40,
        root=Path("/nowhere"),
        files=files,
    )


def context(sink: RecordingSink, *, record_paths: bool = False) -> RunContext:
    return RunContext(
        run_id="20260910T000000-abcd",
        trigger="eval",
        events=sink,
        log=get_logger("test"),
        record_paths=record_paths,
    )


def draft_of(
    *,
    claims: tuple[Claim, ...] = (),
    snippets: tuple = (),
    paths_named: tuple[str, ...] = (),
) -> Draft:
    return Draft(
        sections=(
            DraftSection(id="where_to_start_reading", claims=claims, snippets=snippets),
        ),
        paths_named=paths_named,
    )


def only_section(explanation):
    assert len(explanation.sections) == 1
    return explanation.sections[0]


# --- grounding: the path check ---------------------------------------------

def test_grounding_drops_a_path_that_is_not_in_the_repo():
    repo = repo_of(source_file("README.md", "hello\n"))
    draft = draft_of(paths_named=("README.md", "ghost.py"))

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    assert explanation.paths_kept == frozenset({"README.md"})
    assert explanation.drops.paths_proposed == 2
    assert explanation.drops.paths_dropped == 1


# --- grounding: the snippet check ------------------------------------------

def test_grounding_slices_snippet_text_out_of_the_real_file():
    from repo_explainer.domain import SnippetRequest

    text = "one\ntwo\nthree\nfour\n"
    repo = repo_of(source_file("src/cli.py", text))
    draft = draft_of(
        snippets=(SnippetRequest(path="src/cli.py", start_line=2, end_line=3),),
        paths_named=("src/cli.py",),
    )

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    snippet = only_section(explanation).snippets[0]
    assert snippet.text == "two\nthree"
    assert snippet.path == "src/cli.py"
    assert (snippet.start_line, snippet.end_line) == (2, 3)
    assert explanation.drops.snippets_proposed == 1
    assert explanation.drops.snippets_dropped == 0


def test_grounding_drops_a_snippet_whose_line_range_runs_past_the_end_of_the_file():
    from repo_explainer.domain import SnippetRequest

    repo = repo_of(source_file("src/cli.py", "one\ntwo\n"))
    draft = draft_of(
        snippets=(SnippetRequest(path="src/cli.py", start_line=2, end_line=9),),
        paths_named=("src/cli.py",),
    )

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    assert only_section(explanation).snippets == ()
    assert explanation.drops.snippets_dropped == 1


def test_grounding_drops_a_snippet_longer_than_the_line_limit():
    from repo_explainer.domain import SnippetRequest

    over = MAX_SNIPPET_LINES + 1
    repo = repo_of(source_file("src/cli.py", "\n".join(f"line {n}" for n in range(1, over + 1))))
    draft = draft_of(
        snippets=(SnippetRequest(path="src/cli.py", start_line=1, end_line=over),),
        paths_named=("src/cli.py",),
    )

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    assert only_section(explanation).snippets == ()
    assert explanation.drops.snippets_dropped == 1


# --- grounding: the claim check --------------------------------------------

def test_grounding_drops_a_claim_that_cites_no_file():
    repo = repo_of(source_file("README.md", "hello\n"))
    kept = Claim(text="it is a command line tool", source_path="README.md")
    draft = draft_of(
        claims=(kept, Claim(text="it appears to be fast", source_path=None)),
        paths_named=("README.md",),
    )

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    assert only_section(explanation).claims == (kept,)
    assert explanation.drops.claims_proposed == 2
    assert explanation.drops.claims_dropped == 1


def test_grounding_drops_a_claim_citing_a_path_that_was_itself_dropped():
    repo = repo_of(source_file("README.md", "hello\n"))
    kept = Claim(text="it is a command line tool", source_path="README.md")
    draft = draft_of(
        claims=(kept, Claim(text="it has a scheduler", source_path="ghost.py")),
        paths_named=("README.md", "ghost.py"),
    )

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    assert only_section(explanation).claims == (kept,)
    assert explanation.drops.claims_dropped == 1


# --- grounding: what the drop counts name ----------------------------------

def test_drop_counts_name_dropped_paths_only_under_record_paths():
    repo = repo_of(source_file("README.md", "hello\n"))
    draft = draft_of(paths_named=("README.md", "ghost.py"))

    silent = RecordingSink()
    quiet = ground(draft, repo, ctx=context(silent))
    assert quiet.drops.dropped_paths == ()
    assert silent.writes[-1][2]["dropped_paths"] == ()

    loud_sink = RecordingSink()
    loud = ground(draft, repo, ctx=context(loud_sink, record_paths=True))
    assert loud.drops.dropped_paths == ("ghost.py",)

    event, stage, fields = loud_sink.writes[-1]
    assert (event, stage) == ("grounding.completed", "grounding")
    assert fields["dropped_paths"] == ("ghost.py",)
    assert fields["paths_dropped"] == 1


# --- events ----------------------------------------------------------------

def test_an_event_line_is_flat_and_carries_the_five_field_envelope(tmp_path):
    path = tmp_path / "events.jsonl"
    sink = JsonlSink(run_id="20260910T000000-abcd", path=path)

    run_started(
        sink,
        repo="https://github.com/owner/name",
        commit="a" * 40,
        trigger="cli",
        flags={"record_paths": False},
    )

    line = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert {"v", "run_id", "ts", "event", "stage"} <= set(line)
    assert line["event"] == "run.started"
    assert line["event"] in EVENT_NAMES
    assert line["stage"] == "run"
    assert line["run_id"] == "20260910T000000-abcd"
    assert line["repo"] == "https://github.com/owner/name"
    assert line["commit"] == "a" * 40
    assert line["trigger"] == "cli"
    assert "data" not in line


def test_an_event_write_failure_does_not_raise(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where a directory would have to be", encoding="utf-8")
    sink = JsonlSink(run_id="20260910T000000-abcd", path=blocker / "events.jsonl")

    run_started(
        sink,
        repo="https://github.com/owner/name",
        commit="a" * 40,
        trigger="cli",
        flags={},
    )

    assert not (blocker / "events.jsonl").exists()


# --- domain ----------------------------------------------------------------

def test_a_local_source_missing_its_url_or_commit_is_refused():
    with pytest.raises(ValueError):
        Source(kind=SourceKind.LOCAL, location="evals/cases/tiny")

    with pytest.raises(ValueError):
        Source(
            kind=SourceKind.LOCAL,
            location="evals/cases/tiny",
            url="https://github.com/owner/name",
        )

    ok = Source(
        kind=SourceKind.LOCAL,
        location="evals/cases/tiny",
        url="https://github.com/owner/name",
        commit="a" * 40,
    )
    assert ok.commit == "a" * 40

    assert Source(kind=SourceKind.GITHUB, location="https://github.com/owner/name")


# --- the package ------------------------------------------------------------

def test_every_module_in_the_package_imports():
    for name in PACKAGE_MODULES:
        assert importlib.import_module(name) is not None


# --- what the review found ---------------------------------------------------

def test_a_path_named_many_times_counts_once():
    repo = repo_of(source_file("README.md", "hello\n"))
    draft = draft_of(paths_named=("ghost.py", "README.md", "ghost.py", "ghost.py"))

    sink = RecordingSink()
    explanation = ground(draft, repo, ctx=context(sink, record_paths=True))

    assert explanation.drops.paths_proposed == 2
    assert explanation.drops.paths_dropped == 1
    assert explanation.drops.dropped_paths == ("ghost.py",)


def test_paths_kept_names_the_file_behind_every_surviving_claim_and_snippet():
    from repo_explainer.domain import SnippetRequest

    repo = repo_of(
        source_file("README.md", "hello\n"),
        source_file("src/cli.py", "one\ntwo\n"),
    )
    # The model cited two real files but listed neither in paths_named.
    draft = draft_of(
        claims=(Claim(text="it has a command line", source_path="README.md"),),
        snippets=(SnippetRequest(path="src/cli.py", start_line=1, end_line=2),),
        paths_named=(),
    )

    explanation = ground(draft, repo, ctx=context(RecordingSink()))

    assert explanation.paths_kept == frozenset({"README.md", "src/cli.py"})


def test_an_unserialisable_event_field_does_not_raise(tmp_path):
    path = tmp_path / "events.jsonl"
    sink = JsonlSink(run_id="20260910T000000-abcd", path=path)

    run_started(
        sink,
        repo="https://github.com/owner/name",
        commit="a" * 40,
        trigger="cli",
        flags={"out": tmp_path / "explanation.html", "kind": SourceKind.LOCAL},
    )

    line = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert line["flags"]["out"] == str(tmp_path / "explanation.html")


def test_an_empty_xdg_data_home_does_not_put_the_events_file_in_the_clone(monkeypatch):
    from repo_explainer.events import default_events_path

    monkeypatch.setenv("XDG_DATA_HOME", "")
    assert default_events_path().is_absolute()

    monkeypatch.setenv("XDG_DATA_HOME", "/somewhere/share")
    assert default_events_path() == Path("/somewhere/share/repo-explainer/events.jsonl")
    assert JsonlSink(run_id="r").path == Path("/somewhere/share/repo-explainer/events.jsonl")
