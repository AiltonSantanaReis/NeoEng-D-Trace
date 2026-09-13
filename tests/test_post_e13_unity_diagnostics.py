from tools.qualify_post_e13_unity_diagnostics import classify_log


def test_positive_log_classification_preserves_functional_and_environment_signals():
    result = classify_log(
        """
        [Licensing::Client] Code 10 while verifying Licensing Client signature
        [Licensing::Module] LicensingClient has failed validation; ignoring
        [Licensing::Module] Error: Access token is unavailable; failed to update
        [Licensing::Client] Successfully resolved entitlement details
        Product: Unity Personal
        TILEMAP_RUNTIME_UNITY=SUCCESS
        ExitCode: 4
        ExitCode: 0
        Curl error 42: Callback aborted
        abort_threads: Failed aborting id: abc
        Found no leaked weakptrs.
        ##utp:{"type":"MemoryLeaks"}
        """,
        "positive",
        "fixture-positive.log",
    )

    assert result["functional_status"] == "PASS"
    assert result["native_clean_environment_status"] == "PENDING_EVIDENCE"
    assert result["shutdown_diagnostic_status"] == "PENDING_EVIDENCE"
    assert result["internal_subprocess_exit_code_4_observed"] is True
    assert result["marker_counts"]["abort_threads"] == 1
    assert result["marker_counts"]["memory_leaks_event"] == 1


def test_negative_log_classification_requires_rejection_marker_and_exit_zero():
    result = classify_log(
        """
        TILEMAP_RUNTIME_UNITY_DRIFT=REJECTED
        ExitCode: 0
        """,
        "negative",
        "fixture-negative.log",
    )

    assert result["functional_status"] == "PASS"
    assert result["native_clean_environment_status"] == "PASS"
    assert result["shutdown_diagnostic_status"] == "PASS"


def test_missing_functional_marker_is_not_masked_by_exit_code():
    result = classify_log("ExitCode: 0", "positive", "incomplete.log")

    assert result["functional_status"] == "FAIL"
