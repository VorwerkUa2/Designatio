# Designatio

**Універсальний MCP-інструмент для професійного продуктового дизайну, mockup-to-code та перевірки адаптивних інтерфейсів.**

Designatio routes design tasks to focused skills, validates results, and renders HTML/CSS or JSON design systems. It is designed to run with Claude Code, Mnemosyne, or another MCP host.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](#)
[![React](https://img.shields.io/badge/React-Vite-blue.svg)](#)

## MVP capabilities

- Analyze an uploaded screenshot or SVG path
- Produce a versioned design brief and design tokens
- Generate a responsive HTML/CSS implementation
- Route tasks between web, mobile, desktop, brand and texture skills
- Export machine-readable project state
- Serve tools through MCP JSON-RPC over stdio
- Extract text and layout zones from screenshots
- Capture desktop/tablet/mobile screenshots in Chromium
- Generate pixel diffs and React implementations

## Installation
```powershell
cd C:\Users\knyaz\Desktop\Designatio
py -m pip install -e ".[test,image,vision,browser]"
```

## CLI

```powershell
py -m designatio.cli init --name "CRM Dashboard" --platform web --stack html
py -m designatio.cli analyze mockup.png --project output/project.json
py -m designatio.cli render output/project.json --output output/site
py -m designatio.cli render-react output/project.json --output output/react
py -m designatio.cli route "Create a responsive React dashboard"
py -m designatio.cli pipeline mockup.png --name "CRM Dashboard" --output output/pipeline
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
- `design_take_screenshots`
- `design_compare`
- `design_render_react`
- `design_run_pipeline`

## End-to-end pipeline

`design_run_pipeline` executes the local workflow:

1. Create a versioned project
2. Analyze the screenshot with Pillow, OpenCV and Tesseract
3. Infer header/card component hints and palette
4. Render HTML or React
5. Capture screenshots at 1440/1024/768/390 px
6. Check accessibility and responsive structure
7. Compare the implementation against the source mockup

## Project state

The project JSON is the source of truth for brief, platform, stack, screens, components, tokens, assets, accessibility settings and validation reports.

