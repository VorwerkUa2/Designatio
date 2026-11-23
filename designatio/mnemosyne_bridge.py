from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import shutil
import sys


def build_mnemosyne_mcp_config(project_dir: str | Path) -> dict[str, Any]:
    project = Path(project_dir).resolve()
    designatio_dir = Path(__file__).resolve().parents[1]
    python = sys.executable
    config = {
        "mcpServers": {
            "designatio": {
                "command": python,
                "args": ["-m", "designatio.mcp.server"],
                "cwd": str(designatio_dir),
            }
        }
    }
    path = project / "designatio-mcp.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"config": str(path.resolve()), "server": "designatio", "mcpConfig": config}


def create_mnemosyne_preview_manifest(preview_dir: str | Path, project: dict[str, Any]) -> dict[str, Any]:
    preview = Path(preview_dir).resolve()
    candidates = [preview / "dist" / "index.html", preview / "index.html"]
    entry = next((candidate for candidate in candidates if candidate.is_file()), None)
    if entry is None:
        raise FileNotFoundError(f"No preview entry found under {preview}")
    manifest = {
        "schema": "1",
        "host": "Mnemosyne",
        "preview": {
            "entry": str(entry),
            "directory": str(preview),
            "url": f"file:///{entry.as_posix().lstrip('/')}",
        },
        "project": {
            "name": project.get("name", "Untitled"),
            "platform": project.get("platform", "web"),
            "stack": project.get("stack", "html"),
            "tokens": project.get("tokens", {}),
        },
        "breakpoints": [1440, 1024, 768, 390],
    }
    path = preview / "mnemosyne-preview.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"manifest": str(path.resolve()), "preview": manifest["preview"]}
