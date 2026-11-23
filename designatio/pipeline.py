from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess

from .contracts import create_project, save_project
from .mockup import analyze_mockup
from .renderers import render_react
from .validation import check_accessibility, check_responsive
from .visual import take_screenshots, compare_images


def run_pipeline(
    mockup: str | Path,
    output_dir: str | Path,
    name: str = "Untitled design",
    mode: str = "production-ready",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    project = create_project(name, "web", "react", brief={"goal": "Mockup-to-code", "mode": mode})
    analysis = analyze_mockup(mockup, mode)
    project["components"] = analysis.get("components", [])
    project["assets"].append(analysis["source"])
    project["reports"].append({"type": "mockup-analysis", "data": analysis})

    colors = analysis.get("detected", {}).get("colors", [])
    if colors:
        project["tokens"]["colors"]["surface"] = colors[0]
        project["tokens"]["colors"]["background"] = next(
            (color for color in reversed(colors) if color not in {"#FFFFFF", "#000000"}),
            project["tokens"]["colors"]["background"],
        )

    project_path = output / "project.json"
    save_project(project, project_path)

    rendered = render_react(project, output / "react")
    save_project(rendered, project_path)

    react_dir = output / "react"
    npm_command = ["cmd", "/d", "/c", "npm", "install", "&&", "npm", "run", "build"]
    build = subprocess.run(
        npm_command,
        cwd=react_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if build.returncode != 0:
        project["reports"].append({
            "type": "react-build",
            "passed": False,
            "error": build.stderr[-4000:] or build.stdout[-4000:],
        })
        build_passed = False
        preview_target = react_dir / "index.html"
    else:
        project["reports"].append({
            "type": "react-build",
            "passed": True,
            "stdout": build.stdout[-4000:],
        })
        build_passed = True
        preview_target = react_dir / "dist" / "index.html"

    screenshots = take_screenshots(preview_target, output / "screens")
    accessibility = check_accessibility(project)
    responsive = check_responsive(project)
    project["reports"].append({"type": "accessibility", "data": accessibility})
    project["reports"].append({"type": "responsive", "data": responsive})

    comparisons: dict[str, Any] = {}
    reference = Path(mockup)
    try:
        from PIL import Image
        with Image.open(reference) as reference_image:
            reference_width = reference_image.width
    except Exception:
        reference_width = None
    for width, rendered_path in screenshots["screenshots"].items():
        if reference.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            if reference_width is not None and abs(reference_width - int(width)) > 40:
                comparisons[width] = {
                    "skipped": True,
                    "reason": f"Reference width {reference_width}px does not match breakpoint {width}px",
                }
                continue
            try:
                comparisons[width] = compare_images(
                    reference,
                    rendered_path,
                    output / "comparisons" / width,
                )
            except (OSError, ValueError):
                comparisons[width] = {"skipped": True, "reason": "Incompatible image dimensions or format"}

    project["preview"] = {
        "react": str((react_dir / "src" / "App.jsx").resolve()),
        "screens": screenshots["screenshots"],
        "comparisons": comparisons,
        "breakpoints": [1440, 1024, 768, 390],
    }
    save_project(project, project_path)

    report = {
        "passed": build_passed and accessibility["passed"] and responsive["passed"],
        "project": str(project_path.resolve()),
        "react": str((react_dir / "src" / "App.jsx").resolve()),
        "screenshots": screenshots["screenshots"],
        "accessibility": accessibility,
        "responsive": responsive,
        "comparisons": comparisons,
    }
    return report
