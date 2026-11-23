from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def create_marketplace_entry(manifest: dict[str, Any], bundle_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    for field in ("name", "version", "target", "entry"):
        if not manifest.get(field):
            raise ValueError(f"Manifest missing required field: {field}")
    bundle = Path(bundle_path)
    if not bundle.is_file():
        raise FileNotFoundError(f"Plugin bundle not found: {bundle}")
    entry = {
        "name": manifest["name"],
        "version": manifest["version"],
        "target": manifest["target"],
        "description": manifest.get("description", ""),
        "author": manifest.get("author", ""),
        "license": manifest.get("license", ""),
        "homepage": manifest.get("homepage", ""),
        "bundle": str(bundle.resolve()),
        "entry": manifest["entry"],
        "signature": manifest.get("signature"),
        "keywords": manifest.get("keywords", []),
        "platforms": manifest.get("platforms", ["any"]),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{manifest['name']}@{manifest['version']}.json"
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"entry": str(path.resolve()), "marketplace": entry}
