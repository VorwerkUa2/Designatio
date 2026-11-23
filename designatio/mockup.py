from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import json
import struct

from .layout import extract_layout


def infer_components(analysis: dict[str, Any], project_name: str) -> list[dict[str, Any]]:
    detected = analysis.get("detected", {})
    text_items = detected.get("text", {}).get("items", [])
    zones = detected.get("zones", [])

    components: list[dict[str, Any]] = []
    header_items = [
        item for item in text_items
        if item["box"]["y"] < analysis["source"].get("height", 100000) * 0.25
    ]
    if header_items:
        header_title = " ".join(item["text"] for item in header_items[:4])
        remaining = " ".join(item["text"] for item in header_items[4:8])
    else:
        header_title = project_name
        remaining = "Production-ready responsive interface"
    components.append({
        "type": "header",
        "title": header_title[:120],
        "description": remaining[:240],
    })

    card_zones = [zone for zone in zones if zone["type"] == "card"][:6]
    used_boxes: set[int] = set()
    for index, zone in enumerate(card_zones, start=1):
        box = zone["box"]
        title_parts: list[str] = []
        description_parts: list[str] = []
        for item in text_items:
            item_box = item["box"]
            inside = (
                item_box["x"] >= box["x"] - 12
                and item_box["y"] >= box["y"] - 12
                and item_box["x"] + item_box["width"] <= box["x"] + box["width"] + 12
                and item_box["y"] + item_box["height"] <= box["y"] + box["height"] + 12
            )
            if inside:
                text = item["text"]
                text_id = id(item)
                if text_id not in used_boxes:
                    used_boxes.add(text_id)
                    if len(title_parts) < 3:
                        title_parts.append(text)
                    else:
                        description_parts.append(text)

        if title_parts or description_parts:
            components.append({
                "type": "card",
                "title": " ".join(title_parts[:3])[:120] or f"Card {index}",
                "description": " ".join(description_parts[:18])[:240],
            })

    if len(components) == 1:
        components.extend([
            {"type": "card", "title": "Primary overview", "description": "Production-ready content"},
            {"type": "card", "title": "Supporting details", "description": "Accessible and responsive details"},
        ])
    return components


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
            quantized = sampled.quantize(colors=8)
            raw_palette = quantized.getpalette() or []
            palette = [
                f"#{raw_palette[index]:02X}{raw_palette[index + 1]:02X}{raw_palette[index + 2]:02X}"
                for index in range(0, min(len(raw_palette), 24), 3)
            ]
            palette = list(dict.fromkeys(palette))
    except (ImportError, OSError, ValueError):
        pass

    try:
        layout = extract_layout(source)
    except (OSError, ValueError):
        layout = {
            "available": False,
            "layout": "unknown",
            "zones": [],
            "componentHints": {},
            "text": {"blocks": [], "items": [], "count": 0},
            "ocrError": "The source file could not be decoded as an image",
        }

    components = infer_components({
        "source": metadata,
        "detected": {
            "layout": layout.get("layout", "unknown"),
            "text": layout.get("text", {}),
            "zones": layout.get("zones", []),
            "componentHints": layout.get("componentHints", {}),
        },
    }, metadata["name"])

    return {
        "source": metadata,
        "mode": mode,
        "components": components,
        "detected": {
            "layout": layout.get("layout", "unknown"),
            "components": [
                {"type": kind, "count": count}
                for kind, count in layout.get("componentHints", {}).items()
                if count
            ],
            "text": layout.get("text", {}),
            "zones": layout.get("zones", []),
            "typography": "requires font identification" if not layout.get("text", {}).get("items") else "text regions detected",
            "colors": palette,
            "visionAvailable": layout.get("available", False),
            "ocrError": layout.get("ocrError"),
        },
        "issues": issues,
        "nextActions": [
            "Review image composition and hierarchy",
            "Extract or confirm design tokens",
            "Generate responsive component structure",
            "Render and compare at desktop, tablet and mobile widths",
        ],
    }
