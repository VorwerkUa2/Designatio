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


def github_status(repo: str | Path) -> dict[str, Any]:
    repo_path = Path(repo)
    remotes = subprocess.run(
        ["git", "-C", str(repo_path), "remote", "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    gh = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner,url,defaultBranchRef,visibility"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "passed": gh.returncode == 0,
        "repo": gh.stdout.strip(),
        "remotes": remotes.stdout,
        "error": gh.stderr,
    }


def github_create_release(repo: str | Path, tag: str, title: str, notes: str = "") -> dict[str, Any]:
    repo_path = Path(repo)
    args = ["gh", "release", "create", tag, "--title", title]
    if notes:
        args.extend(["--notes", notes])
    result = subprocess.run(args, cwd=repo_path, capture_output=True, text=True, check=False)
    return {"passed": result.returncode == 0, "output": result.stdout, "error": result.stderr}


def github_create_pr(repo: str | Path, title: str, body: str = "", base: str = "", head: str = "") -> dict[str, Any]:
    repo_path = Path(repo)
    args = ["gh", "pr", "create", "--title", title]
    if body:
        args.extend(["--body", body])
    if base:
        args.extend(["--base", base])
    if head:
        args.extend(["--head", head])
    result = subprocess.run(args, cwd=repo_path, capture_output=True, text=True, check=False)
    return {"passed": result.returncode == 0, "output": result.stdout, "error": result.stderr}


def github_create_issue(repo: str | Path, title: str, body: str = "", labels: list[str] | None = None) -> dict[str, Any]:
    repo_path = Path(repo)
    args = ["gh", "issue", "create", "--title", title]
    if body:
        args.extend(["--body", body])
    for label in labels or []:
        args.extend(["--label", label])
    result = subprocess.run(args, cwd=repo_path, capture_output=True, text=True, check=False)
    return {"passed": result.returncode == 0, "output": result.stdout, "error": result.stderr}


def mnemosyne_launch_preview(preview_dir: str | Path) -> dict[str, Any]:
    preview = Path(preview_dir)
    if not preview.exists():
        raise FileNotFoundError(f"Preview directory not found: {preview}")
    candidates = [preview / "dist" / "index.html", preview / "index.html"]
    target = next((candidate for candidate in candidates if candidate.is_file()), None)
    if target is None:
        raise FileNotFoundError(f"No preview index found in: {preview}")
    handoff = create_mnemosyne_handoff({"preview": str(target.resolve())}, preview / "handoff")
    return {
        "passed": True,
        "host": "Mnemosyne",
        "preview": str(target.resolve()),
        "handoff": handoff["handoff"],
    }
