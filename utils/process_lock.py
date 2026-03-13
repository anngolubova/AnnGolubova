from __future__ import annotations

import fcntl
from pathlib import Path


class ProcessAlreadyRunningError(RuntimeError):
    """Raised when another process already holds the app lock."""


class SingleInstanceLock:
    def __init__(self, lock_path: str) -> None:
        self._lock_file_path = Path(lock_path)
        self._file_handle = None

    def acquire(self) -> None:
        self._lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_handle = self._lock_file_path.open("w", encoding="utf-8")
        try:
            fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self._file_handle.close()
            self._file_handle = None
            raise ProcessAlreadyRunningError(
                "Another app.py process is already running. Stop duplicate processes first."
            ) from error

        self._file_handle.write(str(self._lock_file_path))
        self._file_handle.flush()

    def release(self) -> None:
        if self._file_handle is None:
            return
        try:
            fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._file_handle.close()
            self._file_handle = None
