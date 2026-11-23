from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class TrustStore:
    def __init__(self, store_dir: str | Path):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.store_dir / "trusted-keys.json"
        if not self.index_path.exists():
            self.index_path.write_text("{}", encoding="utf-8")

    def list(self) -> dict[str, Any]:
        return json.loads(self.index_path.read_text(encoding="utf-8-sig"))

    def add_public_key(self, name: str, public_path: str | Path, fingerprint: str | None = None) -> dict[str, Any]:
        public = Path(public_path)
        if not public.is_file():
            raise FileNotFoundError(f"Public key not found: {public}")
        public_key = serialization.load_pem_public_key(public.read_bytes())
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("Only Ed25519 public keys are supported")
        raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        computed = hashlib.sha256(raw).hexdigest()
        record = {
            "name": name,
            "algorithm": "Ed25519",
            "fingerprint": fingerprint or computed,
            "publicKey": str(public.resolve()),
        }
        index = self.list()
        index[name] = record
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def revoke(self, name: str) -> bool:
        index = self.list()
        removed = index.pop(name, None)
        if removed is not None:
            self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        return removed is not None

    def resolve(self, name: str) -> dict[str, Any] | None:
        return self.list().get(name)

    def verify_fingerprint(self, name: str, public_path: str | Path) -> bool:
        record = self.resolve(name)
        if record is None:
            return False
        public = Path(public_path)
        if not public.is_file():
            return False
        public_key = serialization.load_pem_public_key(public.read_bytes())
        if not isinstance(public_key, Ed25519PublicKey):
            return False
        raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return hashlib.sha256(raw).hexdigest() == record["fingerprint"]
