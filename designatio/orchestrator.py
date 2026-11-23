from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import subprocess
import sys

from .contracts import create_project, save_project
from .toolchain_matrix import inspect_toolchain_matrix
from .os_sandbox import detect_os_sandbox
from .build_validation import validate_source
from .renderers import render_react
from .visual import take_screenshots, inspect_preview
from .validation import check_accessibility, check_responsive
from .platform import npm_command
from .preview_host import start_preview_server, stop_preview_server


def run_subprocess(command: list[str], cwd: str | Path | None = None) -> dict[str, Any]:
    if command and command[0] == "npm":
        command = npm_command(*command[1:])
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return {
        "passed": result.returncode == 0,
        "command": command,
        "returnCode": result.returncode,
        "stdout": result.stdout[-8000:],
        "stderr": result.stderr[-8000:],
    }


def doctor() -> dict[str, Any]:
    python = sys.executable
    python_check = run_subprocess([python, "--version"])
    npm = inspect_toolchain_matrix()["toolchains"]
    return {
        "passed": python_check["passed"],
        "python": {"executable": python, "check": python_check},
        "toolchains": npm,
        "sandbox": detect_os_sandbox(),
        "installHint": "Run .\\install.ps1 on Windows or ./install.sh on Linux/macOS.",
    }


def run_all(
    mockup: str | Path | None = None,
    name: str = "Automated Design",
    output_dir: str | Path = "output/automated",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    project = create_project(name, "web", "react")
    project["components"] = [
        {"type": "header", "title": name, "description": "Production-ready responsive interface"},
        {"type": "card", "title": "Primary overview", "description": "Start with real content and component states."},
        {"type": "card", "title": "Supporting details", "description": "Accessible and responsive content."},
    ]
    project_path = save_project(project, output / "project.json")
    reports: dict[str, Any] = {
        "doctor": doctor(),
        "steps": [],
    }

    if mockup:
        mockup_path = Path(mockup)
        if mockup_path.is_file():
            from .mockup import analyze_mockup
            analysis = analyze_mockup(mockup_path)
            project["components"] = analysis.get("components", [])
            project["assets"].append(analysis["source"])
            project["reports"].append({"type": "mockup-analysis", "data": analysis})
            save_project(project, project_path)
            reports["mockup"] = analysis
        else:
            reports["steps"].append({"step": "mockup", "passed": False, "status": "not-found", "path": str(mockup_path)})

    rendered = render_react(project, output / "react")
    save_project(rendered, project_path)
    react_dir = output / "react"
    install = run_subprocess(["npm", "install"], react_dir)
    build = run_subprocess(["npm", "run", "build"], react_dir) if install["passed"] else {"passed": False, "status": "install-failed"}
    reports["steps"].append({"step": "react-install", "result": install})
    reports["steps"].append({"step": "react-build", "result": build})

    preview_target = react_dir / "dist" / "index.html"
    if not preview_target.is_file():
        preview_target = react_dir / "index.html"
    preview_host = None
    if preview_target.is_file():
        preview_host = start_preview_server(react_dir, 4187)
        preview_url = preview_host["url"]
    else:
        preview_url = None
    screenshots = take_screenshots(preview_url, output / "screens") if preview_url else {"screenshots": {}, "breakpoints": []}
    browser_qa = inspect_preview(preview_url) if preview_url else {"passed": False, "status": "preview-not-found"}
    if preview_host:
        stop_preview_server(4187)
    reports["screenshots"] = screenshots
    reports["browserQa"] = browser_qa
    reports["accessibility"] = check_accessibility(project)
    reports["responsive"] = check_responsive(project)

    passed = (
        reports["doctor"]["passed"]
        and build.get("passed", False)
        and browser_qa.get("passed", False)
        and reports["accessibility"]["passed"]
        and reports["responsive"]["passed"]
    )
    report_path = output / "run-report.json"
    report_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "passed": passed,
        "project": str(project_path.resolve()),
        "report": str(report_path.resolve()),
        "results": reports,
    }


def doctor_cli() -> int:
    print(json.dumps(doctor(), ensure_ascii=False, indent=2))
    return 0


def run_cli() -> int:
    parser = argparse.ArgumentParser(prog="designatio-run")
    parser.add_argument("--mockup")
    parser.add_argument("--name", default="Automated Design")
    parser.add_argument("--output", default="output/automated")
    args = parser.parse_args()
    report = run_all(args.mockup, args.name, args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1
