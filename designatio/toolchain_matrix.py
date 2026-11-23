from __future__ import annotations

from typing import Any
import shutil
import os


TOOLCHAINS = {
    "flutter": ("flutter", "Flutter SDK"),
    "dart": ("dart", "Dart SDK"),
    "gradle": ("gradle", "Gradle"),
    "java": ("java", "Java/JDK"),
    "swift": ("swift", "Swift toolchain"),
    "xcode": ("xcodebuild", "Xcode"),
    "cargo": ("cargo", "Rust Cargo"),
    "rustc": ("rustc", "Rust compiler"),
    "node": ("node", "Node.js"),
    "npm": ("npm", "npm package manager"),
    "dotnet": ("dotnet", ".NET SDK"),
    "glslang": ("glslangValidator", "GLSL shader validator"),
    "dxc": ("dxc", "DirectX shader compiler"),
    "docker": ("docker", "Docker"),
    "podman": ("podman", "Podman"),
}


def inspect_toolchain_matrix() -> dict[str, Any]:
    entries = []
    available = 0
    for target, (executable, label) in TOOLCHAINS.items():
        path = shutil.which(executable)
        if path:
            available += 1
        entries.append({
            "target": target,
            "label": label,
            "executable": executable,
            "status": "available" if path else "missing",
            "path": path,
        })
    return {
        "platform": os.name,
        "available": available,
        "missing": len(entries) - available,
        "toolchains": entries,
    }
