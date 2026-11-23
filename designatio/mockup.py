from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import json
import struct


def image_metadata(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Mockup not found: {source}")

    metadata: dict[str, Any] = {
        "path": str(source.resolve()),
        "name": source.name,
        "extension": source.suffix.lower(),
        "sizeBytes": source.stat().st_size,
    }

    if source.suffix.lower() == ".png":
        with source.open("rb") as handle:
            header = handle.read(24)
        if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
            metadata["width"] = struct.unpack(">I", header[16:20])[0]
            metadata["height"] = struct.unpack(">I", header[20:24])[0]

    if source.suffix.lower() in {".svg", ".svgz"}:
        try:
            text = source.read_text(encoding="utf-8")
            metadata["inlineSvg"] = len(text) <= 64_000
        except (UnicodeDecodeError, OSError):
            metadata["inlineSvg"] = False

    try:
        from PIL import Image

        with Image.open(source) as image:
            metadata.setdefault("width", image.width)
            metadata.setdefault("height", image.height)
            metadata["format"] = image.format
    except ImportError:
        pass
    except (OSError, ValueError):
        pass

    return metadata


def analyze_mockup(path: str | Path, mode: str = "modernized") -> dict[str, Any]:
    source = Path(path)
    metadata = image_metadata(path)
    width = metadata.get("width")
    height = metadata.get("height")

    issues: list[dict[str, str]] = []
    if width and height and width > 1920:
        issues.append({"severity": "medium", "rule": "source-size", "message": "Use 1x/2x exports instead of a single oversized source"})
    if width and height and width < 390:
        issues.append({"severity": "low", "rule": "source-width", "message": "Source mockup is narrower than a standard mobile layout"})

    palette: list[str] = []
    try:
        from PIL import Image

        with Image.open(source) as image:
            rgb = image.convert("RGB")
            sampled = rgb.resize((64, 64))
            palette = [f"#{red:02X}{green:02X}{blue:02X}" for red, green, blue in sampled.quantize(colors=8).getpalette()[:24]]
            palette = list(dict.fromkeys(palette))
    except (ImportError, OSError, ValueError):
        pass

    return {
        "source": metadata,
        "mode": mode,
        "detected": {
            "layout": "unknown",
            "components": [],
            "typography": "requires image OCR/layout detection",
            "colors": palette,
        },
        "issues": issues,
        "nextActions": [
            "Review image composition and hierarchy",
            "Extract or confirm design tokens",
            "Generate responsive component structure",
            "Render and compare at desktop, tablet and mobile widths",
        ],
    }
