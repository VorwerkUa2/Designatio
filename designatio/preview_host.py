from __future__ import annotations

from pathlib import Path
from typing import Any
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading


SERVERS: dict[int, ThreadingHTTPServer] = {}


def start_preview_server(preview_dir: str | Path, port: int = 4173) -> dict[str, Any]:
    directory = Path(preview_dir).resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"Preview directory not found: {directory}")
    if port in SERVERS:
        return {"running": True, "port": port, "url": f"http://127.0.0.1:{port}", "directory": str(directory)}

    dist = directory / "dist"
    root = dist if dist.is_dir() else directory
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, name=f"designatio-preview-{port}", daemon=True)
    thread.start()
    SERVERS[port] = server
    return {"running": True, "port": port, "url": f"http://127.0.0.1:{port}", "directory": str(root)}


def stop_preview_server(port: int) -> dict[str, Any]:
    server = SERVERS.pop(port, None)
    if server is None:
        return {"running": False, "port": port}
    server.shutdown()
    server.server_close()
    return {"running": False, "port": port}
