from tools.validate_continuity_registry import validate_registry


def test_current_continuity_registry_is_internally_consistent():
    registry = validate_registry()
    assert registry["active_work"]["stage"] == "E00"
    assert registry["stage_status"]["E01"] == "NOT_STARTED"


def test_symlink_results_remain_separate():
    registry = validate_registry()
    symlink = registry["gates"]["symlink"]
    assert symlink["sandbox_status"] == "PASS_SANDBOX_DIAGNOSTIC_ONLY"
    assert symlink["local_suite_status"] == "SKIP_PRIVILEGE_LIMITATION"
