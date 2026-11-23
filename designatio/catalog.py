from __future__ import annotations

from typing import Any
import re


LANGUAGES: dict[str, dict[str, Any]] = {
    "javascript": {
        "aliases": ["js", "node", "nodejs", "ecmascript"],
        "platforms": ["web", "desktop", "mobile", "server"],
        "frameworks": ["React", "Next.js", "Vue", "Nuxt", "Svelte", "SvelteKit", "Solid", "Angular", "Astro", "Electron", "Tauri", "React Native", "Expo", "Capacitor", "Ionic", "Vanilla JS"],
        "graphics": ["HTML Canvas", "SVG", "WebGL", "WebGPU", "Three.js", "Babylon.js", "PixiJS", "Two.js", "Fabric.js", "Konva", "P5.js", "Paper.js", "Phaser", "GSAP", "Framer Motion", "React Spring", "Lottie"],
        "preview": ["Browser", "Playwright", "Electron", "React Native"],
    },
    "typescript": {
        "aliases": ["ts", "tsx", "typescript react"],
        "platforms": ["web", "desktop", "mobile", "server"],
        "frameworks": ["React", "Next.js", "Vue", "Nuxt", "Svelte", "SvelteKit", "Solid", "Angular", "Astro", "Electron", "Tauri", "React Native", "Expo", "NestJS", "Angular Universal"],
        "graphics": ["HTML Canvas", "SVG", "WebGL", "WebGPU", "Three.js", "Babylon.js", "PixiJS", "Konva", "Fabric.js", "P5.js", "GSAP", "Framer Motion", "React Spring", "Lottie"],
        "preview": ["Browser", "Playwright", "Electron", "React Native"],
    },
    "python": {
        "aliases": ["py", "cpython"],
        "platforms": ["desktop", "web", "data", "graphics", "server"],
        "frameworks": ["PyQt", "PySide", "Qt", "Tkinter", "CustomTkinter", "wxPython", "Kivy", "PySimpleGUI", "Dear PyGui", "Flet", "Streamlit", "Gradio", "NiceGUI", "Dash", "Reflex", "FastHTML"],
        "graphics": ["Pillow", "OpenCV", "Matplotlib", "Seaborn", "Plotly", "Bokeh", "Altair", "VisPy", "Pygame", "Panda3D", "Moderngl", "PyOpenGL", "Cairo", "QPainter", "Skia", "imageio", "NumPy"],
        "preview": ["Qt", "Browser", "Kivy", "Pygame", "Desktop screenshot"],
    },
    "dart": {
        "aliases": ["dartlang", "flutter"],
        "platforms": ["mobile", "web", "desktop"],
        "frameworks": ["Flutter", "Dart Frog", "Flame", "Shelf"],
        "graphics": ["Flutter Canvas", "CustomPainter", "Skia", "Impeller", "Flame", "Rive", "Lottie", "Vector Graph", "Shaders"],
        "preview": ["Flutter", "Browser", "Android", "iOS", "Desktop"],
    },
    "rust": {
        "aliases": ["rs", "cargo"],
        "platforms": ["desktop", "web", "game", "graphics", "embedded"],
        "frameworks": ["egui", "eframe", "iced", "Dioxus", "Tauri", "Slint", "Relm4", "Leptos", "Yew", "Bevy UI"],
        "graphics": ["wgpu", "Winit", "Pixels", "Renaissance", "Cairo", "Skia", "tiny-skia", "softbuffer", "Vello", "Kanvas", "Nannou", "Macroquad", "Minifb", "Bevy", "gfx-rs", "Luminance"],
        "preview": ["egui", "Tauri", "Browser", "Bevy", "Native desktop"],
    },
    "csharp": {
        "aliases": ["c#", "dotnet", ".net", "asp.net"],
        "platforms": ["desktop", "mobile", "web", "game", "embedded"],
        "frameworks": ["WPF", "WinUI", "MAUI", "Avalonia", "Uno Platform", "Xamarin", "Blazor", "ASP.NET", "MudBlazor", "Syncfusion", "Telerik"],
        "graphics": ["SkiaSharp", "WPF 2D/3D", "DirectX", "Direct2D", "Win2D", "Silk.NET", "Veldrid", "MonoGame", "Stride", "Unity UI", "OpenTK", "SixLabors.ImageSharp", "Helix Toolkit"],
        "preview": ["Desktop", "Browser", "MAUI", "Unity", "Godot"],
    },
    "java": {
        "aliases": ["javafx", "jdk", "jvm"],
        "platforms": ["desktop", "mobile", "web", "game", "server"],
        "frameworks": ["JavaFX", "Swing", "SWT", "Vaadin", "Spring", "LibGDX", "Java2D", "OpenJFX"],
        "graphics": ["Java2D", "JavaFX 2D/3D", "AWT", "LWJGL", "LibGDX", "JOGL", "JMonkeyEngine", "FXGL", "Apache Batik", "TwelveMonkeys"],
        "preview": ["Desktop", "Browser", "Android", "LibGDX"],
    },
    "kotlin": {
        "aliases": ["kt", "kmp", "compose"],
        "platforms": ["android", "desktop", "mobile", "web"],
        "frameworks": ["Jetpack Compose", "Compose Multiplatform", "Android XML", "Kotlin/JS", "Ktor", "KVision", "KMP"],
        "graphics": ["Skia", "Canvas", "Android Canvas", "Compose Graphics", "LWJGL", "LibGDX", "Kotlin SVG", "Lottie"],
        "preview": ["Android", "Desktop", "Browser", "Compose Multiplatform"],
    },
    "swift": {
        "aliases": ["swiftui", "uikit", "ios", "macos"],
        "platforms": ["ios", "macos", "watchos", "tvos", "visionos"],
        "frameworks": ["SwiftUI", "UIKit", "AppKit", "RealityKit", "Core Graphics", "WidgetKit"],
        "graphics": ["Core Graphics", "Core Image", "Core Animation", "Metal", "MetalKit", "SceneKit", "SpriteKit", "RealityKit", "Vision", "Lottie", "SF Symbols"],
        "preview": ["iOS Simulator", "macOS", "SwiftUI Preview"],
    },
    "objective-c": {
        "aliases": ["objc", "objectivec"],
        "platforms": ["ios", "macos"],
        "frameworks": ["UIKit", "AppKit", "Cocoa", "Cocoa Touch"],
        "graphics": ["Core Graphics", "Core Animation", "Core Image", "Metal", "SceneKit", "SpriteKit"],
        "preview": ["iOS Simulator", "macOS"],
    },
    "cpp": {
        "aliases": ["c++", "cpp", "qt/c++"],
        "platforms": ["desktop", "game", "graphics", "embedded", "mobile"],
        "frameworks": ["Qt", "Qt Quick", "Qt Widgets", "Dear ImGui", "FLTK", "wxWidgets", "JUCE", "GTK", "SFML", "SDL", "Unreal UI"],
        "graphics": ["Qt Quick", "Qt Painter", "OpenGL", "Vulkan", "DirectX", "Metal", "SDL", "SDL_ttf", "SFML", "Skia", "Cairo", "NanoVG", "Dear ImGui", "ImPlot", "OpenSceneGraph", "Unreal Engine", "Unreal Slate"],
        "preview": ["Qt", "Native desktop", "Engine viewport", "SDL"],
    },
    "c": {
        "aliases": ["ansi c", "clang", "gcc"],
        "platforms": ["desktop", "embedded", "graphics", "game"],
        "frameworks": ["GTK", "IUP", "nCurses", "Raylib", "SDL", "GLFW", "EFL"],
        "graphics": ["Cairo", "Pango", "Skia", "SDL", "SDL2", "SDL3", "GLFW", "OpenGL", "Vulkan", "Raylib", "Allegro", "Xlib", "Wayland", "NanoVG"],
        "preview": ["Native desktop", "Raylib", "SDL"],
    },
    "go": {
        "aliases": ["golang"],
        "platforms": ["desktop", "web", "server", "game"],
        "frameworks": ["Fyne", "Wails", "Gio", "Lorca", "Ebiten", "Pixel", "Hugo"],
        "graphics": ["Fyne Canvas", "Gio", "Ebiten", "Pixel", "gg", "Cairo", "OpenGL", "Ebitengine", "WebGPU", "Lottie"],
        "preview": ["Native desktop", "Browser", "Wails", "Ebiten"],
    },
    "php": {
        "aliases": ["php"],
        "platforms": ["web", "server"],
        "frameworks": ["Laravel", "Livewire", "Inertia", "Symfony", "Blade", "Filament", "Twig"],
        "graphics": ["SVG", "Canvas", "GD", "ImageMagick", "Intervention Image", "Chart.js", "Plotly"],
        "preview": ["Browser", "Playwright"],
    },
    "ruby": {
        "aliases": ["rb", "rails"],
        "platforms": ["web", "server", "desktop"],
        "frameworks": ["Rails", "Hotwire", "Turbo", "Stimulus", "ViewComponent", "Shoes", "RubyGnome"],
        "graphics": ["SVG", "RMagick", "ImageMagick", "Cairo", "Processing", "Chartkick"],
        "preview": ["Browser", "Playwright"],
    },
    "elixir": {
        "aliases": ["ex", "exs"],
        "platforms": ["web", "server", "desktop"],
        "frameworks": ["Phoenix", "Phoenix LiveView", "Surface", "Scenic", "Ash"],
        "graphics": ["SVG", "Canvas", "Scenic", "Image", "VegaLite"],
        "preview": ["Browser", "LiveView", "Scenic"],
    },
    "scala": {
        "aliases": ["sbt"],
        "platforms": ["web", "desktop", "server"],
        "frameworks": ["Scala.js", "Laminar", "Scalatags", "ScalaFX", "Play", "ZIO"],
        "graphics": ["ScalaFX", "JavaFX", "Canvas", "SVG", "LWJGL"],
        "preview": ["Browser", "Desktop"],
    },
    "haskell": {
        "aliases": ["hs", "ghc"],
        "platforms": ["desktop", "web", "graphics"],
        "frameworks": ["Threepenny", "Reflex", "Miscaro", "Gloss", "Diagrams", "Gtk"],
        "graphics": ["Gloss", "Diagrams", "Chart", "Cairo", "SDL", "OpenGL", "Vulkan"],
        "preview": ["Browser", "Desktop"],
    },
    "lua": {
        "aliases": ["luau", "love"],
        "platforms": ["game", "embedded", "graphics"],
        "frameworks": ["LÖVE", "Solar2D", "LOVE2D", "Defold", "Ren'Py"],
        "graphics": ["LÖVE", "Raylib", "Love2D", "Cairo", "SDL", "OpenGL", "Defold GUI", "Roblox UI"],
        "preview": ["Engine viewport", "Desktop", "Mobile"],
    },
    "r": {
        "aliases": ["rlang"],
        "platforms": ["data", "web", "graphics"],
        "frameworks": ["Shiny", "bslib", "Flexdashboard", "Quarto", "R Markdown"],
        "graphics": ["ggplot2", "plotly", "lattice", "rgl", "highcharter", "leaflet", "gt"],
        "preview": ["Browser", "RStudio", "Quarto"],
    },
    "julia": {
        "aliases": ["jl"],
        "platforms": ["data", "web", "graphics", "scientific"],
        "frameworks": ["Makie", "GLMakie", "CairoMakie", "WGLMakie", "Pluto", "Dash.jl", "Genie"],
        "graphics": ["Makie", "Cairo", "Plots", "Gadfly", "Vega", "Luxor", "GLMakie", "WebGL"],
        "preview": ["Browser", "Desktop", "Notebook"],
    },
    "zig": {
        "aliases": ["ziglang"],
        "platforms": ["desktop", "game", "graphics", "embedded"],
        "frameworks": ["Mach", "Raylib Zig", "SDL Zig", "Tink", "Kap"],
        "graphics": ["Mach", "Raylib", "SDL", "OpenGL", "Vulkan", "WebGPU", "wgpu", "Cairo"],
        "preview": ["Native desktop", "Browser", "Game engine"],
    },
    "nim": {
        "aliases": ["nimlang"],
        "platforms": ["desktop", "game", "web"],
        "frameworks": ["Nimble", "Karax", "Prologue", "NFL", "Nimx"],
        "graphics": ["SDL", "Raylib", "OpenGL", "Vulkan", "Cairo", "Skia", "ImGui"],
        "preview": ["Browser", "Desktop"],
    },
    "crystal": {
        "aliases": ["cr"],
        "platforms": ["desktop", "web", "server"],
        "frameworks": ["Lucky", "Amber", "Kemal", "TIDCrystal"],
        "graphics": ["SVG", "Cairo", "SDL", "OpenGL", "CrystalChart"],
        "preview": ["Browser", "Desktop"],
    },
    "fsharp": {
        "aliases": ["f#", "fs"],
        "platforms": ["desktop", "web", "data"],
        "frameworks": ["Fabulous", "Avalonia", "Elmish", "Bolero", "SAFE", "Fable"],
        "graphics": ["SkiaSharp", "LiveCharts", "Plotly.NET", "Avalonia", "Xaml", "DirectX"],
        "preview": ["Desktop", "Browser", "Mobile"],
    },
    "groovy": {
        "aliases": ["gradle"],
        "platforms": ["desktop", "web", "server"],
        "frameworks": ["Grails", "GWT", "JavaFX", "Swing"],
        "graphics": ["JavaFX", "Java2D", "Processing", "AWT"],
        "preview": ["Browser", "Desktop"],
    },
    "visual-basic": {
        "aliases": ["vb", "vb.net", "basic.net"],
        "platforms": ["desktop", "web"],
        "frameworks": ["WinForms", "WPF", "VB.NET", "ASP.NET"],
        "graphics": ["GDI+", "DirectX", "SkiaSharp", "WPF 2D/3D"],
        "preview": ["Desktop", "Browser"],
    },
}


def get_language_catalog() -> dict[str, dict[str, Any]]:
    return LANGUAGES


def resolve_language(value: str) -> str | None:
    normalized = value.lower().strip()
    for canonical, metadata in LANGUAGES.items():
        aliases = [canonical, *metadata["aliases"]]
        if normalized in aliases:
            return canonical
    return None


def find_graphics_libraries(prompt: str) -> list[dict[str, Any]]:
    text = prompt.lower()
    matches: list[dict[str, Any]] = []
    for language, metadata in LANGUAGES.items():
        language_aliases = [language, *metadata["aliases"]]
        if not any(
            re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text)
            if len(alias) >= 2
            else False
            for alias in language_aliases
        ):
            continue
        matches.append({
            "language": language,
            "platforms": metadata["platforms"],
            "frameworks": metadata["frameworks"],
            "graphics": metadata["graphics"],
            "preview": metadata["preview"],
        })
    return matches
