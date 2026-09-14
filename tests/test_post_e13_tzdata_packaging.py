from zoneinfo import ZoneInfo


def test_runtime_has_iana_timezone_data_for_portable_windows_support():
    """The declared tzdata dependency must make ZoneInfo usable on Windows."""

    assert ZoneInfo("UTC").key == "UTC"
