"""Events: one durable record per moment, appended to `events.jsonl` (ADR 0001).

`foundation` owns every event name and every field name. Other modules never build
an event dict; they call one of the eight functions below. That is what stops two
stages disagreeing about what `duration_ms` means.
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from repo_explainer.domain import Stage, Trigger

SCHEMA_VERSION = 1


def default_events_path() -> Path:
    """`$XDG_DATA_HOME/repo-explainer/events.jsonl`, never inside the working tree.

    Read on every call rather than frozen at import, and an empty XDG_DATA_HOME is
    treated as unset — `Path("")` is `Path(".")`, which would put the run record in
    whatever directory the command was run from, and for this tool that is the clone.
    """
    home = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return Path(home) / "repo-explainer" / "events.jsonl"


DEFAULT_EVENTS_PATH = default_events_path()

EVENT_NAMES = (
    "run.started",
    "fetch.completed",
    "analyze.completed",
    "llm.completed",
    "grounding.completed",
    "render.completed",
    "run.completed",
    "run.failed",
)


def new_run_id() -> str:
    """<compact UTC ISO 8601>-<4 hex>, so the file sorts into run order."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}-{secrets.token_hex(2)}"


class EventSink(Protocol):
    def write(self, event: str, stage: Stage, **fields: object) -> None: ...


class JsonlSink:
    """Append-only. Every failure is swallowed (ADR 0001): telemetry never breaks a run."""

    def __init__(self, run_id: str, path: Path | None = None) -> None:
        self.run_id = run_id
        self.path = path if path is not None else default_events_path()

    def write(self, event: str, stage: Stage, **fields: object) -> None:
        line = {
            "v": SCHEMA_VERSION,
            "run_id": self.run_id,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "event": event,
            "stage": stage,
            **fields,          # flat, never nested under "data"
        }
        try:
            # default=str so a Path or an enum in `flags` cannot raise on the way out.
            rendered = json.dumps(line, default=str)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(rendered + "\n")
        except (OSError, TypeError, ValueError):
            pass               # swallowed on purpose. At most a log record, never a raise.


class NullSink:
    """--no-events."""

    def write(self, event: str, stage: Stage, **fields: object) -> None:
        return None


# --- The eight moments. These signatures ARE the field-name contract. -------

def run_started(sink: EventSink, *, repo: str, commit: str, trigger: Trigger,
                flags: dict[str, object]) -> None:
    sink.write("run.started", "run", repo=repo, commit=commit, trigger=trigger,
               flags=flags)


def fetch_completed(sink: EventSink, *, file_count: int, total_bytes: int,
                    duration_ms: int) -> None:
    sink.write("fetch.completed", "fetch", file_count=file_count,
               total_bytes=total_bytes, duration_ms=duration_ms)


def analyze_completed(sink: EventSink, *, files_considered: int, entry_points_found: int,
                      duration_ms: int) -> None:
    sink.write("analyze.completed", "analyze", files_considered=files_considered,
               entry_points_found=entry_points_found, duration_ms=duration_ms)


def llm_completed(sink: EventSink, *, model: str, input_tokens: int, output_tokens: int,
                  duration_ms: int) -> None:
    sink.write("llm.completed", "llm", model=model, input_tokens=input_tokens,
               output_tokens=output_tokens, duration_ms=duration_ms)


def grounding_completed(sink: EventSink, *, paths_proposed: int, paths_dropped: int,
                        snippets_proposed: int, snippets_dropped: int,
                        claims_proposed: int, claims_dropped: int,
                        dropped_paths: tuple[str, ...] = ()) -> None:
    sink.write("grounding.completed", "grounding", paths_proposed=paths_proposed,
               paths_dropped=paths_dropped, snippets_proposed=snippets_proposed,
               snippets_dropped=snippets_dropped, claims_proposed=claims_proposed,
               claims_dropped=claims_dropped, dropped_paths=dropped_paths)


def render_completed(sink: EventSink, *, sections_rendered: int, empty_sections: int,
                     prose_word_count: int, snippet_count: int) -> None:
    sink.write("render.completed", "render", sections_rendered=sections_rendered,
               empty_sections=empty_sections, prose_word_count=prose_word_count,
               snippet_count=snippet_count)


def run_completed(sink: EventSink, *, duration_ms: int, total_tokens: int) -> None:
    sink.write("run.completed", "run", duration_ms=duration_ms,
               total_tokens=total_tokens)


def run_failed(sink: EventSink, *, stage: Stage, error_type: str) -> None:
    # `stage` fills the envelope's own stage field rather than riding alongside it:
    # for a failure the stage that failed IS the stage of the line, and the envelope
    # already has that field, so duplicating it would be the one renamed field the
    # build ticket forbids.
    sink.write("run.failed", stage, error_type=error_type)
