from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import zipfile


MAX_PLUGIN_BUNDLE_BYTES = 100 * 1024 * 1024
MAX_PLUGIN_MEMBER_BYTES = 25 * 1024 * 1024


def create_plugin_bundle(plugin_dir: str | Path, output_path: str | Path) -> dict[str, Any]:
    source = Path(plugin_dir)
    if not source.is_dir():
        raise FileNotFoundError(f"Plugin directory not found: {source}")
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Plugin manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    for field in ("name", "version", "target", "entry"):
        if not manifest.get(field):
            raise ValueError(f"Plugin manifest missing required field: {field}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(manifest_path, "manifest.json")
        for path in sorted(source.rglob("*")):
            if path.is_file() and path != manifest_path:
                relative = path.relative_to(source).as_posix()
                if relative in {"private.pem", "private-key.pem"} or relative.endswith(".pem"):
                    if "public" not in relative:
                        continue
                archive.write(path, relative)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                files.append({"path": relative, "sha256": digest, "size": path.stat().st_size})

    bundle_digest = hashlib.sha256(output.read_bytes()).hexdigest()
    manifest["bundleSha256"] = bundle_digest
    return {
        "bundle": str(output.resolve()),
        "manifest": manifest,
        "files": files,
        "sha256": bundle_digest,
    }


def inspect_plugin_bundle(bundle_path: str | Path) -> dict[str, Any]:
    bundle = Path(bundle_path)
    if not bundle.is_file():
        raise FileNotFoundError(f"Plugin bundle not found: {bundle}")
    if bundle.stat().st_size > MAX_PLUGIN_BUNDLE_BYTES:
        raise ValueError("Plugin bundle exceeds 100 MB safety limit")
    with zipfile.ZipFile(bundle, "r") as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"Corrupt plugin bundle member: {bad_member}")
        names = archive.namelist()
        if "manifest.json" not in names:
            raise ValueError("Plugin bundle has no manifest.json")
        manifest = json.loads(archive.read("manifest.json").decode("utf-8-sig"))
        files = []
        total = 0
        for name in names:
            if name == "manifest.json":
                continue
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or ".." in Path(normalized).parts:
                raise ValueError(f"Unsafe plugin bundle path: {name}")
            info = archive.getinfo(name)
            if info.file_size > MAX_PLUGIN_MEMBER_BYTES:
                raise ValueError(f"Plugin member exceeds 25 MB: {name}")
            total += info.file_size
            if total > MAX_PLUGIN_BUNDLE_BYTES:
                raise ValueError("Uncompressed plugin bundle exceeds 100 MB safety limit")
            data = archive.read(name)
            files.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    return {
        "bundle": str(bundle.resolve()),
        "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "manifest": manifest,
        "files": files,
    }
