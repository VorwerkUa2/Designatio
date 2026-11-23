import json
from pathlib import Path

from designatio.contracts import create_project, load_project, save_project
from designatio.mockup import analyze_mockup
from designatio.renderers import render_html, render_react
from designatio.router import route_task
from designatio.validation import check_accessibility, check_responsive
from designatio.visual import compare_images
from designatio.mockup import infer_components


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


def test_mockup_layout_has_machine_readable_result(tmp_path: Path) -> None:
    from PIL import Image

    mockup = tmp_path / "layout.png"
    Image.new("RGB", (1440, 900), "#F5F7FB").save(mockup)

    result = analyze_mockup(mockup)

    assert "detected" in result
    assert "visionAvailable" in result["detected"]
    assert isinstance(result["detected"]["zones"], list)


def test_react_renderer(tmp_path: Path) -> None:
    project = create_project("CRM Dashboard", "web", "react")
    project["components"] = [
        {"type": "header", "title": "CRM Dashboard", "description": "Overview"},
        {"type": "card", "title": "Users", "description": "1,200"},
    ]

    rendered = render_react(project, tmp_path)

    app = (tmp_path / "src" / "App.jsx").read_text(encoding="utf-8")
    css = (tmp_path / "src" / "App.css").read_text(encoding="utf-8")
    assert "CRM Dashboard" in app
    assert "Users" in app
    assert "@media (max-width: 768px)" in css
    assert rendered["preview"]["breakpoints"] == [1440, 1024, 768, 390]


def test_infer_components_uses_header_and_card_hints() -> None:
    analysis = {
        "source": {"height": 900},
        "detected": {
            "text": {
                "items": [
                    {"text": "CRM", "confidence": 96.0, "box": {"x": 100, "y": 60, "width": 40, "height": 20}},
                    {"text": "Dashboard", "confidence": 96.0, "box": {"x": 150, "y": 60, "width": 90, "height": 20}},
                ],
            },
            "zones": [
                {"type": "card", "box": {"x": 100, "y": 200, "width": 400, "height": 200}, "area": 80000},
            ],
        },
    }

    components = infer_components(analysis, "Test")

    assert components[0]["type"] == "header"
    assert "CRM" in components[0]["title"]
    assert any(component["type"] == "card" for component in components)
