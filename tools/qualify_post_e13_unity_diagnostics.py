"""Classify preserved Unity logs without launching Unity or stopping processes.

This tool is deliberately read-only. It is a controlled diagnostic harness for
licensing and shutdown-related messages already captured by an approved run or
provided as a simulation fixture. It must never be used as evidence that a
native Unity environment is clean.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

MARKERS: dict[str, str] = {
    "licensing_code_10": r"Code 10 while verifying Licensing Client signature",
    "licensing_failed_validation": r"LicensingClient has failed validation",
    "access_token_unavailable": r"Access token is unavailable",
    "entitlement_resolved": r"Successfully resolved entitlement details",
    "unity_personal_entitlement": r"Product:\s*Unity Personal",
    "curl_callback_aborted": r"Curl error 42:\s*Callback aborted",
    "network_timeout": r"(?:timeout|timed out|public-cdn\.cloud\.unity3d\.com)",
    "abort_threads": r"abort_threads:\s*Failed aborting id",
    "memory_leaks_event": r'"type":"MemoryLeaks"',
    "no_leaked_weakptrs": r"Found no leaked weakptrs",
    "exit_code_0": r"ExitCode:\s*0",
    "exit_code_4": r"ExitCode:\s*4",
    "positive_runtime_marker": r"TILEMAP_RUNTIME_UNITY=SUCCESS",
    "negative_runtime_marker": r"TILEMAP_RUNTIME_UNITY_DRIFT=REJECTED",
}


def _count(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def classify_log(text: str, kind: str, source_name: str) -> dict[str, Any]:
    """Return a sanitised classification for one preserved or simulated log."""

    counts = {name: _count(text, pattern) for name, pattern in MARKERS.items()}
    if kind == "positive":
        functional_marker = "positive_runtime_marker"
    elif kind == "negative":
        functional_marker = "negative_runtime_marker"
    else:
        raise ValueError(f"unsupported log kind: {kind}")

    functional_status = (
        "PASS"
        if counts[functional_marker] > 0 and counts["exit_code_0"] > 0
        else "FAIL"
    )
    known_environment_signals = sum(
        counts[name]
        for name in (
            "licensing_code_10",
            "licensing_failed_validation",
            "access_token_unavailable",
            "curl_callback_aborted",
            "network_timeout",
            "abort_threads",
            "memory_leaks_event",
        )
    )
    clean_environment_status = (
        "PENDING_EVIDENCE" if known_environment_signals else "PASS"
    )
    shutdown_status = (
        "PENDING_EVIDENCE"
        if counts["abort_threads"] or counts["memory_leaks_event"]
        else "PASS"
    )

    return {
        "source_name": source_name,
        "kind": kind,
        "functional_status": functional_status,
        "native_clean_environment_status": clean_environment_status,
        "shutdown_diagnostic_status": shutdown_status,
        "internal_subprocess_exit_code_4_observed": bool(counts["exit_code_4"]),
        "marker_counts": counts,
        "interpretation": {
            "functional": (
                "The expected positive/negative runtime marker and process "
                "ExitCode 0 were both observed."
            ),
            "licensing": (
                "Observed licensing signals are preserved; this classifier "
                "does not diagnose or suppress their cause."
            ),
            "shutdown": (
                "abort_threads and MemoryLeaks records are observations, not "
                "a clean shutdown or soak verdict."
            ),
        },
    }


def classify_files(positive: Path, negative: Path) -> dict[str, Any]:
    """Classify two logs and keep the native-execution boundary explicit."""

    positive_result = classify_log(
        positive.read_text(encoding="utf-8", errors="replace"),
        "positive",
        positive.name,
    )
    negative_result = classify_log(
        negative.read_text(encoding="utf-8", errors="replace"),
        "negative",
        negative.name,
    )
    functional_status = (
        "PASS"
        if positive_result["functional_status"] == "PASS"
        and negative_result["functional_status"] == "PASS"
        else "FAIL"
    )
    return {
        "format_id": "neoeng-d-trace-unity-diagnostics-classification",
        "schema_version": 1,
        "status": functional_status,
        "classification": "CONTROLLED_LOG_CLASSIFICATION_ONLY",
        "native_unity_reexecuted": False,
        "native_shutdown_or_process_termination_requested": False,
        "positive": positive_result,
        "negative": negative_result,
        "limitations": [
            "The classifier reads logs and never launches Unity or executes -quit.",
            (
                "PENDING_EVIDENCE remains correct for a clean "
                "licensing/network/shutdown environment."
            ),
            (
                "A MemoryLeaks event and abort_threads message are retained "
                "and are not converted into PASS."
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positive", type=Path, required=True)
    parser.add_argument("--negative", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = classify_files(args.positive, args.negative)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
