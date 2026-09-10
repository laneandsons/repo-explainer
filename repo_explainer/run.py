"""`RunContext` is the one object threaded through every module.

It is how any stage reaches foundation — `ctx.log` for log records, `ctx.events`
for events — and it is the only argument every stage function shares.
"""

from __future__ import annotations

from dataclasses import dataclass

from repo_explainer.domain import Trigger
from repo_explainer.events import EventSink
from repo_explainer.log import Logger


@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str
    trigger: Trigger      # "cli" | "eval" — evals must set "eval" (ADR 0001)
    events: EventSink     # NullSink under --no-events
    log: Logger
    record_paths: bool = False   # --record-paths: names of dropped paths, off by default
