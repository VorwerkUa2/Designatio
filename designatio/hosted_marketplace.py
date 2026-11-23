from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading


NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


def validate_hosted_entry(entry: dict[str, Any]) -> dict[str, Any]:
    required = ["name", "version", "target", "entry", "bundle", "platforms"]
    missing = [field for field in required if field not in entry]
    errors = []
    if missing:
        errors.append(f"Missing fields: {', '.join(missing)}")
    name = str(entry.get("name", ""))
    if not NAME_PATTERN.fullmatch(name):
        errors.append("Name must contain 2-64 lowercase letters, digits or hyphens")
    if not isinstance(entry.get("platforms"), list) or not entry["platforms"]:
        errors.append("Platforms must be a non-empty array")
    target = entry.get("target")
    allowed = {"react", "flutter", "swiftui", "compose", "egui", "tauri", "html", "texture", "security"}
    if target not in allowed:
        errors.append("Target is not in the sandbox allowlist")
    return {"passed": not errors, "errors": errors, "entry": entry}


def create_hosted_index(entries: list[dict[str, Any]], output_path: str | Path) -> dict[str, Any]:
    validated = [validate_hosted_entry(entry) for entry in entries]
    invalid = [item for item in validated if not item["passed"]]
    if invalid:
        raise ValueError("Hosted marketplace contains invalid entries: " + json.dumps(invalid))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    index = {
        "schema": "1",
        "entries": [item["entry"] for item in validated],
    }
    output.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"index": str(output.resolve()), "count": len(validated)}


MARKETPLACE_SERVERS: dict[int, ThreadingHTTPServer] = {}


def start_marketplace_server(directory: str | Path, port: int = 4174) -> dict[str, Any]:
    root = Path(directory).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Marketplace directory not found: {root}")
    if port in MARKETPLACE_SERVERS:
        return {"running": True, "port": port, "url": f"http://127.0.0.1:{port}", "directory": str(root)}
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, name=f"designatio-marketplace-{port}", daemon=True)
    thread.start()
    MARKETPLACE_SERVERS[port] = server
    return {"running": True, "port": port, "url": f"http://127.0.0.1:{port}", "directory": str(root)}


def stop_marketplace_server(port: int) -> dict[str, Any]:
    server = MARKETPLACE_SERVERS.pop(port, None)
    if server is None:
        return {"running": False, "port": port}
    server.shutdown()
    server.server_close()
    return {"running": False, "port": port}
