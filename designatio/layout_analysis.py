from __future__ import annotations

from typing import Any


def merge_reading_order(text_items: list[dict[str, Any]], tolerance: int = 14) -> list[str]:
    by_row: list[list[dict[str, Any]]] = []
    for item in sorted(text_items, key=lambda value: (value["box"]["y"], value["box"]["x"])):
        box = item["box"]
        row = next((row for row in by_row if abs(row[0]["box"]["y"] - box["y"]) <= tolerance), None)
        if row is None:
            by_row.append([item])
        else:
            row.append(item)
    return [
        " ".join(item["text"] for item in sorted(row, key=lambda value: value["box"]["x"]))
        for row in by_row
    ]


def detect_grid(zones: list[dict[str, Any]], width: int, height: int) -> dict[str, Any]:
    boxes = [zone["box"] for zone in zones]
    xs = sorted({box["x"] for box in boxes})
    ys = sorted({box["y"] for box in boxes})
    gaps_x = [right - left for left, right in zip(xs, xs[1:])]
    gaps_y = [right - left for left, right in zip(ys, ys[1:])]
    repeated_x = len(gaps_x) >= 2 and max(gaps_x) - min(gaps_x) <= max(24, width * 0.04)
    repeated_y = len(gaps_y) >= 2 and max(gaps_y) - min(gaps_y) <= max(24, height * 0.04)
    return {
        "columns": len(set(round(box["x"] / max(width / 12, 1)) for box in boxes)),
        "rows": len(set(round(box["y"] / max(height / 12, 1)) for box in boxes)),
        "anchors": {"x": xs[:12], "y": ys[:12]},
        "consistent": repeated_x or repeated_y,
        "grid": "12-column" if width >= 1024 and repeated_x else "flow",
    }
