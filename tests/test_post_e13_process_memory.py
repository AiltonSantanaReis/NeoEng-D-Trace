import platform
from pathlib import Path

from scripts.calibrate_p2d_05 import _process_memory


def test_process_memory_preserves_cross_platform_contract():
    result = _process_memory()

    assert set(result) == {"working_set_bytes", "private_bytes"}
    assert all(value is None or value >= 0 for value in result.values())
    if platform.system() == "Linux" and Path("/proc/self/smaps_rollup").is_file():
        assert result["working_set_bytes"] is not None
        assert result["private_bytes"] is not None
