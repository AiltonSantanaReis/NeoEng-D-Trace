from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import threading
import time
from typing import Any


def _driver() -> ctypes.CDLL:
    return ctypes.CDLL("libcuda.so.1")


def _configure(lib: ctypes.CDLL) -> None:
    integer = ctypes.c_int
    unsigned = ctypes.c_uint
    pointer = ctypes.c_void_p
    device_pointer = ctypes.c_uint64
    size = ctypes.c_size_t
    lib.cuInit.argtypes = [unsigned]
    lib.cuInit.restype = integer
    lib.cuDeviceGetCount.argtypes = [ctypes.POINTER(integer)]
    lib.cuDeviceGetCount.restype = integer
    lib.cuDeviceGet.argtypes = [ctypes.POINTER(integer), integer]
    lib.cuDeviceGet.restype = integer
    lib.cuDeviceGetName.argtypes = [ctypes.c_char_p, integer, integer]
    lib.cuDeviceGetName.restype = integer
    lib.cuCtxCreate_v2.argtypes = [ctypes.POINTER(pointer), unsigned, integer]
    lib.cuCtxCreate_v2.restype = integer
    lib.cuCtxSynchronize.argtypes = []
    lib.cuCtxSynchronize.restype = integer
    lib.cuMemAlloc_v2.argtypes = [ctypes.POINTER(device_pointer), size]
    lib.cuMemAlloc_v2.restype = integer
    lib.cuMemsetD8_v2.argtypes = [device_pointer, ctypes.c_ubyte, size]
    lib.cuMemsetD8_v2.restype = integer
    lib.cuMemFree_v2.argtypes = [device_pointer]
    lib.cuMemFree_v2.restype = integer
    lib.cuCtxDestroy_v2.argtypes = [pointer]
    lib.cuCtxDestroy_v2.restype = integer


def _sample_nvidia_smi() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=timestamp,name,driver_version,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"error": type(exc).__name__, "detail": str(exc)}
    if completed.returncode != 0:
        return {
            "error": "nvidia-smi-exit",
            "returncode": completed.returncode,
            "stderr": completed.stderr.strip()[:300],
        }
    line = next((line.strip() for line in completed.stdout.splitlines() if line.strip()), "")
    values = [part.strip() for part in line.split(",")]
    fields = (
        "timestamp",
        "name",
        "driver_version",
        "gpu_utilization_percent",
        "memory_utilization_percent",
        "memory_used_mib",
        "memory_total_mib",
        "power_draw_w",
    )
    if len(values) != len(fields):
        return {"error": "nvidia-smi-shape", "raw": line[:500]}
    result: dict[str, Any] = dict(zip(fields, values))
    for field in fields[3:]:
        try:
            result[field] = float(str(result[field]).replace("N/A", "nan"))
        except ValueError:
            result[field] = None
    return result


def main() -> int:
    seconds = float(os.environ.get("GPU_SOAK_SECONDS", "20"))
    allocation_mib = int(os.environ.get("GPU_SOAK_ALLOCATION_MIB", "256"))
    sample_period = 0.5
    lib = _driver()
    _configure(lib)
    result: dict[str, Any] = {
        "schema_version": 1,
        "environment": "docker-linux-controlled",
        "networking": "disabled",
        "runtime": {
            "python": "3.11",
            "cuda_driver_library": "libcuda.so.1",
            "nvidia_smi": shutil.which("nvidia-smi") is not None,
        },
        "workload": {
            "duration_target_seconds": seconds,
            "allocation_mib": allocation_mib,
            "operation": "repeated synchronous cuMemsetD8 on a CUDA allocation",
        },
        "driver": {},
        "telemetry": {"samples": [], "errors": []},
        "limitations": [
            "This qualifies controlled GPU transport and driver workload only.",
            "The QGraphicsView editor soak remains offscreen/software and is not a GPU-renderer measurement.",
        ],
    }
    rc = int(lib.cuInit(0))
    result["driver"]["cuInit"] = rc
    count = ctypes.c_int(-1)
    result["driver"]["cuDeviceGetCount"] = int(lib.cuDeviceGetCount(ctypes.byref(count)))
    result["driver"]["device_count"] = count.value
    if rc != 0 or result["driver"]["cuDeviceGetCount"] != 0 or count.value < 1:
        result["status"] = "BLOCKED"
        result["blocked_reason"] = "CUDA device initialization did not expose a device"
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    device = ctypes.c_int(-1)
    get_device_rc = int(lib.cuDeviceGet(ctypes.byref(device), 0))
    name = ctypes.create_string_buffer(256)
    get_name_rc = int(lib.cuDeviceGetName(name, 256, device))
    result["driver"]["cuDeviceGet"] = get_device_rc
    result["driver"]["cuDeviceGetName"] = get_name_rc
    result["driver"]["device_name"] = name.value.decode("utf-8", errors="replace")

    context = ctypes.c_void_p()
    allocation = ctypes.c_uint64(0)
    errors: list[str] = []
    stop = threading.Event()
    samples: list[dict[str, Any]] = []

    def monitor() -> None:
        while not stop.is_set():
            sample = _sample_nvidia_smi()
            if "error" in sample:
                result["telemetry"]["errors"].append(sample)
            else:
                samples.append(sample)
            stop.wait(sample_period)

    context_rc = int(lib.cuCtxCreate_v2(ctypes.byref(context), 0, device))
    result["driver"]["cuCtxCreate"] = context_rc
    if context_rc != 0:
        result["status"] = "BLOCKED"
        result["blocked_reason"] = "CUDA context creation failed"
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    try:
        allocation_bytes = allocation_mib * 1024 * 1024
        allocation_rc = int(lib.cuMemAlloc_v2(ctypes.byref(allocation), allocation_bytes))
        result["driver"]["cuMemAlloc"] = allocation_rc
        if allocation_rc != 0:
            result["status"] = "BLOCKED"
            result["blocked_reason"] = "CUDA allocation failed"
        else:
            thread = threading.Thread(target=monitor, name="nvidia-smi-monitor", daemon=True)
            thread.start()
            start = time.perf_counter()
            deadline = start + seconds
            iterations = 0
            while time.perf_counter() < deadline:
                memset_rc = int(lib.cuMemsetD8_v2(allocation, iterations % 251, allocation_bytes))
                if memset_rc != 0:
                    errors.append(f"cuMemsetD8={memset_rc}")
                    break
                sync_rc = int(lib.cuCtxSynchronize())
                if sync_rc != 0:
                    errors.append(f"cuCtxSynchronize={sync_rc}")
                    break
                iterations += 1
            elapsed = time.perf_counter() - start
            stop.set()
            thread.join(timeout=5)
            result["workload"]["elapsed_seconds"] = round(elapsed, 3)
            result["workload"]["iterations"] = iterations
            result["workload"]["operations_per_second"] = round(iterations / elapsed, 2) if elapsed else 0.0
            result["telemetry"]["samples"] = samples
            result["telemetry"]["sample_count"] = len(samples)
            result["telemetry"]["errors"] = result["telemetry"]["errors"]
            result["workload"]["errors"] = errors
            result["workload"]["sample_period_seconds"] = sample_period
            result["status"] = "PASS" if iterations > 0 and not errors and samples else "BLOCKED"
            if result["status"] != "PASS":
                result["blocked_reason"] = "GPU workload or telemetry did not produce a complete sample"
    finally:
        if allocation.value:
            result["driver"]["cuMemFree"] = int(lib.cuMemFree_v2(allocation))
        result["driver"]["cuCtxDestroy"] = int(lib.cuCtxDestroy_v2(context))

    numeric_utilization = [
        sample["gpu_utilization_percent"]
        for sample in samples
        if isinstance(sample.get("gpu_utilization_percent"), (int, float))
    ]
    numeric_memory = [
        sample["memory_used_mib"]
        for sample in samples
        if isinstance(sample.get("memory_used_mib"), (int, float))
    ]
    result["telemetry"]["max_gpu_utilization_percent"] = max(numeric_utilization, default=None)
    result["telemetry"]["max_memory_used_mib"] = max(numeric_memory, default=None)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
