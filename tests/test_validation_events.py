import json
import logging
from pathlib import Path
import threading

import pytest

from src.core.app_identity import LOGGER_NAME
from src.core.validation_events import (
    file_evidence,
    object_token,
    record_validation_event,
    record_validation_exception,
    start_validation_session,
    stop_validation_session,
    validation_output_directory,
    validation_output_path,
)


def _read_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def test_validation_session_flushes_structured_events_and_truthful_summary(tmp_path):
    output = tmp_path / "manual-validation.jsonl"
    start_validation_session(output)
    try:
        record_validation_event(
            "language.changed",
            "SUCCESS",
            requested="pt",
            sensitive_path=r"C:\\Users\\someone\\Pictures\\asset.png",
        )
    finally:
        stop_validation_session(
            exit_code=0,
            expected_events=("language.changed", "export.metadata"),
        )

    rows = _read_jsonl(output)
    assert rows[0]["event"] == "session.start"
    assert rows[-1]["event"] == "session.summary"
    assert rows[-1]["status"] == "INCOMPLETE"
    assert rows[-1]["details"]["missing_success_events"] == ["export.metadata"]
    serialized = output.read_text(encoding="utf-8")
    assert "someone" not in serialized
    assert "<PATH>" in serialized


def test_validation_summary_reports_failure_for_nonzero_exit(tmp_path):
    output = tmp_path / "failed-exit.jsonl"
    start_validation_session(output)
    stop_validation_session(exit_code=7)

    summary = _read_jsonl(output)[-1]
    assert summary["event"] == "session.summary"
    assert summary["status"] == "FAILURE"
    assert summary["details"]["exit_code"] == 7


def test_validation_session_captures_warning_without_duplicate_root_route(tmp_path):
    output = tmp_path / "warnings.jsonl"
    start_validation_session(output)
    try:
        logging.getLogger(LOGGER_NAME).warning("controlled warning")
    finally:
        stop_validation_session(exit_code=0)

    rows = _read_jsonl(output)
    warnings = [row for row in rows if row["event"] == "python.log"]
    assert len(warnings) == 1
    assert warnings[0]["status"] == "WARNING"




def test_explicit_validation_event_suppresses_duplicate_python_log(tmp_path):
    output = tmp_path / "deduplicated-error.jsonl"
    start_validation_session(output)
    try:
        record_validation_exception("controlled.failure", RuntimeError("boom"))
        logging.getLogger(LOGGER_NAME).error(
            "boom", extra={"validation_event_recorded": True}
        )
    finally:
        stop_validation_session(exit_code=0)

    rows = _read_jsonl(output)
    assert len([row for row in rows if row["event"] == "controlled.failure"]) == 1
    assert not [row for row in rows if row["event"] == "python.log"]
    assert rows[-1]["details"]["failure_count"] == 1

def test_validation_session_captures_unhandled_thread_exception(tmp_path, monkeypatch):
    output = tmp_path / "thread-exception.jsonl"
    monkeypatch.setattr(threading, "excepthook", lambda args: None)

    start_validation_session(output)
    try:
        worker = threading.Thread(
            target=lambda: (_ for _ in ()).throw(RuntimeError("thread boom")),
            name="validation-worker",
        )
        worker.start()
        worker.join()
    finally:
        stop_validation_session(exit_code=0)

    rows = _read_jsonl(output)
    failure = next(
        row for row in rows if row["event"] == "unhandled.thread_exception"
    )
    assert failure["status"] == "UNHANDLED_EXCEPTION"
    assert failure["details"]["error_type"] == "RuntimeError"
    assert failure["details"]["thread_name"] == "validation-worker"
    assert rows[-1]["status"] == "FAILURE"

def test_validation_output_is_session_scoped_and_rejects_escape(tmp_path):
    output = tmp_path / "manual-validation.jsonl"

    assert validation_output_directory() is None
    assert validation_output_path("sprite.png") is None

    start_validation_session(output)
    try:
        first_root = validation_output_directory()
        sprite = validation_output_path("sprites/selected.png")
        atlas = validation_output_path("atlas", directory=True)
        assert first_root is not None and first_root.is_dir()
        assert sprite is not None and sprite.parent.is_dir()
        assert atlas is not None and atlas.is_dir()
        assert first_root in sprite.parents
        assert first_root in atlas.parents or first_root == atlas
        with pytest.raises(ValueError, match="relative sandbox path"):
            validation_output_path("../escape.json")
    finally:
        stop_validation_session(exit_code=0)

    start_validation_session(output)
    try:
        second_root = validation_output_directory()
        assert second_root is not None
        assert second_root != first_root
    finally:
        stop_validation_session(exit_code=0)


def test_exception_recording_outside_except_has_real_exception_text(tmp_path):
    output = tmp_path / "exception.jsonl"
    start_validation_session(output)
    try:
        record_validation_exception("controlled.failure", ValueError("boom"))
    finally:
        stop_validation_session(exit_code=0)

    row = next(
        item for item in _read_jsonl(output) if item["event"] == "controlled.failure"
    )
    assert row["status"] == "FAILURE"
    assert row["details"]["error_type"] == "ValueError"
    assert "ValueError: boom" in row["details"]["traceback"]
    assert "NoneType: None" not in row["details"]["traceback"]


def test_file_evidence_and_object_token_do_not_expose_identifier(tmp_path):
    target = tmp_path / "result.glb"
    target.write_bytes(b"glTF" + (2).to_bytes(4, "little") + b"data")
    evidence = file_evidence(target)
    assert evidence == {"exists": True, "size": 12, "suffix": ".glb"}

    first = object_token("real-object-id")
    second = object_token("real-object-id")
    other = object_token("other-object-id")
    assert first and len(first) == 12
    assert first == second
    assert first != other
    assert "real-object-id" not in first
