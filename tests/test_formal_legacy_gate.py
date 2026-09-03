from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools.run_formal_legacy_gate import (
    _canonical_sha256,
    load_current_contract,
    validate_current_contract,
)
from tools.run_legacy_tests import load_reconciliation

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_hash_is_independent_of_text_line_endings(tmp_path):
    crlf = tmp_path / "crlf.json"
    lf = tmp_path / "lf.json"
    crlf.write_bytes(b"one\r\ntwo\r\n")
    lf.write_bytes(b"one\ntwo\n")
    assert _canonical_sha256(crlf) == _canonical_sha256(lf)


def test_current_contract_resolves_all_legacy_cases_without_rewriting_history():
    _, contract = load_current_contract(ROOT)
    _, expectations = load_reconciliation(ROOT / "quality/legacy_tests")

    result = validate_current_contract(ROOT, contract, expectations)

    assert len(expectations) == 27
    assert len(result["exact_ids"]) == 15
    assert len(result["observations"]) == 12
    assert len(result["formal_substitute_references"]) == 27
    assert len(result["substitute_references"]) == 4
    assert contract["historical_snapshots"]["manifest"]["path"] == (
        "quality/legacy_tests/manifest.json"
    )
    assert contract["historical_snapshots"]["reconciliation"]["path"] == (
        "quality/legacy_tests/reconciliation.json"
    )


def test_current_contract_rejects_an_unreviewed_case():
    _, contract = load_current_contract(ROOT)
    _, expectations = load_reconciliation(ROOT / "quality/legacy_tests")
    broken = copy.deepcopy(contract)
    broken["current_observations"][0]["id"] = "test_unknown::Test::test_case"

    with pytest.raises(ValueError, match="not a historical expectation"):
        validate_current_contract(ROOT, broken, expectations)


def test_current_contract_rejects_a_changed_replacement_mapping():
    _, contract = load_current_contract(ROOT)
    _, expectations = load_reconciliation(ROOT / "quality/legacy_tests")
    broken = copy.deepcopy(contract)
    broken["current_observations"][0]["replacement_tests"] = [
        "tests/test_missing.py::test_missing"
    ]

    with pytest.raises(ValueError, match="Formal decision substitutes diverge"):
        validate_current_contract(ROOT, broken, expectations)
