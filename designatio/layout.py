from __future__ import annotations

from pathlib import Path
from typing import Any


def _tesseract_candidates() -> tuple[str, ...]:
    return (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    )


def extract_layout(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Mockup not found: {source}")

    try:
        import cv2
        import numpy as np
        import pytesseract
        from PIL import Image
    except ImportError as error:
        return {"available": False, "error": f"Vision dependency missing: {error.name}"}

    pytesseract.pytesseract.tesseract_cmd = next(
        (candidate for candidate in _tesseract_candidates() if Path(candidate).is_file()),
        "tesseract",
    )

    try:
        with Image.open(source).convert("RGB") as pil_image:
            width, height = pil_image.size
            image = np.asarray(pil_image)[:, :, ::-1].copy()
    except (OSError, ValueError) as error:
        return {
            "available": False,
            "layout": "unknown",
            "zones": [],
            "componentHints": {},
            "text": {"blocks": [], "items": [], "count": 0},
            "ocrError": str(error),
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    zones: list[dict[str, Any]] = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        area = float(cv2.contourArea(contour))
        if area < (width * height * 0.001):
            continue
        x, y, box_width, box_height = cv2.boundingRect(contour)
        if box_width < 24 or box_height < 24:
            continue

        kind = "section"
        if box_width > width * 0.8 and y < height * 0.3:
            kind = "header"
        elif box_width < width * 0.25 and box_height > height * 0.45:
            kind = "sidebar"
        elif box_width < width * 0.42 and box_height < height * 0.35:
            kind = "card"

        zones.append({
            "type": kind,
            "box": {"x": int(x), "y": int(y), "width": int(box_width), "height": int(box_height)},
            "area": int(area),
        })
        if len(zones) >= 40:
            break

    text_items: list[dict[str, Any]] = []
    text_blocks: list[str] = []
    ocr_error = None
    try:
        data = pytesseract.image_to_data(
            pil_image,
            lang="eng+ukr",
            config="--psm 11",
            output_type=pytesseract.Output.DICT,
        )
        for index, text in enumerate(data["text"]):
            cleaned = text.strip()
            confidence = float(data["conf"][index])
            if not cleaned or confidence < 45:
                continue
            text_blocks.append(cleaned)
            text_items.append({
                "text": cleaned,
                "confidence": round(confidence, 1),
                "box": {
                    "x": int(data["left"][index]),
                    "y": int(data["top"][index]),
                    "width": int(data["width"][index]),
                    "height": int(data["height"][index]),
                },
            })
    except Exception as error:
        ocr_error = str(error)

    component_types = {
        "header": sum(zone["type"] == "header" for zone in zones),
        "sidebar": sum(zone["type"] == "sidebar" for zone in zones),
        "card": sum(zone["type"] == "card" for zone in zones),
        "section": sum(zone["type"] == "section" for zone in zones),
    }

    if width >= height:
        layout = "desktop" if width >= 1024 else "tablet"
    else:
        layout = "mobile"

    return {
        "available": True,
        "layout": layout,
        "canvas": {"width": width, "height": height},
        "text": {
            "blocks": text_blocks[:200],
            "items": text_items[:500],
            "count": len(text_items),
        },
        "zones": zones,
        "componentHints": component_types,
        "ocrError": ocr_error,
    }
