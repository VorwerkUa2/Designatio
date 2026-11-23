from __future__ import annotations

from typing import Any
import json


TAILWIND_SPACING = {
    4: "1", 8: "2", 12: "3", 16: "4", 20: "5", 24: "6", 32: "8", 40: "10",
    48: "12", 64: "16", 80: "20", 96: "24", 128: "32",
}


def nearest_tailwind(value: int, scale: dict[int, str] = TAILWIND_SPACING) -> str:
    nearest = min(scale, key=lambda candidate: abs(candidate - value))
    return scale[nearest]


def export_tailwind(project: dict[str, Any]) -> dict[str, Any]:
    tokens = project["tokens"]
    colors = tokens["colors"]
    spacing = tokens["spacing"]
    radius = tokens["radius"]
    return {
        "colors": {
            "brand": colors["primary"],
            "surface": colors["surface"],
            "content": colors["text"],
            "muted": colors["muted"],
            "border": colors["border"],
        },
        "spacing": {
            name: f"{nearest_tailwind(pixel)}"
            for name, pixel in spacing.items()
        },
        "radius": {
            name: f"{nearest_tailwind(pixel)}"
            for name, pixel in radius.items()
        },
        "classNameHints": {
            "shell": "mx-auto max-w-7xl",
            "header": "flex items-center justify-between gap-4",
            "grid": "grid grid-cols-1 md:grid-cols-2 gap-6",
            "card": "rounded-xl border bg-white p-6",
            "button": "min-h-11 rounded-xl px-6 font-bold",
        },
    }


def react_tailwind_source(project: dict[str, Any]) -> str:
    mapping = export_tailwind(project)
    cards = [
        component for component in project.get("components", [])
        if component.get("type") != "header"
    ]
    header = next((component for component in project.get("components", []) if component.get("type") == "header"), None)
    title = header.get("title", project["name"]) if header else project["name"]
    description = header.get("description", "") if header else ""
    card_markup = "\n".join(
        f'        <article className="{mapping["classNameHints"]["card"]}">'
        f'<h2 className="mb-3 text-xl font-bold">{component.get("title", "Card")}</h2>'
        f'<p className="text-slate-600">{component.get("description", "")}</p></article>'
        for component in cards
    )
    return f'''export default function App() {{
  return (
    <main className="{mapping["classNameHints"]["shell"]}">
      <header className="{mapping["classNameHints"]["header"]} mb-8">
        <div><h1 className="text-3xl font-bold">{title}</h1><p className="text-slate-600">{description}</p></div>
        <button className="{mapping["classNameHints"]["button"]}">Створити</button>
      </header>
      <section className="{mapping["classNameHints"]["grid"]}">
{card_markup}
      </section>
    </main>
  );
}}
'''
