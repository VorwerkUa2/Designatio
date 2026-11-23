from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import create_project, load_project, save_project
from .mockup import analyze_mockup
from .renderers import render_html
from .router import route_task
from .validation import check_accessibility, check_responsive


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

    route = subparsers.add_parser("route")
    route.add_argument("prompt")

    validate = subparsers.add_parser("validate")
    validate.add_argument("project")
    validate.add_argument("--output", default="output/validation.json")

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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
