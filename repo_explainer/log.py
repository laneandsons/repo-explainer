"""Log records: diagnostic lines for a person debugging right now.

Disposable, and free to change shape at any time. They are NOT events — different
reader, different lifetime (CONTEXT.md). Named `log.py`, not `logging.py`, so
nothing has to think about the standard library module.

Records go to stderr and nowhere else. Nothing here ever touches the events file.
"""

from __future__ import annotations

import sys
from typing import Protocol, TextIO


class Logger(Protocol):
    def debug(self, msg: str, **kv: object) -> None: ...
    def info(self, msg: str, **kv: object) -> None: ...
    def warn(self, msg: str, **kv: object) -> None: ...
    def error(self, msg: str, **kv: object) -> None: ...


class StderrLogger:
    """One line per record: `LEVEL name: message key=value`. Debug needs `verbose`."""

    def __init__(self, name: str, *, verbose: bool = False,
                 stream: TextIO | None = None) -> None:
        self.name = name
        self.verbose = verbose
        self._stream = stream

    def debug(self, msg: str, **kv: object) -> None:
        if self.verbose:
            self._emit("DEBUG", msg, kv)

    def info(self, msg: str, **kv: object) -> None:
        self._emit("INFO", msg, kv)

    def warn(self, msg: str, **kv: object) -> None:
        self._emit("WARN", msg, kv)

    def error(self, msg: str, **kv: object) -> None:
        self._emit("ERROR", msg, kv)

    def _emit(self, level: str, msg: str, kv: dict[str, object]) -> None:
        pairs = "".join(f" {key}={value!r}" for key, value in kv.items())
        stream = self._stream if self._stream is not None else sys.stderr
        print(f"{level} {self.name}: {msg}{pairs}", file=stream)


def get_logger(name: str, *, verbose: bool = False) -> Logger:
    """One logger per module: get_logger("fetch")."""
    return StderrLogger(name, verbose=verbose)
