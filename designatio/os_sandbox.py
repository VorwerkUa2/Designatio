from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import shutil
import subprocess


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
