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
from .visual import inspect_preview
from .plugin_registry import PluginRegistry


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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
