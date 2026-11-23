from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import create_project, load_project, save_project
from .mockup import analyze_mockup
from .renderers import render_html, render_react
from .router import route_task
from .validation import check_accessibility, check_responsive
from .visual import take_screenshots, compare_images
from .pipeline import run_pipeline
from .catalog import get_language_catalog, resolve_language, find_graphics_libraries
from .native_renderers import render_native
from .figma import import_figma_json
from .design_mappings import export_tailwind, react_tailwind_source
from .texture_pipeline import generate_seamless
from .engine_manifest import export_engine_manifest
from .publish import git_status, create_commit, create_mnemosyne_handoff
from .publish import mnemosyne_launch_preview
from .build_validation import validate_source
from .plugin_bundle import create_plugin_bundle, inspect_plugin_bundle
from .shader_validation import validate_shader
from .plugin_marketplace import create_marketplace_entry
from .mnemosyne_bridge import build_mnemosyne_mcp_config, create_mnemosyne_preview_manifest
from .os_sandbox import detect_os_sandbox, validate_sandbox_backend
from .toolchain_matrix import inspect_toolchain_matrix
from .hosted_marketplace import validate_hosted_entry, create_hosted_index
from .hosted_marketplace import start_marketplace_server, stop_marketplace_server
from .os_sandbox import build_sandbox_command
from .trust_store import TrustStore
from .preview_host import start_preview_server, stop_preview_server
from .publish import github_create_pr, github_create_issue
from .visual import inspect_preview
from .plugin_registry import PluginRegistry
from .orchestrator import doctor, run_all
from .figma_api import import_figma_api
from .os_sandbox import execute_sandbox_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="designatio")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--name", default="Untitled design")
    init.add_argument("--platform", default="web")
    init.add_argument("--stack", default="html")
    init.add_argument("--output", default="output/project.json")

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("mockup")
    analyze.add_argument("--mode", default="modernized")
    analyze.add_argument("--project", default="output/project.json")

    render = subparsers.add_parser("render")
    render.add_argument("project")
    render.add_argument("--output", default="output/site")

    render_react_parser = subparsers.add_parser("render-react")
    render_react_parser.add_argument("project")
    render_react_parser.add_argument("--output", default="output/react")

    route = subparsers.add_parser("route")
    route.add_argument("prompt")

    validate = subparsers.add_parser("validate")
    validate.add_argument("project")
    validate.add_argument("--output", default="output/validation.json")

    screenshot = subparsers.add_parser("screenshot")
    screenshot.add_argument("target")
    screenshot.add_argument("--output", default="output/screens")

    compare = subparsers.add_parser("compare")
    compare.add_argument("reference")
    compare.add_argument("rendered")
    compare.add_argument("--output", default="output/comparison")

    pipeline = subparsers.add_parser("pipeline")
    pipeline.add_argument("mockup")
    pipeline.add_argument("--name", default="Untitled design")
    pipeline.add_argument("--mode", default="production-ready")
    pipeline.add_argument("--output", default="output/pipeline")

    catalog = subparsers.add_parser("catalog")
    catalog.add_argument("--language")

    resolve = subparsers.add_parser("resolve-stack")
    resolve.add_argument("prompt")

    render_native_parser = subparsers.add_parser("render-native")
    render_native_parser.add_argument("target")
    render_native_parser.add_argument("project")
    render_native_parser.add_argument("--output", required=True)

    figma = subparsers.add_parser("import-figma")
    figma.add_argument("json")
    figma.add_argument("--output", default="output/figma")
    figma.add_argument("--name")

    tailwind = subparsers.add_parser("tailwind")
    tailwind.add_argument("project")
    tailwind.add_argument("--output", default="output/tailwind.json")

    texture = subparsers.add_parser("texture")
    texture.add_argument("source")
    texture.add_argument("--output", default="output/texture")

    engine = subparsers.add_parser("engine-manifest")
    engine.add_argument("target")
    engine.add_argument("project")
    engine.add_argument("--output", default="output/engine")

    handoff = subparsers.add_parser("mnemosyne-handoff")
    handoff.add_argument("project")
    handoff.add_argument("--output", default="output/mnemosyne")

    git = subparsers.add_parser("git-status")
    git.add_argument("repo")

    browser = subparsers.add_parser("browser-qa")
    browser.add_argument("target")

    mnemosyne_preview = subparsers.add_parser("mnemosyne-preview")
    mnemosyne_preview.add_argument("preview")

    validate_build = subparsers.add_parser("validate-build")
    validate_build.add_argument("target")
    validate_build.add_argument("source")

    bundle = subparsers.add_parser("plugin-bundle")
    bundle.add_argument("plugin_dir")
    bundle.add_argument("--output", required=True)

    inspect_bundle = subparsers.add_parser("inspect-plugin-bundle")
    inspect_bundle.add_argument("bundle")

    shader = subparsers.add_parser("validate-shader")
    shader.add_argument("shader")

    marketplace = subparsers.add_parser("plugin-marketplace")
    marketplace.add_argument("manifest")
    marketplace.add_argument("bundle")
    marketplace.add_argument("--output", default="output/marketplace")

    pr = subparsers.add_parser("github-pr")
    pr.add_argument("repo")
    pr.add_argument("title")
    pr.add_argument("--body", default="")
    pr.add_argument("--base", default="")
    pr.add_argument("--head", default="")

    issue = subparsers.add_parser("github-issue")
    issue.add_argument("repo")
    issue.add_argument("title")
    issue.add_argument("--body", default="")
    issue.add_argument("--label", action="append", default=[])

    mnemosyne_mcp = subparsers.add_parser("mnemosyne-mcp-config")
    mnemosyne_mcp.add_argument("project_dir")

    mnemosyne_manifest = subparsers.add_parser("mnemosyne-preview-manifest")
    mnemosyne_manifest.add_argument("project")
    mnemosyne_manifest.add_argument("preview")

    sandbox = subparsers.add_parser("sandbox-status")

    toolchains = subparsers.add_parser("toolchains")

    marketplace = subparsers.add_parser("hosted-marketplace")
    marketplace.add_argument("entries")
    marketplace.add_argument("--output", default="output/hosted-marketplace.json")

    marketplace_host = subparsers.add_parser("marketplace-host")
    marketplace_host.add_argument("directory")
    marketplace_host.add_argument("--port", type=int, default=4174)
    marketplace_host.add_argument("--stop", action="store_true")

    sandbox_command = subparsers.add_parser("sandbox-command")
    sandbox_command.add_argument("entry")
    sandbox_command.add_argument("--backend")

    trust = subparsers.add_parser("trust-key")
    trust.add_argument("name")
    trust.add_argument("public_key")
    trust.add_argument("--store", default="output/trust")

    trust_list = subparsers.add_parser("trust-list")
    trust_list.add_argument("--store", default="output/trust")

    preview = subparsers.add_parser("preview-host")
    preview.add_argument("directory")
    preview.add_argument("--port", type=int, default=4173)
    preview.add_argument("--stop", action="store_true")

    doctor_parser = subparsers.add_parser("doctor")

    run_auto = subparsers.add_parser("run-all")
    run_auto.add_argument("--mockup")
    run_auto.add_argument("--name", default="Automated Design")
    run_auto.add_argument("--output", default="output/automated")

    figma_api = subparsers.add_parser("import-figma-api")
    figma_api.add_argument("file_key")
    figma_api.add_argument("--token")
    figma_api.add_argument("--output", default="output/figma-api")
    figma_api.add_argument("--name")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "init":
        project = create_project(args.name, args.platform, args.stack)
        output = save_project(project, args.output)
        print(output)
        return 0

    if args.command == "analyze":
        project_path = Path(args.project)
        project = load_project(project_path) if project_path.is_file() else create_project()
        analysis = analyze_mockup(args.mockup, args.mode)
        project["brief"]["mode"] = args.mode
        project["assets"].append(analysis["source"])
        project["components"] = analysis.get("components", [])
        project["reports"].append({"type": "mockup-analysis", "data": analysis})
        save_project(project, project_path)
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
        return 0

    if args.command == "render":
        project = load_project(args.project)
        rendered = render_html(project, args.output)
        output = save_project(rendered, args.project)
        print(output)
        return 0

    if args.command == "render-react":
        project = load_project(args.project)
        rendered = render_react(project, args.output)
        output = save_project(rendered, args.project)
        print(output)
        return 0

    if args.command == "route":
        print(json.dumps(route_task(args.prompt), ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate":
        project = load_project(args.project)
        report = {
            "accessibility": check_accessibility(project),
            "responsive": check_responsive(project),
        }
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(output)
        return 0

    if args.command == "screenshot":
        report = take_screenshots(args.target, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "compare":
        report = compare_images(args.reference, args.rendered, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "pipeline":
        report = run_pipeline(args.mockup, args.output, args.name, args.mode)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1

    if args.command == "catalog":
        if args.language:
            canonical = resolve_language(args.language)
            catalog_data = get_language_catalog().get(canonical, {}) if canonical else {}
        else:
            catalog_data = get_language_catalog()
        print(json.dumps(catalog_data, ensure_ascii=False, indent=2))
        return 0

    if args.command == "resolve-stack":
        print(json.dumps(find_graphics_libraries(args.prompt), ensure_ascii=False, indent=2))
        return 0

    if args.command == "render-native":
        project = load_project(args.project)
        report = render_native(project, args.target, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "import-figma":
        report = import_figma_json(args.json, args.output, args.name)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "tailwind":
        project = load_project(args.project)
        mapping = export_tailwind(project)
        output = Path(args.output)
        if output.suffix.lower() in {".js", ".json"}:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(react_tailwind_source(project), encoding="utf-8")
        print(str(output.resolve()))
        return 0

    if args.command == "texture":
        report = generate_seamless(args.source, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "engine-manifest":
        project = load_project(args.project)
        report = export_engine_manifest(project, args.target, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "mnemosyne-handoff":
        project = load_project(args.project)
        report = create_mnemosyne_handoff(project, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "git-status":
        print(json.dumps(git_status(args.repo), ensure_ascii=False, indent=2))
        return 0

    if args.command == "browser-qa":
        print(json.dumps(inspect_preview(args.target), ensure_ascii=False, indent=2))
        return 0

    if args.command == "mnemosyne-preview":
        print(json.dumps(mnemosyne_launch_preview(args.preview), ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate-build":
        print(json.dumps(validate_source(args.target, args.source), ensure_ascii=False, indent=2))
        return 0

    if args.command == "plugin-bundle":
        print(json.dumps(create_plugin_bundle(args.plugin_dir, args.output), ensure_ascii=False, indent=2))
        return 0

    if args.command == "inspect-plugin-bundle":
        print(json.dumps(inspect_plugin_bundle(args.bundle), ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate-shader":
        shader_path = Path(args.shader)
        if not shader_path.is_file():
            print(json.dumps({
                "passed": False,
                "status": "not-found",
                "stage": shader_path.suffix.lower().lstrip("."),
                "shader": str(shader_path.resolve()),
                "error": "Shader not found",
            }, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps(validate_shader(shader_path), ensure_ascii=False, indent=2))
        return 0

    if args.command == "plugin-marketplace":
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        print(json.dumps(create_marketplace_entry(manifest, args.bundle, args.output), ensure_ascii=False, indent=2))
        return 0

    if args.command == "github-pr":
        print(json.dumps(github_create_pr(args.repo, args.title, args.body, args.base, args.head), ensure_ascii=False, indent=2))
        return 0

    if args.command == "github-issue":
        print(json.dumps(github_create_issue(args.repo, args.title, args.body, args.label), ensure_ascii=False, indent=2))
        return 0

    if args.command == "mnemosyne-mcp-config":
        print(json.dumps(build_mnemosyne_mcp_config(args.project_dir), ensure_ascii=False, indent=2))
        return 0

    if args.command == "mnemosyne-preview-manifest":
        project = load_project(args.project)
        print(json.dumps(create_mnemosyne_preview_manifest(args.preview, project), ensure_ascii=False, indent=2))
        return 0

    if args.command == "sandbox-status":
        print(json.dumps(detect_os_sandbox(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "toolchains":
        print(json.dumps(inspect_toolchain_matrix(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "hosted-marketplace":
        entries = json.loads(Path(args.entries).read_text(encoding="utf-8-sig"))
        report = create_hosted_index(entries, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "marketplace-host":
        report = stop_marketplace_server(args.port) if args.stop else start_marketplace_server(args.directory, args.port)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "sandbox-command":
        print(json.dumps(build_sandbox_command(args.entry, {}, args.backend), ensure_ascii=False, indent=2))
        return 0

    if args.command == "doctor":
        print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "run-all":
        report = run_all(args.mockup, args.name, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1

    if args.command == "import-figma-api":
        try:
            report = import_figma_api(args.file_key, args.output, args.token, args.name)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        except (ValueError, RuntimeError) as error:
            print(json.dumps({"passed": False, "status": "figma-api-error", "error": str(error)}, ensure_ascii=False, indent=2))
            return 1

    if args.command == "trust-key":
        store = TrustStore(args.store)
        print(json.dumps(store.add_public_key(args.name, args.public_key), ensure_ascii=False, indent=2))
        return 0

    if args.command == "trust-list":
        print(json.dumps(TrustStore(args.store).list(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "preview-host":
        report = stop_preview_server(args.port) if args.stop else start_preview_server(args.directory, args.port)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
