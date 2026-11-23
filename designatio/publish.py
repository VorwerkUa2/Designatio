from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import subprocess


def git_status(repo: str | Path) -> dict[str, Any]:
    repo_path = Path(repo)
    if not (repo_path / ".git").is_dir():
        raise FileNotFoundError(f"Not a Git repository: {repo_path}")
    result = subprocess.run(
        ["git", "-C", str(repo_path), "--no-pager", "status", "--short", "--branch"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {"passed": result.returncode == 0, "output": result.stdout, "error": result.stderr}


def create_commit(repo: str | Path, message: str, files: list[str] | None = None) -> dict[str, Any]:
    repo_path = Path(repo)
    if not (repo_path / ".git").is_dir():
        raise FileNotFoundError(f"Not a Git repository: {repo_path}")
    if files:
        add = subprocess.run(["git", "-C", str(repo_path), "add", *files], capture_output=True, text=True, check=False)
        if add.returncode != 0:
            return {"passed": False, "stage": "add", "error": add.stderr}
    commit = subprocess.run(
        ["git", "-C", str(repo_path), "-c", "core.autocrlf=true", "commit", "-m", message],
        capture_output=True,
        text=True,
        check=False,
    )
    return {"passed": commit.returncode == 0, "output": commit.stdout, "error": commit.stderr}


def create_mnemosyne_handoff(project: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    handoff = {
        "schema": "1",
        "host": "Mnemosyne",
        "project": project,
        "instructions": [
            "Open the project in the active workspace.",
            "Preserve the Designatio project JSON as source of truth.",
            "Use Plan mode for analysis and Turbo mode only for approved file edits.",
            "Capture screenshots at 1440, 1024, 768 and 390 px.",
            "Run accessibility and responsive validation before commit.",
        ],
    }
    path = output / "mnemosyne-handoff.json"
    path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"handoff": str(path.resolve()), "schema": "1", "host": "Mnemosyne"}


def push_repository(repo: str | Path, remote: str = "origin", branch: str = "main") -> dict[str, Any]:
    repo_path = Path(repo)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "push", "-u", remote, branch],
        capture_output=True,
        text=True,
        check=False,
    )
    return {"passed": result.returncode == 0, "output": result.stdout, "error": result.stderr}
