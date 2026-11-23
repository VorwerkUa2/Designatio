from __future__ import annotations

from pathlib import Path
from typing import Any
import json
from copy import deepcopy

from .contracts import create_project, save_project


def _walk(node: dict[str, Any], output: list[dict[str, Any]], depth: int = 0) -> None:
    name = str(node.get("name", "Untitled"))
    kind = str(node.get("type", "FRAME")).upper()
    children = node.get("children", [])
    if kind in {"FRAME", "GROUP", "COMPONENT", "COMPONENT_SET", "INSTANCE"}:
        output.append({
            "type": "section" if depth == 0 else "card",
            "title": name,
            "description": "",
            "sourceType": kind,
            "depth": depth,
        })
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                _walk(child, output, depth + 1)


def import_figma_json(path: str | Path, output_dir: str | Path, project_name: str | None = None) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Figma JSON not found: {source}")
    with source.open("r", encoding="utf-8-sig") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError("Figma JSON root must be an object")

    project = create_project(project_name or str(document.get("name", "Figma import")), "web", "react")
    document_node = document.get("document", document)
    components: list[dict[str, Any]] = []
    _walk(document_node if isinstance(document_node, dict) else {}, components)

    text_nodes: list[str] = []
    for node in document_node.get("children", []) if isinstance(document_node, dict) else []:
        if not isinstance(node, dict):
            continue
        stack = [node]
        while stack:
            current = stack.pop()
            if current.get("type") == "TEXT":
                text = current.get("characters")
                if isinstance(text, str) and text.strip():
                    text_nodes.append(text.strip())
            children = current.get("children")
            if isinstance(children, list):
                stack.extend(child for child in children if isinstance(child, dict))

    if text_nodes:
        for index, component in enumerate(components):
            if index == 0:
                component["description"] = " ".join(text_nodes[:8])
            elif text_nodes:
                component["description"] = text_nodes[index % len(text_nodes)]

    project["components"] = components
    project["screens"].append({
        "name": str(document.get("name", "Imported screen")),
        "source": str(source.resolve()),
        "componentCount": len(components),
    })
    project["assets"].append({
        "path": str(source.resolve()),
        "name": source.name,
        "type": "figma-json",
    })
    project["reports"].append({"type": "figma-import", "components": len(components), "textNodes": len(text_nodes)})

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    project_path = save_project(project, output / "project.json")
    return {"project": str(project_path.resolve()), "components": len(components), "textNodes": len(text_nodes), "screens": project["screens"]}
