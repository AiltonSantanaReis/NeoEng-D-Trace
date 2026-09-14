from tools.validate_continuity_registry import validate_registry


def test_current_continuity_registry_is_internally_consistent():
    registry = validate_registry()
    assert registry["active_work"]["stage"] == "POST_E13"
    assert registry["active_work"]["closed_stage"] == "E13"
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
    assert (
        registry["stage_status"]["E04"]
        == "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert (
        registry["stage_status"]["E05"]
        == "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E06"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert (
        registry["stage_status"]["E07"]
        == "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E08"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E09"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E10"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E11"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E12"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )
    assert registry["stage_status"]["E13"] == (
        "TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING"
    )


def test_symlink_results_remain_separate():
    registry = validate_registry()
    symlink = registry["gates"]["symlink"]
    assert symlink["sandbox_status"] == "PASS_SANDBOX_DIAGNOSTIC_ONLY"
    assert symlink["local_suite_status"] == "SKIP_CONTROLLED_ONLY"
    assert symlink["current_definitive_requalification"]["status"] == "PASS"
    assert symlink["current_definitive_requalification"]["skipped"] == 0


def test_human_review_approval_is_registered_after_final_audit():
    registry = validate_registry()
    visual = registry["gates"]["visual"]
    assert visual["native_human_status"] == "PASS"
    assert visual["human_review_policy"] == "APPROVED_BY_OWNER"
    assert visual["human_review_required_before_close"] is False
    assert visual["human_review_decision"].endswith(
        "DECISAO_REVISAO_HUMANA_APROVADA_POS_E13_20260913.md"
    )
