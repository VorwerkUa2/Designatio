from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json


DEFAULT_TOKENS = {
    "colors": {
        "background": "#F5F7FB",
        "surface": "#FFFFFF",
        "text": "#172033",
        "muted": "#667085",
        "primary": "#4F46E5",
        "primaryContrast": "#FFFFFF",
        "border": "#E4E7EC",
        "success": "#16834B",
        "warning": "#B54708",
        "danger": "#B42318",
    },
    "typography": {
        "fontFamily": "Inter, system-ui, -apple-system, \"Segoe UI\", sans-serif",
        "baseSize": 16,
        "headingWeight": 700,
    },
    "spacing": {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "xxl": 48},
    "radius": {"sm": 8, "md": 12, "lg": 16, "full": 999},
}


def create_project(
    name: str = "Untitled design",
    platform: str = "web",
    stack: str = "html",
    brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    platform = platform.lower().strip()
    stack = stack.lower().strip()
    return {
        "schemaVersion": "1",
        "name": name,
        "brief": brief or {
            "goal": "",
            "audience": [],
            "tone": [],
            "requirements": [],
            "constraints": [],
            "mode": "modernized",
        },
        "platform": platform,
        "stack": stack,
        "screens": [],
        "components": [],
        "tokens": deepcopy(DEFAULT_TOKENS),
        "assets": [],
        "accessibility": {
            "target": "WCAG 2.2 AA",
            "contrastMinimum": 4.5,
            "keyboardRequired": True,
        },
        "preview": {},
        "reports": [],
        "history": [],
    }


def load_project(path: str | Path) -> dict[str, Any]:
    project_path = Path(path)
    with project_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Project root must be a JSON object")
    return data


def save_project(project: dict[str, Any], path: str | Path) -> Path:
    project_path = Path(path)
    project_path.parent.mkdir(parents=True, exist_ok=True)
    with project_path.open("w", encoding="utf-8") as handle:
        json.dump(project, handle, ensure_ascii=False, indent=2)
    return project_path
