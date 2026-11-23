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
- Resolve 27 programming languages to UI frameworks, graphics engines and preview methods

## Language and graphics catalog

Designatio includes a built-in registry for JavaScript, TypeScript, Python, Dart,
Rust, C#, Java, Kotlin, Swift, Objective-C, C++, C, Go, PHP, Ruby, Elixir,
Scala, Haskell, Lua, R, Julia, Zig, Nim, Crystal, F#, Groovy and Visual Basic.

The catalog covers web UI, native desktop/mobile UI, game engines, 2D/3D graphics,
canvas, SVG, Skia, Cairo, OpenGL, Vulkan, DirectX, Metal, WebGPU, WGPU, Qt,
Flutter, Compose, SwiftUI, egui, React, Vue, Angular, Dear ImGui, Three.js,
Babylon.js, PixiJS, Pygame, Raylib, SDL and many framework-specific libraries.

```powershell
py -m designatio.cli catalog
py -m designatio.cli catalog --language rust
py -m designatio.cli resolve-stack "Create a C++ Qt app with OpenGL"
py -m designatio.cli render-native flutter output/project.json --output output/flutter
py -m designatio.cli render-native swiftui output/project.json --output output/swiftui
py -m designatio.cli render-native compose output/project.json --output output/compose
py -m designatio.cli render-native egui output/project.json --output output/egui
py -m designatio.cli import-figma figma-screen.json --name "Dashboard" --output output/figma
```

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
py -m designatio.cli catalog
py -m designatio.cli catalog --language swift
py -m designatio.cli resolve-stack "Create a native C++ Qt app with OpenGL"
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
- `design_list_languages`
- `design_resolve_stack`

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
