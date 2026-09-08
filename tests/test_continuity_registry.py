from tools.validate_continuity_registry import validate_registry


def test_current_continuity_registry_is_internally_consistent():
    registry = validate_registry()
    assert registry["active_work"]["stage"] == "E06"
    assert registry["active_work"]["technical_continuation_authorized"] is True
    assert registry["stage_status"]["E00"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E01"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E02"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E03"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E04"] == "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    assert registry["stage_status"]["E05"] == "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    assert registry["stage_status"]["E06"] == "IN_PROGRESS"


def test_symlink_results_remain_separate():
    registry = validate_registry()
    symlink = registry["gates"]["symlink"]
    assert symlink["sandbox_status"] == "PASS_SANDBOX_DIAGNOSTIC_ONLY"
    assert symlink["local_suite_status"] == "SKIP_PRIVILEGE_LIMITATION"


def test_human_review_deferral_remains_pending_until_final_audit():
    registry = validate_registry()
    visual = registry["gates"]["visual"]
    assert visual["native_human_status"] == "PENDING_EVIDENCE"
    assert visual["human_review_policy"] == (
        "DEFERRED_UNTIL_FINAL_AUDIT_BY_USER_AUTHORIZATION"
    )
    assert visual["human_review_required_before_close"] is True
