from __future__ import annotations

from pathlib import Path
from typing import Any
import html


def render_html(project: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    tokens = project["tokens"]
    colors = tokens["colors"]
    typography = tokens["typography"]
    spacing = tokens["spacing"]
    radius = tokens["radius"]
    title = html.escape(project["name"])

    components = project.get("components") or [
        {"type": "header", "title": project["name"], "description": "Production-ready responsive interface"},
        {"type": "card", "title": "Primary overview", "description": "Start with real content and component states."},
        {"type": "card", "title": "Accessible by default", "description": "Semantic structure, contrast and keyboard support."},
    ]

    cards = []
    for component in components:
        if component.get("type") in {"header"}:
            continue
        cards.append(
            f"""<article class="card">
  <h2>{html.escape(str(component.get("title", "Component")))}</h2>
  <p>{html.escape(str(component.get("description", "")))}</p>
</article>"""
        )

    header = next((item for item in components if item.get("type") == "header"), None)
    header_title = header["title"] if header else project["name"]
    header_description = header.get("description", "") if header else ""

    document = f"""<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --background: {colors["background"]};
      --surface: {colors["surface"]};
      --text: {colors["text"]};
      --muted: {colors["muted"]};
      --primary: {colors["primary"]};
      --primary-contrast: {colors["primaryContrast"]};
      --border: {colors["border"]};
      --space-md: {spacing["md"]}px;
      --space-lg: {spacing["lg"]}px;
      --space-xl: {spacing["xl"]}px;
      --radius-md: {radius["md"]}px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--background);
      color: var(--text);
      font-family: {typography["fontFamily"]};
      font-size: {typography["baseSize"]}px;
    }}
    .shell {{ max-width: 1280px; margin: 0 auto; padding: var(--space-xl); }}
    .header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-md);
      margin-bottom: var(--space-xl);
    }}
    .header p {{ color: var(--muted); margin: 8px 0 0; }}
    .action {{
      border: 0;
      border-radius: var(--radius-md);
      background: var(--primary);
      color: var(--primary-contrast);
      min-height: 44px;
      padding: 0 var(--space-lg);
      font-weight: 700;
      cursor: pointer;
    }}
    .action:focus-visible {{ outline: 3px solid #98A2B3; outline-offset: 3px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--space-lg);
    }}
    .card {{
      min-height: 180px;
      padding: var(--space-lg);
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
    }}
    .card h2 {{ margin: 0 0 12px; font-size: 20px; }}
    .card p {{ color: var(--muted); line-height: 1.6; margin: 0; }}
    @media (max-width: 768px) {{
      .shell {{ padding: var(--space-lg) var(--space-md); }}
      .header {{ align-items: flex-start; flex-direction: column; }}
      .grid {{ grid-template-columns: 1fr; }}
      .action {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="header">
      <div>
        <h1>{html.escape(str(header_title))}</h1>
        <p>{html.escape(str(header_description))}</p>
      </div>
      <button class="action" type="button">Створити</button>
    </header>
    <section class="grid" aria-label="Основний вміст">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""
    index = output / "index.html"
    index.write_text(document, encoding="utf-8")

    export = dict(project)
    export["preview"] = {
        "html": str(index.resolve()),
        "breakpoints": [1440, 1024, 768, 390],
    }
    return export
