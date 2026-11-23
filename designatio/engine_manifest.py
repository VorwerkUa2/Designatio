from __future__ import annotations

from pathlib import Path
from typing import Any
import json


ENGINE_EXPORTS = {
    "threejs": "threejs",
    "babylon": "babylonjs",
    "unity": "unity",
    "godot": "godot",
    "unreal": "unreal",
    "bevy": "bevy",
    "blender": "blender",
}


def export_engine_manifest(project: dict[str, Any], engine: str, output_dir: str | Path) -> dict[str, Any]:
    normalized = engine.lower().strip()
    if normalized not in ENGINE_EXPORTS:
        raise ValueError(f"Unsupported engine: {engine}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    nodes = []
    for index, component in enumerate(project.get("components", [])):
        nodes.append({
            "id": f"node-{index}",
            "name": component.get("title", f"Component {index}"),
            "type": component.get("type", "section"),
            "description": component.get("description", ""),
            "transform": {"position": [index * 2.0, 0.0, 0.0], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
            "material": {"baseColor": project["tokens"]["colors"]["surface"], "roughness": 0.65, "metallic": 0.0},
        })

    manifest = {
        "schema": "1",
        "name": project["name"],
        "engine": ENGINE_EXPORTS[normalized],
        "units": "meters",
        "camera": {"position": [0, 2, 8], "target": [0, 1, 0], "fov": 45},
        "lighting": {"environment": "studio", "exposure": 1.0},
        "nodes": nodes,
        "assets": project.get("assets", []),
        "sourceProject": str(project.get("preview", {}).get("html", "")),
    }
    path = output / f"{normalized}-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"engine": normalized, "manifest": str(path.resolve()), "nodes": len(nodes)}
