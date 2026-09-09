"""PROTOTYPE — throwaway. Answers issue #5.

`RunContext` is the one object threaded through every module. It is how any stage
reaches foundation, and it is the only argument every stage function shares.
"""

from __future__ import annotations

from dataclasses import dataclass

from events import EventSink
from log import Logger
from domain import Trigger


@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str
    trigger: Trigger      # "cli" | "eval" — evals must set "eval" (ADR 0001)
    events: EventSink     # NullSink under --no-events
    log: Logger
    record_paths: bool = False   # --record-paths: names of dropped paths, off by default
