from __future__ import annotations

from pathlib import Path
from typing import Any
from PIL import Image, ImageFilter
import colorsys


def generate_seamless(source: str | Path, output_dir: str | Path, size: int = 512) -> dict[str, Any]:
    input_path = Path(source)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if not input_path.is_file():
        raise FileNotFoundError(f"Texture source not found: {input_path}")
    with Image.open(input_path).convert("RGB") as image:
        texture = image.resize((size, size), Image.Resampling.LANCZOS)
        seamless = texture.filter(ImageFilter.GaussianBlur(radius=1))
        base_path = output / "texture.png"
        seamless.save(base_path)

        gray = seamless.convert("L")
        normal = Image.new("RGBA", (size, size))
        pixels = normal.load()
        source_pixels = gray.load()
        for y in range(size):
            for x in range(size):
                left = source_pixels[(x - 1) % size, y]
                right = source_pixels[(x + 1) % size, y]
                up = source_pixels[x, (y - 1) % size]
                down = source_pixels[x, (y + 1) % size]
                dx = (left - right) / 255.0
                dy = (up - down) / 255.0
                red = int(max(0, min(255, (dx * 0.5 + 0.5) * 255)))
                green = int(max(0, min(255, (dy * 0.5 + 0.5) * 255)))
                blue = 255
                pixels[x, y] = (red, green, blue, 255)
        normal_path = output / "normal.png"
        normal.save(normal_path)

        roughness = gray.point(lambda value: int(value * 0.8 + 25))
        roughness_path = output / "roughness.png"
        roughness.save(roughness_path)

    return {
        "base": str(base_path.resolve()),
        "normal": str(normal_path.resolve()),
        "roughness": str(roughness_path.resolve()),
        "size": [size, size],
        "maps": ["base", "normal", "roughness"],
    }
