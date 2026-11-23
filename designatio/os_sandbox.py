from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import shutil
import subprocess
import sys
import json


def detect_os_sandbox() -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if os.name == "nt":
        if shutil.which("docker"):
            candidates.append({"backend": "docker", "status": "available", "isolation": "container"})
        if shutil.which("podman"):
            candidates.append({"backend": "podman", "status": "available", "isolation": "container"})
        if shutil.which("where.exe"):
            candidates.append({"backend": "job-object", "status": "platform-supported", "isolation": "job-and-process"})
    else:
        for executable in ("bwrap", "firejail", "systemd-run", "docker", "podman"):
            found = shutil.which(executable)
            if found:
                candidates.append({"backend": executable, "status": "available", "isolation": "process-or-container"})
    active = next((item for item in candidates if item["status"] == "available"), None)
    return {
        "platform": os.name,
        "activeBackend": active["backend"] if active else None,
        "mode": active["isolation"] if active else "not-configured",
        "candidates": candidates,
    }


def validate_sandbox_backend(backend: str) -> dict[str, Any]:
    normalized = backend.lower().strip()
    executable = {
        "bwrap": "bwrap",
        "firejail": "firejail",
        "systemd": "systemd-run",
        "docker": "docker",
        "podman": "podman",
        "job-object": None,
    }.get(normalized)

    if normalized == "job-object":
        if os.name != "nt":
            return {"backend": normalized, "available": False, "reason": "Windows-only"}
        return {"backend": normalized, "available": True, "reason": "Platform-supported adapter; native implementation required"}
    if not executable:
        return {"backend": normalized, "available": False, "reason": "Unknown backend"}
    path = shutil.which(executable)
    if not path:
        return {"backend": normalized, "available": False, "reason": f"{executable} not found"}
    return {"backend": normalized, "available": True, "path": path}


def run_sandbox_probe(command: list[str], timeout: int = 10) -> dict[str, Any]:
    if not command:
        raise ValueError("Sandbox probe command is required")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "passed": result.returncode == 0,
        "returnCode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def build_sandbox_command(entry: str | Path, payload: dict[str, Any], backend: str | None = None) -> dict[str, Any]:
    entry_path = Path(entry).resolve()
    if not entry_path.is_file():
        raise FileNotFoundError(f"Sandbox entry not found: {entry_path}")
    chosen = (backend or detect_os_sandbox().get("activeBackend") or "bounded")
    if chosen == "bwrap" and shutil.which("bwrap"):
        command = [
            "bwrap",
            "--die-with-parent",
            "--unshare-net",
            "--ro-bind", "/usr", "/usr",
            "--proc", "/proc",
            "--dev", "/dev",
            "--bind", str(entry_path.parent), str(entry_path.parent),
            "--chdir", str(entry_path.parent),
            "python",
            "-I",
            str(entry_path),
        ]
    elif chosen == "firejail" and shutil.which("firejail"):
        command = ["firejail", "--quiet", "--netnone", "--private=" + str(entry_path.parent), sys.executable, "-I", str(entry_path)]
    elif chosen == "docker" and shutil.which("docker"):
        command = [
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{entry_path.parent}:{entry_path.parent}",
            "-w", str(entry_path.parent),
            "python:3.12-slim",
            "python",
            "-I",
            str(entry_path),
        ]
    elif chosen == "podman" and shutil.which("podman"):
        command = [
            "podman", "run", "--rm", "--network", "none",
            "-v", f"{entry_path.parent}:{entry_path.parent}",
            "-w", str(entry_path.parent),
            "python:3.12-slim",
            "python",
            "-I",
            str(entry_path),
        ]
    elif chosen == "job-object" and os.name == "nt":
        command = [sys.executable, "-I", str(entry_path)]
    else:
        command = [sys.executable, "-I", str(entry_path)]
    return {
        "backend": chosen,
        "command": command,
        "payloadEnvironment": "DESIGNATIO_PAYLOAD",
        "payload": payload,
    }


def execute_sandbox_command(command_report: dict[str, Any], timeout: int = 10) -> dict[str, Any]:
    command = command_report.get("command")
    if not isinstance(command, list) or not command:
        raise ValueError("Sandbox command is required")
    if os.name == "nt" and command_report.get("backend") == "job-object":
        return run_windows_job_object(command, command_report.get("payload", {}), timeout)
    environment = dict(os.environ)
    environment["DESIGNATIO_PAYLOAD"] = json.dumps(command_report.get("payload", {}), ensure_ascii=False)
    result = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "passed": result.returncode == 0,
        "backend": command_report.get("backend"),
        "returnCode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def run_windows_job_object(command: list[str], payload: dict[str, Any], timeout: int = 10) -> dict[str, Any]:
    if os.name != "nt":
        return {"passed": False, "backend": "job-object", "status": "unsupported-host"}
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError as error:
        return {"passed": False, "backend": "job-object", "status": "unavailable", "error": str(error)}

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOB_OBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", ctypes.c_ulong),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_ulong),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_ulong),
            ("SchedulingClass", ctypes.c_ulong),
        ]

    class JOB_OBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOB_OBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return {"passed": False, "backend": "job-object", "status": "create-failed", "error": ctypes.get_last_error()}

    limits = JOB_OBJECT_EXTENDED_LIMIT_INFORMATION()
    limits.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    limits.BasicLimitInformation.ActiveProcessLimit = 1
    limits.BasicLimitInformation.LimitFlags |= 0x00000008  # JOB_OBJECT_LIMIT_ACTIVE_PROCESS

    if not kernel32.SetInformationJobObject(
        job,
        9,  # JobObjectExtendedLimitInformation
        ctypes.byref(limits),
        ctypes.sizeof(limits),
    ):
        kernel32.CloseHandle(job)
        return {"passed": False, "backend": "job-object", "status": "configure-failed", "error": ctypes.get_last_error()}

    environment = dict(os.environ)
    environment["DESIGNATIO_PAYLOAD"] = json.dumps(payload, ensure_ascii=False)
    process = subprocess.Popen(
        command,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    process_handle = process._handle
    if not kernel32.AssignProcessToJobObject(job, process_handle):
        process.terminate()
        kernel32.CloseHandle(job)
        return {"passed": False, "backend": "job-object", "status": "assign-failed", "error": ctypes.get_last_error()}

    try:
        stdout, stderr = process.communicate(timeout=timeout)
        passed = process.returncode == 0
    except subprocess.TimeoutExpired:
        kernel32.TerminateJobObject(job, 1)
        stdout, stderr = process.communicate(timeout=5)
        passed = False
    finally:
        kernel32.CloseHandle(job)

    return {
        "passed": passed,
        "backend": "job-object",
        "returnCode": process.returncode,
        "stdout": stdout[-4000:] if stdout else "",
        "stderr": stderr[-4000:] if stderr else "",
    }
