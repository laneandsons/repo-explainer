"""PROTOTYPE — throwaway. Answers issue #5.

`foundation` owns every event name and every field name (ADR 0001). Other modules
never build an event dict; they call one of the eight functions below. That is what
stops two stages disagreeing about what `duration_ms` means.
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from domain import Stage, Trigger  # prototype-local import; real tree uses the package

SCHEMA_VERSION = 1

DEFAULT_EVENTS_PATH = (
    Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    / "repo-explainer"
    / "events.jsonl"
)

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

    def __init__(self, run_id: str, path: Path = DEFAULT_EVENTS_PATH) -> None:
        self.run_id = run_id
        self.path = path

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
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(line) + "\n")
        except OSError:
            pass               # swallowed on purpose. At most a log record, never a raise.


class NullSink:
    """--no-events."""

    def write(self, event: str, stage: Stage, **fields: object) -> None:
        return None


# --- The eight moments. These signatures ARE the field-name contract. -------

def run_started(sink: EventSink, *, repo: str, commit: str, trigger: Trigger,
                flags: dict[str, object]) -> None: ...

def fetch_completed(sink: EventSink, *, file_count: int, total_bytes: int,
                    duration_ms: int) -> None: ...

def analyze_completed(sink: EventSink, *, files_considered: int, entry_points_found: int,
                      duration_ms: int) -> None: ...

def llm_completed(sink: EventSink, *, model: str, input_tokens: int, output_tokens: int,
                  duration_ms: int) -> None: ...

def grounding_completed(sink: EventSink, *, paths_proposed: int, paths_dropped: int,
                        snippets_proposed: int, snippets_dropped: int,
                        claims_proposed: int, claims_dropped: int,
                        dropped_paths: tuple[str, ...] = ()) -> None: ...

def render_completed(sink: EventSink, *, sections_rendered: int, empty_sections: int,
                     prose_word_count: int, snippet_count: int) -> None: ...

def run_completed(sink: EventSink, *, duration_ms: int, total_tokens: int) -> None: ...

def run_failed(sink: EventSink, *, stage: Stage, error_type: str) -> None: ...
