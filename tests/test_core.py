import json
from pathlib import Path

from designatio.contracts import create_project, load_project, save_project
from designatio.mockup import analyze_mockup
from designatio.renderers import render_html
from designatio.router import route_task
from designatio.validation import check_accessibility, check_responsive
from designatio.visual import compare_images


def test_project_roundtrip(tmp_path: Path) -> None:
    project = create_project("CRM", "web", "html")
    path = save_project(project, tmp_path / "project.json")

    loaded = load_project(path)

    assert loaded["name"] == "CRM"
    assert loaded["schemaVersion"] == "1"
    assert loaded["tokens"]["colors"]["primary"] == "#4F46E5"


def test_router_matches_mockup_and_accessibility() -> None:
    result = route_task("Improve this mockup screenshot for mobile with WCAG accessibility")

    assert "mockup-to-code" in result["profiles"]
    assert "ui-mobile" in result["profiles"]
    assert "accessibility" in result["profiles"]


def test_png_analysis(tmp_path: Path) -> None:
    mockup = tmp_path / "mockup.png"
    mockup.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + b"\x00\x00\x05\x00"
        + b"\x00\x00\x02\xd0"
        + b"\x00" * 13
    )

    result = analyze_mockup(mockup)

    assert result["source"]["width"] == 1280
    assert result["source"]["height"] == 720
    assert "nextActions" in result


def test_html_renderer(tmp_path: Path) -> None:
    project = create_project("Test app")
    project["components"] = [
        {"type": "header", "title": "Dashboard", "description": "Overview"},
        {"type": "card", "title": "Users", "description": "1,200"},
    ]

    rendered = render_html(project, tmp_path)

    index = tmp_path / "index.html"
    assert index.is_file()
    assert "Dashboard" in index.read_text(encoding="utf-8")
    assert rendered["preview"]["breakpoints"] == [1440, 1024, 768, 390]


def test_validation_reports(tmp_path: Path) -> None:
    project = create_project("Test app")
    project["components"] = [{"type": "card", "title": "Test"}]

    accessibility = check_accessibility(project)
    responsive = check_responsive(project)

    assert accessibility["passed"] is True
    assert responsive["passed"] is True


def test_visual_diff(tmp_path: Path) -> None:
    from PIL import Image

    reference = tmp_path / "reference.png"
    rendered = tmp_path / "rendered.png"
    Image.new("RGB", (20, 10), "#FFFFFF").save(reference)
    Image.new("RGB", (20, 10), "#000000").save(rendered)

    report = compare_images(reference, rendered, tmp_path / "comparison")

    assert report["differentPixels"] == 200
    assert report["differenceRatio"] == 1.0
    assert (tmp_path / "comparison" / "diff.png").is_file()
