import json
from pathlib import Path

from designatio.contracts import create_project, load_project, save_project
from designatio.mockup import analyze_mockup
from designatio.renderers import render_html, render_react
from designatio.router import route_task
from designatio.validation import check_accessibility, check_responsive
from designatio.visual import compare_images
from designatio.mockup import infer_components
from designatio.catalog import get_language_catalog, resolve_language, find_graphics_libraries
from designatio.native_renderers import render_native
from designatio.figma import import_figma_json


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


def test_language_catalog_is_broad_and_resolvable() -> None:
    catalog = get_language_catalog()

    assert len(catalog) >= 25
    assert resolve_language("c#") == "csharp"
    assert resolve_language("tsx") == "typescript"
    assert "Skia" in catalog["dart"]["graphics"]
    assert "Dear ImGui" in catalog["cpp"]["graphics"]


def test_stack_resolution_matches_language() -> None:
    matches = find_graphics_libraries("Create a native SwiftUI app with Swift")

    assert matches
    assert matches[0]["language"] == "swift"
    assert "Metal" in matches[0]["graphics"]


def test_native_renderers_generate_source(tmp_path: Path) -> None:
    project = create_project("Native app")
    project["components"] = [
        {"type": "header", "title": "Dashboard", "description": "Overview"},
        {"type": "card", "title": "Users", "description": "1,200"},
    ]

    flutter = render_native(project, "flutter", tmp_path / "flutter")
    swift = render_native(project, "swiftui", tmp_path / "swiftui")
    compose = render_native(project, "compose", tmp_path / "compose")
    egui = render_native(project, "egui", tmp_path / "egui")

    assert (tmp_path / "flutter" / "lib" / "main.dart").is_file()
    assert (tmp_path / "swiftui" / "ContentView.swift").is_file()
    assert "VStack" in (tmp_path / "swiftui" / "ContentView.swift").read_text(encoding="utf-8")
    assert "Text(" in (tmp_path / "compose" / "DesignatioScreen.kt").read_text(encoding="utf-8")
    assert "CentralPanel" in (tmp_path / "egui" / "main.rs").read_text(encoding="utf-8")
    assert flutter["renderer"] == "flutter"


def test_figma_json_import(tmp_path: Path) -> None:
    figma = tmp_path / "screen.json"
    figma.write_text(json.dumps({
        "name": "Dashboard",
        "document": {
            "name": "Root",
            "type": "CANVAS",
            "children": [{
                "name": "Desktop",
                "type": "FRAME",
                "children": [{"name": "Title", "type": "TEXT", "characters": "Sales dashboard"}],
            }],
        },
    }), encoding="utf-8")

    result = import_figma_json(figma, tmp_path / "project")

    assert result["components"] >= 1
    assert result["textNodes"] == 1
    assert (tmp_path / "project" / "project.json").is_file()
