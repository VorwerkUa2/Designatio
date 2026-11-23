from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import hmac
import json


class PluginRegistry:
    def __init__(self, registry_dir: str | Path):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.registry_dir / "plugins.json"
        self.index_path.write_text(self.index_path.read_text(encoding="utf-8") if self.index_path.exists() else "{}", encoding="utf-8")

    def list(self) -> dict[str, Any]:
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def sign_manifest(self, manifest: dict[str, Any], secret: str) -> dict[str, Any]:
        payload = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        signed = dict(manifest)
        signed["signature"] = {"algorithm": "HMAC-SHA256", "value": signature}
        return signed

    def verify_manifest(self, manifest: dict[str, Any], secret: str) -> bool:
        signed = manifest.get("signature")
        if not isinstance(signed, dict):
            return False
        candidate = dict(manifest)
        candidate.pop("signature", None)
        payload = json.dumps(candidate, sort_keys=True, ensure_ascii=False).encode("utf-8")
        actual = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(actual, signed.get("value", ""))

    def register(self, manifest: dict[str, Any], secret: str) -> dict[str, Any]:
        allowed_targets = {"react", "flutter", "swiftui", "compose", "egui", "html", "texture", "security"}
        if manifest.get("target") not in allowed_targets:
            raise ValueError("Plugin target is not in the allowlist")
        name = str(manifest.get("name", "")).strip()
        version = str(manifest.get("version", "")).strip()
        if not name or not version:
            raise ValueError("Plugin name and version are required")
        signed = self.sign_manifest(manifest, secret)
        if not self.verify_manifest(signed, secret):
            raise RuntimeError("Plugin signature verification failed")
        index = self.list()
        index[f"{name}@{version}"] = signed
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        return signed

    def execute_builtin(self, manifest: dict[str, Any], payload: dict[str, Any], secret: str) -> dict[str, Any]:
        if not self.verify_manifest(manifest, secret):
            raise PermissionError("Refusing unverified plugin")
        target = manifest["target"]
        if target not in {"react", "flutter", "swiftui", "compose", "egui", "html", "texture", "security"}:
            raise PermissionError("Plugin target is outside the sandbox allowlist")
        return {"accepted": True, "target": target, "sandbox": "builtin-plugin-allowlist", "payload": payload}
