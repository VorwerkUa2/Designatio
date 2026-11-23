from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ..contracts import create_project, load_project, save_project
from ..mockup import analyze_mockup
from ..renderers import render_html, render_react
from ..router import route_task
from ..validation import check_accessibility, check_responsive
from ..visual import take_screenshots, compare_images, inspect_preview, compare_regions
from ..pipeline import run_pipeline
from ..catalog import get_language_catalog, resolve_language, find_graphics_libraries
from ..native_renderers import render_native
from ..figma import import_figma_json
from ..design_mappings import export_tailwind
from ..texture_pipeline import generate_seamless
from ..engine_manifest import export_engine_manifest
from ..publish import git_status, create_commit, create_mnemosyne_handoff, push_repository, github_status, github_create_release, mnemosyne_launch_preview
from ..build_validation import validate_source
from ..plugin_bundle import create_plugin_bundle, inspect_plugin_bundle
from ..shader_validation import validate_shader
from ..plugin_marketplace import create_marketplace_entry
from ..publish import github_create_pr, github_create_issue
from ..plugin_registry import PluginRegistry


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
    {
        "name": "design_take_screenshots",
        "description": "Render an HTML preview in Chromium and capture desktop, tablet and mobile screenshots.",
        "inputSchema": {
            "type": "object",
            "properties": {"target": {"type": "string"}, "outputDir": {"type": "string"}},
            "required": ["target", "outputDir"],
        },
    },
    {
        "name": "design_compare",
        "description": "Compare a mockup against a rendered screenshot and create a visual diff.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reference": {"type": "string"},
                "rendered": {"type": "string"},
                "outputDir": {"type": "string"},
            },
            "required": ["reference", "rendered", "outputDir"],
        },
    },
    {
        "name": "design_render_react",
        "description": "Generate a responsive Vite and React implementation from a Designatio project.",
        "inputSchema": {
            "type": "object",
            "properties": {"projectPath": {"type": "string"}, "outputDir": {"type": "string"}},
            "required": ["projectPath", "outputDir"],
        },
    },
    {
        "name": "design_run_pipeline",
        "description": "Run the complete mockup-to-code pipeline with React build, screenshots, accessibility and visual comparison.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mockupPath": {"type": "string"},
                "outputDir": {"type": "string"},
                "name": {"type": "string"},
                "mode": {"type": "string"},
            },
            "required": ["mockupPath", "outputDir"],
        },
    },
    {
        "name": "design_list_languages",
        "description": "List supported programming languages and their UI, graphics and preview libraries.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "design_resolve_stack",
        "description": "Resolve a language or framework request into UI, graphics and preview recommendations.",
        "inputSchema": {
            "type": "object",
            "properties": {"prompt": {"type": "string"}, "language": {"type": "string"}},
            "required": ["prompt"],
        },
    },
    {
        "name": "design_render_native",
        "description": "Generate Flutter, SwiftUI, Compose, egui or Tauri source from a Designatio project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "projectPath": {"type": "string"},
                "target": {"type": "string", "enum": ["flutter", "swiftui", "compose", "egui", "tauri"]},
                "outputDir": {"type": "string"},
            },
            "required": ["projectPath", "target", "outputDir"],
        },
    },
    {
        "name": "design_import_figma",
        "description": "Import Figma exported JSON into the Designatio project schema.",
        "inputSchema": {
            "type": "object",
            "properties": {"jsonPath": {"type": "string"}, "outputDir": {"type": "string"}, "name": {"type": "string"}},
            "required": ["jsonPath", "outputDir"],
        },
    },
    {
        "name": "design_export_tailwind",
        "description": "Export design tokens and React Tailwind class hints.",
        "inputSchema": {"type": "object", "properties": {"projectPath": {"type": "string"}, "outputDir": {"type": "string"}}, "required": ["projectPath", "outputDir"]},
    },
    {
        "name": "design_generate_texture",
        "description": "Generate seamless base, normal and roughness texture maps.",
        "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "outputDir": {"type": "string"}, "size": {"type": "integer"}}, "required": ["source", "outputDir"]},
    },
    {
        "name": "design_export_engine",
        "description": "Export a neutral 3D engine manifest for Three.js, Babylon, Unity, Godot, Unreal, Bevy or Blender.",
        "inputSchema": {"type": "object", "properties": {"projectPath": {"type": "string"}, "engine": {"type": "string"}, "outputDir": {"type": "string"}}, "required": ["projectPath", "engine", "outputDir"]},
    },
    {
        "name": "design_mnemosyne_handoff",
        "description": "Create a machine-readable Mnemosyne workspace handoff.",
        "inputSchema": {"type": "object", "properties": {"projectPath": {"type": "string"}, "outputDir": {"type": "string"}}, "required": ["projectPath", "outputDir"]},
    },
    {
        "name": "design_git_status",
        "description": "Read Git status for a local repository without modifying it.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}, "required": ["repo"]},
    },
    {
        "name": "design_register_plugin",
        "description": "Register a signed plugin manifest in the local plugin allowlist.",
        "inputSchema": {"type": "object", "properties": {"registryDir": {"type": "string"}, "manifest": {"type": "object"}, "secret": {"type": "string"}}, "required": ["registryDir", "manifest", "secret"]},
    },
    {
        "name": "design_browser_qa",
        "description": "Inspect DOM overflow, heading structure, alt text, button names and document language.",
        "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]},
    },
    {
        "name": "design_push",
        "description": "Push an existing local Designatio repository to a configured remote.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "remote": {"type": "string"}, "branch": {"type": "string"}}, "required": ["repo"]},
    },
    {
        "name": "design_compare_regions",
        "description": "Compare detected OCR/layout regions against a rendered screenshot.",
        "inputSchema": {"type": "object", "properties": {"reference": {"type": "string"}, "rendered": {"type": "string"}, "regions": {"type": "array"}, "outputDir": {"type": "string"}}, "required": ["reference", "rendered", "regions", "outputDir"]},
    },
    {
        "name": "design_plugin_keys",
        "description": "Generate an Ed25519 keypair for plugin signing.",
        "inputSchema": {"type": "object", "properties": {"registryDir": {"type": "string"}, "privateName": {"type": "string"}, "publicName": {"type": "string"}}, "required": ["registryDir"]},
    },
    {
        "name": "design_plugin_sign",
        "description": "Sign a plugin manifest with Ed25519.",
        "inputSchema": {"type": "object", "properties": {"registryDir": {"type": "string"}, "manifest": {"type": "object"}, "privateKey": {"type": "string"}}, "required": ["registryDir", "manifest", "privateKey"]},
    },
    {
        "name": "design_plugin_execute",
        "description": "Verify and execute a plugin under the allowlisted sandbox.",
        "inputSchema": {"type": "object", "properties": {"registryDir": {"type": "string"}, "manifest": {"type": "object"}, "publicKey": {"type": "string"}, "payload": {"type": "object"}}, "required": ["registryDir", "manifest", "publicKey"]},
    },
    {
        "name": "design_github_status",
        "description": "Inspect the local repository and GitHub CLI repository metadata.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}}, "required": ["repo"]},
    },
    {
        "name": "design_github_release",
        "description": "Create a GitHub release for an existing tag.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "tag": {"type": "string"}, "title": {"type": "string"}, "notes": {"type": "string"}}, "required": ["repo", "tag", "title"]},
    },
    {
        "name": "design_mnemosyne_preview",
        "description": "Create a Mnemosyne preview handoff for a generated preview directory.",
        "inputSchema": {"type": "object", "properties": {"previewDir": {"type": "string"}}, "required": ["previewDir"]},
    },
    {
        "name": "design_validate_build",
        "description": "Validate generated source with the installed toolchain or report an explicit unavailable status.",
        "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "sourceDir": {"type": "string"}}, "required": ["target", "sourceDir"]},
    },
    {
        "name": "design_plugin_bundle",
        "description": "Create or inspect an offline Designatio plugin bundle.",
        "inputSchema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["create", "inspect"]}, "pluginDir": {"type": "string"}, "bundle": {"type": "string"}}, "required": ["action"]},
    },
    {
        "name": "design_validate_shader",
        "description": "Validate a shader with a local registered toolchain or report an explicit unavailable status.",
        "inputSchema": {"type": "object", "properties": {"shader": {"type": "string"}}, "required": ["shader"]},
    },
    {
        "name": "design_plugin_marketplace",
        "description": "Create a machine-readable offline plugin marketplace entry.",
        "inputSchema": {"type": "object", "properties": {"manifest": {"type": "object"}, "bundle": {"type": "string"}, "outputDir": {"type": "string"}}, "required": ["manifest", "bundle", "outputDir"]},
    },
    {
        "name": "design_github_pr",
        "description": "Create a GitHub pull request in a local repository.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "base": {"type": "string"}, "head": {"type": "string"}}, "required": ["repo", "title"]},
    },
    {
        "name": "design_github_issue",
        "description": "Create a GitHub issue in a local repository.",
        "inputSchema": {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "labels": {"type": "array", "items": {"type": "string"}}}, "required": ["repo", "title"]},
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

    if name == "design_take_screenshots":
        return result(take_screenshots(arguments["target"], arguments["outputDir"]))

    if name == "design_compare":
        return result(compare_images(arguments["reference"], arguments["rendered"], arguments["outputDir"]))

    if name == "design_render_react":
        project_path = arguments["projectPath"]
        project = load_project(project_path)
        rendered = render_react(project, arguments["outputDir"])
        save_project(rendered, project_path)
        return result(rendered["preview"])

    if name == "design_run_pipeline":
        return result(run_pipeline(
            arguments["mockupPath"],
            arguments["outputDir"],
            arguments.get("name", "Untitled design"),
            arguments.get("mode", "production-ready"),
        ))

    if name == "design_list_languages":
        return result({
            "count": len(get_language_catalog()),
            "languages": get_language_catalog(),
        })

    if name == "design_resolve_stack":
        language = resolve_language(arguments.get("language", ""))
        return result({
            "language": language,
            "matches": find_graphics_libraries(arguments["prompt"]),
        })

    if name == "design_render_native":
        project = load_project(arguments["projectPath"])
        return result(render_native(project, arguments["target"], arguments["outputDir"]))

    if name == "design_import_figma":
        return result(import_figma_json(arguments["jsonPath"], arguments["outputDir"], arguments.get("name")))

    if name == "design_export_tailwind":
        project = load_project(arguments["projectPath"])
        output = Path(arguments["outputDir"])
        output.mkdir(parents=True, exist_ok=True)
        mapping_path = output / "tailwind.json"
        mapping_path.write_text(json.dumps(export_tailwind(project), ensure_ascii=False, indent=2), encoding="utf-8")
        return result({"mapping": str(mapping_path.resolve()), "data": export_tailwind(project)})

    if name == "design_generate_texture":
        size = arguments.get("size", 512)
        report = generate_seamless(arguments["source"], arguments["outputDir"], int(size))
        return result(report)

    if name == "design_export_engine":
        project = load_project(arguments["projectPath"])
        return result(export_engine_manifest(project, arguments["engine"], arguments["outputDir"]))

    if name == "design_mnemosyne_handoff":
        project = load_project(arguments["projectPath"])
        return result(create_mnemosyne_handoff(project, arguments["outputDir"]))

    if name == "design_git_status":
        return result(git_status(arguments["repo"]))

    if name == "design_register_plugin":
        registry = PluginRegistry(arguments["registryDir"])
        return result(registry.register(arguments["manifest"], arguments["secret"]))

    if name == "design_browser_qa":
        return result(inspect_preview(arguments["target"]))

    if name == "design_push":
        return result(push_repository(arguments["repo"], arguments.get("remote", "origin"), arguments.get("branch", "main")))

    if name == "design_compare_regions":
        return result(compare_regions(arguments["reference"], arguments["rendered"], arguments["regions"], arguments["outputDir"]))

    if name == "design_plugin_keys":
        registry = PluginRegistry(arguments["registryDir"])
        private_name = arguments.get("privateName", "plugin-private.pem")
        public_name = arguments.get("publicName", "plugin-public.pem")
        root = Path(arguments["registryDir"])
        return result(registry.generate_ed25519_keypair(root / private_name, root / public_name))

    if name == "design_plugin_sign":
        registry = PluginRegistry(arguments["registryDir"])
        return result(registry.sign_ed25519(arguments["manifest"], arguments["privateKey"]))

    if name == "design_plugin_execute":
        registry = PluginRegistry(arguments["registryDir"])
        return result(registry.execute_sandboxed(arguments["manifest"], arguments["publicKey"], arguments.get("payload", {})))

    if name == "design_github_status":
        return result(github_status(arguments["repo"]))

    if name == "design_github_release":
        return result(github_create_release(arguments["repo"], arguments["tag"], arguments["title"], arguments.get("notes", "")))

    if name == "design_mnemosyne_preview":
        return result(mnemosyne_launch_preview(arguments["previewDir"]))

    if name == "design_validate_build":
        return result(validate_source(arguments["target"], arguments["sourceDir"]))

    if name == "design_plugin_bundle":
        if arguments["action"] == "create":
            if not arguments.get("pluginDir") or not arguments.get("bundle"):
                raise ValueError("Create action requires pluginDir and bundle")
            return result(create_plugin_bundle(arguments["pluginDir"], arguments["bundle"]))
        if arguments["action"] == "inspect":
            if not arguments.get("bundle"):
                raise ValueError("Inspect action requires bundle")
            return result(inspect_plugin_bundle(arguments["bundle"]))
        raise ValueError("Unsupported plugin bundle action")

    if name == "design_validate_shader":
        return result(validate_shader(arguments["shader"]))

    if name == "design_plugin_marketplace":
        return result(create_marketplace_entry(arguments["manifest"], arguments["bundle"], arguments["outputDir"]))

    if name == "design_github_pr":
        return result(github_create_pr(arguments["repo"], arguments["title"], arguments.get("body", ""), arguments.get("base", ""), arguments.get("head", "")))

    if name == "design_github_issue":
        return result(github_create_issue(arguments["repo"], arguments["title"], arguments.get("body", ""), arguments.get("labels", [])))

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
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

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
