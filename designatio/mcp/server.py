from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ..contracts import create_project, load_project, save_project
from ..mockup import analyze_mockup
from ..renderers import render_html
from ..router import route_task
from ..validation import check_accessibility, check_responsive


TOOLS = [
    {
        "name": "design_create_brief",
        "description": "Create a versioned Designatio project from name, platform and stack.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "platform": {"type": "string", "enum": ["web", "mobile", "desktop", "game"]},
                "stack": {"type": "string"},
                "brief": {"type": "object"},
                "outputPath": {"type": "string"},
            },
        },
    },
    {
        "name": "design_analyze_mockup",
        "description": "Inspect a screenshot or SVG and produce a mockup-to-code analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mockupPath": {"type": "string"},
                "mode": {"type": "string", "enum": ["pixel-faithful", "ux-improved", "modernized", "accessible", "production-ready"]},
                "projectPath": {"type": "string"},
            },
            "required": ["mockupPath"],
        },
    },
    {
        "name": "design_generate_system",
        "description": "Create or replace design tokens for an existing project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "projectPath": {"type": "string"},
                "tokens": {"type": "object"},
            },
            "required": ["projectPath", "tokens"],
        },
    },
    {
        "name": "design_render",
        "description": "Render a project as responsive HTML and update the project preview.",
        "inputSchema": {
            "type": "object",
            "properties": {"projectPath": {"type": "string"}, "outputDir": {"type": "string"}},
            "required": ["projectPath", "outputDir"],
        },
    },
    {
        "name": "design_check_accessibility",
        "description": "Check project contrast and basic accessibility requirements.",
        "inputSchema": {"type": "object", "properties": {"projectPath": {"type": "string"}}, "required": ["projectPath"]},
    },
    {
        "name": "design_check_responsive",
        "description": "Check responsive content at standard breakpoints.",
        "inputSchema": {"type": "object", "properties": {"projectPath": {"type": "string"}}, "required": ["projectPath"]},
    },
    {
        "name": "design_export",
        "description": "Save a project to a JSON file.",
        "inputSchema": {
            "type": "object",
            "properties": {"projectPath": {"type": "string"}, "outputPath": {"type": "string"}},
            "required": ["projectPath", "outputPath"],
        },
    },
    {
        "name": "design_route",
        "description": "Route a natural-language design request to one or more skills.",
        "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]},
    },
]


def result(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}]}


def execute(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "design_create_brief":
        project = create_project(
            arguments.get("name", "Untitled design"),
            arguments.get("platform", "web"),
            arguments.get("stack", "html"),
            arguments.get("brief"),
        )
        output = save_project(project, arguments.get("outputPath", "output/project.json"))
        return result({"project": project, "savedTo": str(output)})

    if name == "design_analyze_mockup":
        analysis = analyze_mockup(arguments["mockupPath"], arguments.get("mode", "modernized"))
        project_path = Path(arguments.get("projectPath", "output/project.json"))
        project = load_project(project_path) if project_path.is_file() else create_project()
        project["brief"]["mode"] = arguments.get("mode", "modernized")
        project["assets"].append(analysis["source"])
        project["reports"].append({"type": "mockup-analysis", "data": analysis})
        save_project(project, project_path)
        return result(analysis)

    if name == "design_generate_system":
        project_path = arguments["projectPath"]
        project = load_project(project_path)
        project["tokens"] = arguments["tokens"]
        save_project(project, project_path)
        return result(project)

    if name == "design_render":
        project_path = arguments["projectPath"]
        project = load_project(project_path)
        rendered = render_html(project, arguments["outputDir"])
        save_project(rendered, project_path)
        return result(rendered["preview"])

    if name == "design_check_accessibility":
        return result(check_accessibility(load_project(arguments["projectPath"])))

    if name == "design_check_responsive":
        return result(check_responsive(load_project(arguments["projectPath"])))

    if name == "design_export":
        project = load_project(arguments["projectPath"])
        output = save_project(project, arguments["outputPath"])
        return result({"savedTo": str(output)})

    if name == "design_route":
        return result(route_task(arguments["prompt"]))

    raise ValueError(f"Unknown tool: {name}")


def handle(request: dict[str, Any]) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "designatio", "version": "0.1.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = request.get("params", {})
        try:
            payload = execute(params["name"], params.get("arguments", {}))
            return {"jsonrpc": "2.0", "id": request_id, "result": payload}
        except Exception as error:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(error)},
            }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle(request)
        except json.JSONDecodeError as error:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(error)}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
