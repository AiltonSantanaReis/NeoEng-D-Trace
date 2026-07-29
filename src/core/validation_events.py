"""Structured, privacy-preserving manual validation events.

The recorder is opt-in. Normal application behavior is unchanged unless the
launcher receives ``--validation-log``. Each JSON line is flushed immediately
so an abnormal termination still leaves useful evidence.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from src.core.app_identity import APP_DISPLAY_NAME, LOGGER_NAME

_STATUS_ERROR = {"FAILURE", "UNHANDLED_EXCEPTION"}
_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/](?:[^\s\"']+[\\/]?)+"),
    re.compile(r"/(?:home|mnt|Users|tmp)/(?:[^\s\"']+/?) +".replace(" ", "")),
)
_PROCESS_TOKEN_KEY = secrets.token_bytes(32)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _sanitize_text(value: str) -> str:
    text = str(value)
    for pattern in _PATH_PATTERNS:
        text = pattern.sub("<PATH>", text)
    return text.replace("\r", "\\r").replace("\n", "\\n")


def _sanitize_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, dict):
        return {str(key): _sanitize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in value]
    return _sanitize_text(repr(value))


def object_token(value: Any) -> Optional[str]:
    """Return a process-local pseudonymous token for an object identifier.

    The HMAC key is random and never written to the log, so predictable object
    identifiers cannot be recovered through a precomputed hash dictionary.
    Tokens remain stable during one application process, which is sufficient to
    correlate selection and export events in the same validation session.
    """

    if value is None:
        return None
    recorder = _recorder
    key = recorder._token_key if recorder is not None else _PROCESS_TOKEN_KEY
    digest = hmac.new(
        key,
        str(value).encode("utf-8", errors="replace"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:12]


def file_evidence(path: str | os.PathLike[str] | None) -> Dict[str, Any]:
    """Return non-sensitive postcondition evidence for a generated file."""

    if not path:
        return {"exists": False, "size": 0, "suffix": None}
    target = Path(path)
    try:
        exists = target.is_file()
        size = target.stat().st_size if exists else 0
    except OSError:
        exists = False
        size = 0
    return {
        "exists": exists,
        "size": size,
        "suffix": target.suffix.lower() or None,
    }


class _ValidationRecorder:
    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = uuid.uuid4().hex[:16]
        self._token_key = secrets.token_bytes(32)
        self._lock = threading.RLock()
        self._handle = self.path.open("a", encoding="utf-8", newline="\n")
        self._event_status: Dict[str, str] = {}
        self._failure_count = 0
        self._closed = False
        self.write(
            "session.start",
            "SUCCESS",
            application=APP_DISPLAY_NAME,
            python=(
                f"{sys.version_info.major}."
                f"{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            ),
            pid=os.getpid(),
        )

    def write(self, event: str, status: str = "INFO", **details: Any) -> None:
        normalized_status = str(status).upper()
        payload = {
            "timestamp_utc": _utc_now(),
            "session_id": self.session_id,
            "event": str(event),
            "status": normalized_status,
            "details": _sanitize_value(details),
        }
        with self._lock:
            if self._closed:
                return
            self._handle.write(
                json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
            )
            self._handle.flush()
            self._event_status[str(event)] = normalized_status
            if (
                str(event) != "session.summary"
                and normalized_status in _STATUS_ERROR
            ):
                self._failure_count += 1

    def write_exception(
        self,
        event: str,
        exc: BaseException,
        *,
        status: str = "FAILURE",
        traceback_object=None,
        **details: Any,
    ) -> None:
        tb = traceback_object if traceback_object is not None else exc.__traceback__
        if tb is None:
            trace = "".join(traceback.format_exception_only(type(exc), exc))
        else:
            trace = "".join(traceback.format_exception(type(exc), exc, tb))
        self.write(
            event,
            status,
            error_type=type(exc).__name__,
            error_message=_sanitize_text(str(exc)),
            traceback=_sanitize_text(trace),
            **details,
        )

    def close(self, *, exit_code: int = 0, expected_events: Iterable[str] = ()) -> None:
        with self._lock:
            if self._closed:
                return
            expected = list(expected_events)
            missing = [
                event
                for event in expected
                if self._event_status.get(event) != "SUCCESS"
            ]
            if self._failure_count or int(exit_code) != 0:
                summary_status = "FAILURE"
            elif missing:
                summary_status = "INCOMPLETE"
            else:
                summary_status = "SUCCESS"
            self.write(
                "session.summary",
                summary_status,
                exit_code=int(exit_code),
                failure_count=self._failure_count,
                expected_events=expected,
                missing_success_events=missing,
                observed_status=self._event_status,
            )
            self._closed = True
            self._handle.close()


class _ValidationLogCapture(logging.Handler):
    """Capture WARNING+ records without changing normal logger routing."""

    def emit(self, record: logging.LogRecord) -> None:
        recorder = _recorder
        if recorder is None or getattr(record, "validation_event_recorded", False):
            return
        try:
            details: Dict[str, Any] = {
                "logger": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
            }
            if record.exc_info:
                details["traceback"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )
            recorder.write(
                "python.log",
                "FAILURE" if record.levelno >= logging.ERROR else "WARNING",
                **details,
            )
        except Exception:
            # Observability must never crash the application being observed.
            return


_recorder: Optional[_ValidationRecorder] = None
_capture_handler: Optional[_ValidationLogCapture] = None
_capture_targets: list[logging.Logger] = []
_previous_excepthook = None
_previous_threading_excepthook = None


def validation_enabled() -> bool:
    return _recorder is not None


def validation_output_directory() -> Optional[Path]:
    """Return the private output directory for the active validation session.

    A session identifier is part of the path. Reusing the same JSONL filename
    therefore cannot make a stale file from an earlier run satisfy a current
    exporter postcondition.
    """

    recorder = _recorder
    if recorder is None:
        return None
    output = (
        recorder.path.parent / "export_outputs" / recorder.session_id
    ).resolve()
    output.mkdir(parents=True, exist_ok=True)
    return output


def validation_output_path(
    relative_path: str | os.PathLike[str],
    *,
    directory: bool = False,
) -> Optional[Path]:
    """Allocate a path inside the active validation session sandbox.

    Absolute paths and parent traversal are rejected. Outside validation mode,
    ``None`` is returned so the normal native file dialog remains authoritative.
    """

    root = validation_output_directory()
    if root is None:
        return None

    relative = Path(relative_path)
    if relative.is_absolute() or relative.drive or ".." in relative.parts:
        raise ValueError("Validation output must be a relative sandbox path")
    if not relative.parts or relative == Path("."):
        raise ValueError("Validation output path cannot be empty")

    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Validation output escaped the session sandbox")

    if directory:
        target.mkdir(parents=True, exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
    return target


def start_validation_session(path: str | os.PathLike[str]) -> None:
    global _recorder, _capture_handler, _capture_targets
    global _previous_excepthook, _previous_threading_excepthook
    if _recorder is not None:
        raise RuntimeError("Validation session already active")
    _recorder = _ValidationRecorder(path)

    handler = _ValidationLogCapture(level=logging.WARNING)
    handler.setLevel(logging.WARNING)
    _capture_handler = handler
    root_logger = logging.getLogger()
    app_logger = logging.getLogger(LOGGER_NAME)
    _capture_targets = [root_logger]
    root_logger.addHandler(handler)
    if not app_logger.propagate:
        app_logger.addHandler(handler)
        _capture_targets.append(app_logger)

    _previous_excepthook = sys.excepthook

    def _hook(exc_type, exc, tb):
        record_validation_exception(
            "unhandled.exception",
            exc,
            status="UNHANDLED_EXCEPTION",
            traceback_object=tb,
        )
        logging.getLogger(LOGGER_NAME).critical(
            "Unhandled exception",
            exc_info=(exc_type, exc, tb),
            extra={"validation_event_recorded": True},
        )
        if _previous_excepthook is not None:
            _previous_excepthook(exc_type, exc, tb)

    sys.excepthook = _hook

    if hasattr(threading, "excepthook"):
        _previous_threading_excepthook = threading.excepthook

        def _thread_hook(args):
            record_validation_exception(
                "unhandled.thread_exception",
                args.exc_value,
                status="UNHANDLED_EXCEPTION",
                traceback_object=args.exc_traceback,
                thread_name=getattr(args.thread, "name", None),
            )
            if _previous_threading_excepthook is not None:
                _previous_threading_excepthook(args)

        threading.excepthook = _thread_hook


def record_validation_event(event: str, status: str = "INFO", **details: Any) -> None:
    recorder = _recorder
    if recorder is not None:
        recorder.write(event, status, **details)


def record_validation_exception(
    event: str,
    exc: BaseException,
    *,
    status: str = "FAILURE",
    traceback_object=None,
    **details: Any,
) -> None:
    recorder = _recorder
    if recorder is not None:
        recorder.write_exception(
            event,
            exc,
            status=status,
            traceback_object=traceback_object,
            **details,
        )


def stop_validation_session(
    *, exit_code: int = 0, expected_events: Iterable[str] = ()
) -> None:
    global _recorder, _capture_handler, _capture_targets
    global _previous_excepthook, _previous_threading_excepthook
    recorder = _recorder
    if recorder is None:
        return
    try:
        recorder.close(exit_code=exit_code, expected_events=expected_events)
    finally:
        if _capture_handler is not None:
            for target in _capture_targets:
                target.removeHandler(_capture_handler)
            _capture_handler.close()
        if _previous_excepthook is not None:
            sys.excepthook = _previous_excepthook
        if (
            _previous_threading_excepthook is not None
            and hasattr(threading, "excepthook")
        ):
            threading.excepthook = _previous_threading_excepthook
        _capture_handler = None
        _capture_targets = []
        _previous_excepthook = None
        _previous_threading_excepthook = None
        _recorder = None


def elapsed_ms(started_at: float) -> int:
    return max(0, int(round((time.perf_counter() - started_at) * 1000)))
