from __future__ import annotations

from pathlib import Path
from typing import Any
import shutil
import subprocess


STAGE_BY_EXTENSION = {
    ".vert": "vertex",
    ".frag": "fragment",
    ".comp": "compute",
    ".geom": "geometry",
    ".tesc": "tess-control",
    ".tese": "tess-evaluation",
    ".glsl": "glsl",
    ".hlsl": "hlsl",
    ".metal": "metal",
}


def validate_shader(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Shader not found: {source}")
    stage = STAGE_BY_EXTENSION.get(source.suffix.lower(), "unknown")
    validator = shutil.which("glslangValidator")
    if source.suffix.lower() in {".vert", ".frag", ".comp", ".geom", ".tesc", ".tese", ".glsl"}:
        if not validator:
            return {
                "passed": False,
                "status": "toolchain-unavailable",
                "stage": stage,
                "shader": str(source.resolve()),
                "error": "glslangValidator not found",
            }
        result = subprocess.run(
            [validator, str(source)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    else:
        return {
            "passed": False,
            "status": "unsupported-host-validator",
            "stage": stage,
            "shader": str(source.resolve()),
            "error": f"No local validator is registered for {source.suffix}",
        }
    output = (result.stdout + "\n" + result.stderr).strip()
    return {
        "passed": result.returncode == 0,
        "status": "passed" if result.returncode == 0 else "failed",
        "stage": stage,
        "shader": str(source.resolve()),
        "output": output[-12000:],
        "returnCode": result.returncode,
    }
