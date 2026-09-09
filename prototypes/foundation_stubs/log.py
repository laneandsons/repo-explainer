"""PROTOTYPE — throwaway. Answers issue #5.

Log records are for a person debugging right now, and are free to change shape
(CONTEXT.md). They are NOT events. Named `log.py`, not `logging.py`, so nothing
has to think about the standard library module.
"""

from __future__ import annotations

from typing import Protocol


class Logger(Protocol):
    def debug(self, msg: str, **kv: object) -> None: ...
    def info(self, msg: str, **kv: object) -> None: ...
    def warn(self, msg: str, **kv: object) -> None: ...
    def error(self, msg: str, **kv: object) -> None: ...


def get_logger(name: str, *, verbose: bool = False) -> Logger:
    """One logger per module: get_logger("fetch")."""
    raise NotImplementedError("foundation builds this")
