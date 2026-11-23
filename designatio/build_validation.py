from __future__ import annotations

from pathlib import Path
from typing import Any
import shutil
import subprocess
import os

from .platform import npm_command, python_executable


def validate_source(target: str, source_dir: str | Path) -> dict[str, Any]:
    normalized = target.lower().strip()
    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    if normalized in {"python", "py"}:
        command = [python_executable(), "-m", "compileall", "-q", str(source)]
        runner = command
    elif normalized in {"react", "html", "vite"}:
        if not shutil.which("npm"):
            return {"target": normalized, "passed": False, "status": "toolchain-unavailable", "error": "npm not found"}
        package = source / "package.json"
        if not package.is_file():
            return {"target": normalized, "passed": False, "status": "invalid-output", "error": "package.json not found"}
        runner = npm_command("run", "build")
    elif normalized in {"rust", "egui"}:
        if not shutil.which("cargo"):
            return {"target": normalized, "passed": False, "status": "toolchain-unavailable", "error": "cargo not found"}
        if not (source / "Cargo.toml").is_file():
            return {"target": normalized, "passed": False, "status": "invalid-output", "error": "Cargo.toml not found"}
        runner = ["cargo", "check"]
    elif normalized in {"flutter", "dart"}:
        executable = shutil.which("flutter")
        if not executable:
            return {"target": normalized, "passed": False, "status": "toolchain-unavailable", "error": "flutter not found"}
        runner = [executable, "analyze"]
    elif normalized in {"compose", "kotlin", "android"}:
        gradle = source / ("gradlew.bat" if os.name == "nt" else "gradlew")
        if not gradle.is_file():
            return {"target": normalized, "passed": False, "status": "toolchain-unavailable", "error": "Gradle wrapper not found"}
        runner = [str(gradle), "assembleDebug"]
    elif normalized in {"swiftui", "swift", "ios"}:
        if not shutil.which("xcrun"):
            return {"target": normalized, "passed": False, "status": "toolchain-unavailable", "error": "Xcode toolchain is unavailable on this Windows host"}
        runner = ["xcodebuild", "-list"]
    elif normalized in {"tauri"}:
        if not shutil.which("cargo") or not (source / "src-tauri" / "Cargo.toml").is_file():
            return {"target": normalized, "passed": False, "status": "toolchain-unavailable", "error": "cargo or Tauri Rust project not found"}
        runner = ["cargo", "check", "--manifest-path", str(source / "src-tauri" / "Cargo.toml")]
    else:
        return {"target": normalized, "passed": False, "status": "unsupported", "error": f"No validator for {target}"}

    result = subprocess.run(
        runner,
        cwd=source,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    output = (result.stdout + "\n" + result.stderr)[-12000:]
    return {
        "target": normalized,
        "passed": result.returncode == 0,
        "status": "passed" if result.returncode == 0 else "failed",
        "command": runner,
        "output": output,
        "returnCode": result.returncode,
    }
