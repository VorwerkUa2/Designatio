# Designatio

**Універсальний MCP-інструмент для професійного продуктового дизайну, mockup-to-code та перевірки адаптивних інтерфейсів.**

Designatio routes design tasks to focused skills, validates results, and renders HTML/CSS or JSON design systems. It is designed to run with Claude Code, Mnemosyne, or another MCP host.

## MVP capabilities

- Analyze an uploaded screenshot or SVG path
- Produce a versioned design brief and design tokens
- Generate a responsive HTML/CSS implementation
- Route tasks between web, mobile, desktop, brand and texture skills
- Export machine-readable project state
- Serve tools through MCP JSON-RPC over stdio

## Installation

py -m designatio.cli screenshot output/site/index.html --output output/screens
py -m designatio.cli compare output/mockup.png output/screens/desktop.png --output output/comparison
```powershell
cd C:\Users\knyaz\Desktop\Designatio
py -m pip install -e ".[test,image]"
py -m pip install -e ".[vision,browser]"
```

## CLI

```powershell
py -m designatio.cli init --name "CRM Dashboard" --platform web --stack html
py -m designatio.cli analyze mockup.png --project output/project.json
py -m designatio.cli render output/project.json --output output/site
py -m designatio.cli render-react output/project.json --output output/react
py -m designatio.cli route "Create a responsive React dashboard"
```

## MCP

```powershell
py -m designatio.mcp.server
```

MCP tools:

- `design_create_brief`
- `design_analyze_mockup`
- `design_generate_system`
- `design_render`
- `design_check_accessibility`
- `design_check_responsive`
- `design_export`
- `design_route`

## Project state

The project JSON is the source of truth for brief, platform, stack, screens, components, tokens, assets, accessibility settings and validation reports.

