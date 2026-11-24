from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .figma import import_figma_json


def fetch_figma_file(file_key: str, token: str | None = None) -> dict[str, Any]:
    key = file_key.strip()
    if not key:
        raise ValueError("Figma file key is required")
    auth = (token or os.getenv("FIGMA_TOKEN") or "").strip()
    if not auth:
        raise ValueError(
            "Figma token is missing; configure it in Mnemosyne Settings or set FIGMA_TOKEN. "
            "Importing a local Figma JSON file does not require a token."
        )
    request = Request(
        f"https://api.figma.com/v1/files/{key}",
        headers={"X-Figma-Token": auth, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Figma API HTTP {error.code}: {error.read().decode('utf-8', 'replace')}") from error
    except URLError as error:
        raise RuntimeError(f"Figma API unavailable: {error.reason}") from error
    if not isinstance(data, dict):
        raise ValueError("Figma API response must be an object")
    return data


def import_figma_api(file_key: str, output_dir: str | Path, token: str | None = None, project_name: str | None = None) -> dict[str, Any]:
    data = fetch_figma_file(file_key, token)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source = output / "figma-api.json"
    source.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    report = import_figma_json(source, output, project_name)
    report["fileKey"] = file_key
    report["source"] = str(source.resolve())
    return report
