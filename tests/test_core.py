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
from designatio.layout_analysis import merge_reading_order, detect_grid
from designatio.design_mappings import export_tailwind, react_tailwind_source
from designatio.texture_pipeline import generate_seamless
from designatio.plugin_registry import PluginRegistry
from designatio.build_validation import validate_source
from designatio.plugin_bundle import create_plugin_bundle, inspect_plugin_bundle
from designatio.shader_validation import validate_shader
from designatio.plugin_marketplace import create_marketplace_entry
from designatio.engine_manifest import export_engine_manifest
from designatio.publish import create_mnemosyne_handoff
from designatio.native_renderers import render_native
from designatio.visual import compare_regions
from designatio.plugin_registry import PluginRegistry


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


def test_reading_order_and_grid(tmp_path: Path) -> None:
    items = [
        {"text": "Right", "box": {"x": 500, "y": 100, "width": 50, "height": 20}},
        {"text": "Left", "box": {"x": 100, "y": 96, "width": 50, "height": 20}},
        {"text": "Next", "box": {"x": 100, "y": 300, "width": 50, "height": 20}},
    ]
    zones = [{"box": {"x": 100, "y": 100, "width": 200, "height": 100}}, {"box": {"x": 400, "y": 100, "width": 200, "height": 100}}]

    assert merge_reading_order(items) == ["Left Right", "Next"]
    assert detect_grid(zones, 1440, 900)["grid"] in {"12-column", "flow"}


def test_tailwind_and_texture_exports(tmp_path: Path) -> None:
    project = create_project("Tailwind app")
    mapping = export_tailwind(project)
    source = tmp_path / "source.png"
    Image = __import__("PIL.Image", fromlist=["Image"])
    Image.new("RGB", (64, 64), "#4F46E5").save(source)

    texture = generate_seamless(source, tmp_path / "texture")
    react_source = react_tailwind_source(project)

    assert mapping["classNameHints"]["grid"] == "grid grid-cols-1 md:grid-cols-2 gap-6"
    assert "className=\"grid" in react_source
    assert (tmp_path / "texture" / "normal.png").is_file()
    assert texture["maps"] == ["base", "normal", "roughness"]


def test_plugin_registry_sign_verify_and_allowlist(tmp_path: Path) -> None:
    registry = PluginRegistry(tmp_path / "plugins")
    signed = registry.register({"name": "tailwind-export", "version": "1.0.0", "target": "react"}, "test-secret")

    assert registry.verify_manifest(signed, "test-secret") is True
    assert registry.verify_manifest(signed, "wrong-secret") is False

    try:
        registry.register({"name": "shell", "version": "1.0.0", "target": "shell"}, "test-secret")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe plugin target was accepted")


def test_engine_manifest_and_mnemosyne_handoff(tmp_path: Path) -> None:
    project = create_project("3D app")
    project["components"] = [{"type": "card", "title": "Scene", "description": "Main scene"}]

    engine = export_engine_manifest(project, "godot", tmp_path / "engine")
    handoff = create_mnemosyne_handoff(project, tmp_path / "mnemosyne")

    assert engine["engine"] == "godot"
    assert (tmp_path / "engine" / "godot-manifest.json").is_file()
    assert (tmp_path / "mnemosyne" / "mnemosyne-handoff.json").is_file()


def test_tauri_renderer(tmp_path: Path) -> None:
    project = create_project("Tauri app")
    project["components"] = [
        {"type": "header", "title": "Desktop", "description": "Tauri interface"},
        {"type": "card", "title": "Settings", "description": "Preferences"},
    ]

    result = render_native(project, "tauri", tmp_path)

    assert result["renderer"] == "tauri"
    assert (tmp_path / "src-tauri" / "tauri.conf.json").is_file()
    assert (tmp_path / "index.html").is_file()


def test_region_visual_comparison(tmp_path: Path) -> None:
    from PIL import Image

    reference = tmp_path / "reference.png"
    rendered = tmp_path / "rendered.png"
    Image.new("RGB", (100, 100), "#FFFFFF").save(reference)
    Image.new("RGB", (100, 100), "#000000").save(rendered)

    report = compare_regions(
        reference,
        rendered,
        [{"type": "card", "box": {"x": 10, "y": 10, "width": 40, "height": 40}}],
        tmp_path / "regions",
    )

    assert report["regionCount"] == 1
    assert report["regions"][0]["differenceRatio"] == 1.0


def test_ed25519_plugin_sign_verify(tmp_path: Path) -> None:
    registry = PluginRegistry(tmp_path / "plugins")
    keys = registry.generate_ed25519_keypair(
        tmp_path / "plugins" / "private.pem",
        tmp_path / "plugins" / "public.pem",
    )
    manifest = {
        "name": "region-check",
        "version": "1.0.0",
        "target": "security",
        "entry": "entry.json",
        "sandboxRoot": str(tmp_path / "plugins"),
    }
    entry = tmp_path / "plugins" / "entry.json"
    entry.write_text(json.dumps({"mode": "read-only"}), encoding="utf-8")

    signed = registry.sign_ed25519(manifest, keys["private"])

    assert registry.verify_ed25519(signed, keys["public"]) is True
    assert registry.verify_ed25519(dict(signed, target="shell"), keys["public"]) is False
    execution = registry.execute_sandboxed(signed, keys["public"], {"region": "header"})
    assert execution["accepted"] is True
    assert execution["sandbox"] == "allowlist-json"


def test_semantic_component_actions(tmp_path: Path) -> None:
    analysis = {
        "source": {"width": 1440, "height": 900},
        "detected": {
            "text": {
                "items": [
                    {"text": "Dashboard", "confidence": 96, "box": {"x": 100, "y": 60, "width": 120, "height": 30}},
                    {"text": "Create", "confidence": 96, "box": {"x": 1200, "y": 65, "width": 70, "height": 30}},
                    {"text": "Revenue", "confidence": 96, "box": {"x": 120, "y": 300, "width": 100, "height": 30}},
                ],
            },
            "zones": [
                {"type": "card", "box": {"x": 1180, "y": 60, "width": 110, "height": 40}},
                {"type": "card", "box": {"x": 100, "y": 280, "width": 400, "height": 200}},
            ],
        },
    }

    components = infer_components(analysis, "CRM")

    assert components[0]["type"] == "header"
    assert "Create" in components[0]["actions"]


def test_figma_variables_styles_and_auto_layout(tmp_path: Path) -> None:
    figma = tmp_path / "advanced.json"
    figma.write_text(json.dumps({
        "name": "Advanced screen",
        "variables": {"Primary": {"value": "#4F46E5"}},
        "styles": {"Heading": {"fontFamily": "Inter"}},
        "document": {
            "name": "Root",
            "type": "CANVAS",
            "children": [{
                "name": "Card stack",
                "type": "FRAME",
                "layoutMode": "VERTICAL",
                "itemSpacing": 16,
                "paddingTop": 24,
                "paddingRight": 24,
                "paddingBottom": 24,
                "paddingLeft": 24,
                "children": [{"name": "Title", "type": "TEXT", "characters": "Revenue"}],
            }],
        },
    }), encoding="utf-8")

    result = import_figma_json(figma, tmp_path / "advanced")

    assert result["variables"] == 1
    assert result["styles"] == 1
    assert result["autoLayoutFrames"] == 1


def test_plugin_bundle_roundtrip(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / "manifest.json").write_text(json.dumps({
        "name": "bundle-qa",
        "version": "1.0.0",
        "target": "security",
        "entry": "entry.json",
    }), encoding="utf-8")
    (plugin / "entry.json").write_text(json.dumps({"mode": "read-only"}), encoding="utf-8")

    created = create_plugin_bundle(plugin, tmp_path / "bundle.dsgzip")
    inspected = inspect_plugin_bundle(created["bundle"])

    assert inspected["manifest"]["name"] == "bundle-qa"
    assert inspected["files"][0]["sha256"]


def test_build_validation_is_honest(tmp_path: Path) -> None:
    flutter = validate_source("flutter", tmp_path)
    unsupported = validate_source("unknown-target", tmp_path)
    react_missing_package = validate_source("react", tmp_path)

    assert flutter["status"] == "toolchain-unavailable"
    assert unsupported["status"] == "unsupported"
    assert react_missing_package["status"] == "invalid-output"


def test_shader_validation_is_honest(tmp_path: Path) -> None:
    shader = tmp_path / "example.frag"
    shader.write_text("void main() {}", encoding="utf-8")

    report = validate_shader(shader)

    assert report["stage"] == "fragment"
    assert report["status"] in {"toolchain-unavailable", "passed", "failed"}


def test_plugin_marketplace_entry(tmp_path: Path) -> None:
    bundle = tmp_path / "plugin.dsgzip"
    bundle.write_bytes(b"bundle")
    manifest = {
        "name": "security-qa",
        "version": "1.0.0",
        "target": "security",
        "entry": "entry.json",
        "description": "Accessibility and shader QA",
        "platforms": ["windows", "linux"],
    }

    report = create_marketplace_entry(manifest, bundle, tmp_path / "marketplace")

    assert (tmp_path / "marketplace" / "security-qa@1.0.0.json").is_file()
    assert report["marketplace"]["platforms"] == ["windows", "linux"]


def test_plugin_bundle_rejects_traversal(tmp_path: Path) -> None:
    import zipfile

    bundle = tmp_path / "unsafe.dsgzip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "name": "unsafe",
            "version": "1.0.0",
            "target": "security",
            "entry": "entry.json",
        }))
        archive.writestr("../entry.json", "{}")

    try:
        inspect_plugin_bundle(bundle)
    except ValueError as error:
        assert "Unsafe plugin bundle path" in str(error)
    else:
        raise AssertionError("unsafe plugin bundle traversal was accepted")
