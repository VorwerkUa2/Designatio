from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import tempfile
import sys
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


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

    def generate_ed25519_keypair(self, private_path: str | Path, public_path: str | Path) -> dict[str, str]:
        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        private = Path(private_path)
        public = Path(public_path)
        private.parent.mkdir(parents=True, exist_ok=True)
        public.parent.mkdir(parents=True, exist_ok=True)
        private.write_bytes(private_bytes)
        public.write_bytes(public_bytes)
        os.chmod(private, 0o600)
        return {"private": str(private.resolve()), "public": str(public.resolve())}

    def sign_ed25519(self, manifest: dict[str, Any], private_path: str | Path) -> dict[str, Any]:
        private_key = serialization.load_pem_private_key(
            Path(private_path).read_bytes(),
            password=None,
        )
        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("Private key must be Ed25519")
        candidate = dict(manifest)
        candidate.pop("signature", None)
        payload = json.dumps(candidate, sort_keys=True, ensure_ascii=False).encode("utf-8")
        value = private_key.sign(payload).hex()
        signed = dict(candidate)
        signed["signature"] = {"algorithm": "Ed25519", "value": value}
        return signed

    def verify_ed25519(self, manifest: dict[str, Any], public_path: str | Path) -> bool:
        signed = manifest.get("signature")
        if not isinstance(signed, dict) or signed.get("algorithm") != "Ed25519":
            return False
        candidate = dict(manifest)
        candidate.pop("signature", None)
        payload = json.dumps(candidate, sort_keys=True, ensure_ascii=False).encode("utf-8")
        try:
            signature = bytes.fromhex(signed.get("value", ""))
            public_key = serialization.load_pem_public_key(Path(public_path).read_bytes())
            if not isinstance(public_key, Ed25519PublicKey):
                return False
            public_key.verify(signature, payload)
            return True
        except (ValueError, InvalidSignature, OSError):
            return False

    def execute_sandboxed(self, manifest: dict[str, Any], public_path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
        allowed_targets = {"react", "flutter", "swiftui", "compose", "egui", "tauri", "html", "texture", "security"}
        if not self.verify_ed25519(manifest, public_path):
            raise PermissionError("Refusing plugin with invalid Ed25519 signature")
        target = manifest.get("target")
        if target not in allowed_targets:
            raise PermissionError("Plugin target is outside the sandbox allowlist")
        required = {"name", "version", "target", "entry"}
        if not required.issubset(manifest):
            raise ValueError("Plugin manifest requires name, version, target and entry")
        entry = str(manifest["entry"])
        if Path(entry).is_absolute():
            raise PermissionError("Plugin entry must be repository-relative")
        root = Path(manifest.get("sandboxRoot", self.registry_dir)).resolve()
        resolved = (root / entry).resolve()
        if resolved.parent != root and root not in resolved.parents:
            raise PermissionError("Plugin entry escapes the sandbox")
        if not resolved.is_file():
            raise FileNotFoundError(f"Plugin entry not found: {resolved}")
        if resolved.suffix.lower() not in {".py", ".json"}:
            raise PermissionError("Only JSON metadata or Python built-ins are allowed in MVP sandbox")

        if resolved.suffix.lower() == ".json":
            data = json.loads(resolved.read_text(encoding="utf-8"))
            return {"accepted": True, "target": target, "sandbox": "allowlist-json", "manifest": manifest, "payload": payload, "entryData": data}

        with tempfile.TemporaryDirectory(prefix="designatio-plugin-") as temp_dir:
            process_env = dict(os.environ)
            process_env["DESIGNATIO_PAYLOAD"] = json.dumps(payload, ensure_ascii=False)
            result = subprocess.run(
                [sys.executable, "-I", str(resolved)],
                cwd=temp_dir,
                env=process_env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        return {
            "accepted": result.returncode == 0,
            "target": target,
            "sandbox": "isolated-python-mvp",
            "returnCode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }

    def sandbox_policy(self) -> dict[str, Any]:
        return {
            "level": "bounded-process-mvp",
            "filesystem": "Entry and sandboxRoot must remain inside the plugin directory",
            "network": "Not explicitly isolated until an OS/container backend is active",
            "processTimeoutSeconds": 10,
            "allowedTargets": ["react", "flutter", "swiftui", "compose", "egui", "tauri", "html", "texture", "security"],
            "allowedEntries": [".json", ".py"],
            "osIsolation": "not-provided",
        }
