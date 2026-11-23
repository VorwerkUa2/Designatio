from __future__ import annotations

import re
from typing import Any


SKILLS = {
    "design-discovery": ("brief", ["discover", "brief", "requirement", "briefing"]),
    "ui-web": ("web", ["website", "web", "dashboard", "landing", "react", "html"]),
    "ui-mobile": ("mobile", ["mobile", "ios", "android", "flutter", "react native"]),
    "ui-desktop": ("desktop", ["desktop", "tauri", "egui", "windows", "mac", "linux"]),
    "mockup-to-code": ("implementation", ["mockup", "screenshot", "png", "figma", "pixel", "make real"]),
    "design-system": ("foundation", ["design system", "tokens", "components", "typography"]),
    "accessibility": ("validation", ["accessibility", "contrast", "wcag", "keyboard"]),
    "responsive": ("validation", ["responsive", "mobile", "breakpoint", "overflow"]),
    "texture": ("assets", ["texture", "pbr", "seamless", "normal map", "material"]),
}


def route_task(prompt: str) -> dict[str, Any]:
    text = prompt.lower()
    matched: list[str] = []
    for skill_name, (_category, keywords) in SKILLS.items():
        if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
            matched.append(skill_name)

    if not matched:
        matched = ["design-discovery", "ui-web"]

    if "mockup" in text or ".png" in text or ".jpg" in text or ".webp" in text:
        matched.append("mockup-to-code")
    if "accessible" in text or "wcag" in text:
        matched.append("accessibility")

    matched = list(dict.fromkeys(matched))
    return {
        "profiles": matched,
        "skills": [{"name": name, "category": SKILLS[name][0]} for name in matched],
        "mode": "plan" if "plan" in text else "turbo",
    }
