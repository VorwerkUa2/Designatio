from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import shutil
import subprocess
import sys


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
    else:
        command = [sys.executable, "-I", str(entry_path)]
    return {
        "backend": chosen,
        "command": command,
        "payloadEnvironment": "DESIGNATIO_PAYLOAD",
        "payload": payload,
    }
