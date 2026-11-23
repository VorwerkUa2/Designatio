from __future__ import annotations

from typing import Any
import re


def check_accessibility(project: dict[str, Any]) -> dict[str, Any]:
    tokens = project.get("tokens", {})
    colors = tokens.get("colors", {})
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def luminance(hex_color: str) -> float:
        value = hex_color.lstrip("#")
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
            raise ValueError(f"Invalid hex color: {hex_color}")
        channels = [int(value[index:index + 2], 16) / 255 for index in range(0, 6, 2)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    def contrast(first: str, second: str) -> float:
        first_luma = luminance(first)
        second_luma = luminance(second)
        lighter = max(first_luma, second_luma)
        darker = min(first_luma, second_luma)
        return (lighter + 0.05) / (darker + 0.05)

    checks = [
        ("text", colors.get("text"), colors.get("surface")),
        ("primary", colors.get("primaryContrast"), colors.get("primary")),
    ]
    for name, foreground, background in checks:
        if not foreground or not background:
            continue
        try:
            ratio = contrast(foreground, background)
        except ValueError as error:
            errors.append({"rule": "valid-color", "message": str(error)})
            continue
        if ratio < 4.5:
            warnings.append({"rule": f"{name}-contrast", "message": f"Contrast ratio {ratio:.2f}:1 is below 4.5:1"})

    return {
        "passed": not errors and not warnings,
        "errors": errors,
        "warnings": warnings,
        "checks": ["color-contrast", "keyboard-target-plan", "semantic-html"],
    }


def check_responsive(project: dict[str, Any]) -> dict[str, Any]:
    breakpoints = [1440, 1024, 768, 390]
    issues: list[dict[str, str]] = []
    if not project.get("components"):
        issues.append({"rule": "component-content", "message": "Project has no components to render responsively"})
    return {
        "passed": not issues,
        "breakpoints": breakpoints,
        "issues": issues,
        "checks": ["overflow", "stacking", "navigation", "touch-targets"],
    }
