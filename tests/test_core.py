import json
from pathlib import Path
import subprocess
import sys

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
from designatio.os_sandbox import build_sandbox_command, execute_sandbox_command
from designatio.trust_store import TrustStore
from designatio.preview_host import start_preview_server, stop_preview_server
from designatio.platform import python_executable, npm_executable, tesseract_executable
from designatio.mnemosyne_bridge import build_mnemosyne_mcp_config, create_mnemosyne_preview_manifest
from designatio.os_sandbox import detect_os_sandbox
from designatio.toolchain_matrix import inspect_toolchain_matrix
from designatio.hosted_marketplace import start_marketplace_server, stop_marketplace_server
from designatio.os_sandbox import build_sandbox_command
from designatio.figma_api import fetch_figma_file
from designatio.orchestrator import bootstrap_cli
from designatio.orchestrator import doctor, run_all
from designatio.hosted_marketplace import validate_hosted_entry, create_hosted_index
from designatio.os_sandbox import detect_os_sandbox, validate_sandbox_backend
from designatio.toolchain_matrix import inspect_toolchain_matrix
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
    flutter_source = (tmp_path / "flutter" / "lib" / "main.dart").read_text(encoding="utf-8")
    assert "),\n            Card(" in flutter_source
    assert (tmp_path / "swiftui" / "ContentView.swift").is_file()
    assert "VStack" in (tmp_path / "swiftui" / "ContentView.swift").read_text(encoding="utf-8")
    assert "Text(" in (tmp_path / "compose" / "DesignatioScreen.kt").read_text(encoding="utf-8")
    assert "CentralPanel" in (tmp_path / "egui" / "src" / "main.rs").read_text(encoding="utf-8")
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


def test_trust_store_ed25519_fingerprint(tmp_path: Path) -> None:
    registry = PluginRegistry(tmp_path / "registry")
    keys = registry.generate_ed25519_keypair(tmp_path / "private.pem", tmp_path / "public.pem")
    store = TrustStore(tmp_path / "trust")

    record = store.add_public_key("local-auditor", keys["public"])

    assert store.verify_fingerprint("local-auditor", keys["public"]) is True
    assert record["algorithm"] == "Ed25519"
    assert store.revoke("local-auditor") is True
    assert store.resolve("local-auditor") is None


def test_loopback_preview_host(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>Preview</h1>", encoding="utf-8")

    started = start_preview_server(tmp_path, 4199)
    stopped = stop_preview_server(4199)

    assert started["running"] is True
    assert started["url"] == "http://127.0.0.1:4199"
    assert stopped["running"] is False


def test_platform_helpers_resolve_cross_platform_executables() -> None:
    assert python_executable()
    assert npm_executable() is None or isinstance(npm_executable(), str)
    discovered = tesseract_executable()
    assert discovered is None or isinstance(discovered, str)


def test_os_sandbox_and_toolchain_detection() -> None:
    sandbox = detect_os_sandbox()
    toolchains = inspect_toolchain_matrix()

    assert sandbox["platform"] in {"nt", "posix"}
    assert isinstance(sandbox["candidates"], list)
    assert toolchains["toolchains"]
    assert validate_sandbox_backend("unknown")["available"] is False


def test_hosted_marketplace_validation_and_index(tmp_path: Path) -> None:
    entry = {
        "name": "region-qa",
        "version": "1.0.0",
        "target": "security",
        "entry": "entry.json",
        "bundle": "region-qa.dsgzip",
        "platforms": ["windows", "linux"],
    }

    validation = validate_hosted_entry(entry)
    index = create_hosted_index([entry], tmp_path / "marketplace.json")

    assert validation["passed"] is True
    assert index["count"] == 1
    assert (tmp_path / "marketplace.json").is_file()


def test_loopback_marketplace_server(tmp_path: Path) -> None:
    (tmp_path / "marketplace.json").write_text(json.dumps({"schema": "1", "entries": []}), encoding="utf-8")

    started = start_marketplace_server(tmp_path, 4196)
    stopped = stop_marketplace_server(4196)

    assert started["running"] is True
    assert started["url"] == "http://127.0.0.1:4196"
    assert stopped["running"] is False


def test_sandbox_command_builder(tmp_path: Path) -> None:
    entry = tmp_path / "entry.json"
    entry.write_text(json.dumps({"mode": "read-only"}), encoding="utf-8")

    report = build_sandbox_command(entry, {"region": "header"}, "bounded")

    assert report["backend"] == "bounded"
    assert report["command"][-1].endswith("entry.json")


def test_windows_job_object_command_when_requested(tmp_path: Path) -> None:
    entry = tmp_path / "entry.py"
    entry.write_text("print('sandbox')\n", encoding="utf-8")

    report = build_sandbox_command(entry, {}, "job-object")

    assert report["backend"] == "job-object"
    assert str(entry) in report["command"]


def test_windows_job_object_executes_child_process(tmp_path: Path) -> None:
    if sys.platform != "win32":
        return

    entry = tmp_path / "entry.py"
    entry.write_text("print('job-object-ok')\n", encoding="utf-8")
    report = build_sandbox_command(entry, {}, "job-object")

    execution = execute_sandbox_command(report, timeout=5)

    assert execution["passed"] is True
    assert execution["stdout"].strip() == "job-object-ok"

    entry.write_text("import time; time.sleep(30)\n", encoding="utf-8")
    timeout_report = build_sandbox_command(entry, {}, "job-object")
    timeout_execution = execute_sandbox_command(timeout_report, timeout=1)

    assert timeout_execution["passed"] is False


def test_cli_and_mcp_import_without_optional_pillow() -> None:
    script = """
import builtins
original_import = builtins.__import__
def import_without_pillow(name, *args, **kwargs):
    if name == "PIL" or name.startswith("PIL."):
        raise ModuleNotFoundError("Pillow intentionally unavailable")
    return original_import(name, *args, **kwargs)
builtins.__import__ = import_without_pillow
import designatio.cli
import designatio.mcp.server
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_figma_api_requires_token() -> None:
    try:
        fetch_figma_file("example", token="")
    except ValueError as error:
        assert "token" in str(error)
    else:
        raise AssertionError("Figma API accepted a missing token")


def test_bootstrap_is_explicit(tmp_path: Path) -> None:
    import contextlib
    import io

    stdout = io.StringIO()
    old = sys.argv
    sys.argv = ["designatio-bootstrap", "--flutter", "--android", "--shader-tools"]
    try:
        with contextlib.redirect_stdout(stdout):
            from designatio.orchestrator import bootstrap_cli
            result = bootstrap_cli()
    finally:
        sys.argv = old

    assert result == 0
    assert "flutter" in stdout.getvalue()


def test_doctor_and_automated_run(tmp_path: Path) -> None:
    report = doctor()
    run_report = run_all(None, "Test automation", tmp_path / "automated")

    assert report["python"]["executable"]
    assert "toolchains" in report
    assert (tmp_path / "automated" / "project.json").is_file()
    assert "run-report" in str(run_report["report"])


def test_mnemosyne_bridge_contract(tmp_path: Path) -> None:
    project = create_project("Mnemosyne app")
    preview = tmp_path / "preview"
    preview.mkdir()
    (preview / "index.html").write_text("<h1>Preview</h1>", encoding="utf-8")

    config = build_mnemosyne_mcp_config(tmp_path)
    manifest = create_mnemosyne_preview_manifest(preview, project)

    assert Path(config["config"]).is_file()
    assert config["mcpConfig"]["mcpServers"]["designatio"]["args"] == ["-m", "designatio.mcp.server"]
    assert manifest["preview"]["entry"].endswith("index.html")


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
