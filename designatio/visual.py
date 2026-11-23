from __future__ import annotations

from pathlib import Path
from typing import Iterable
import asyncio
import json


BREAKPOINTS = (1440, 1024, 768, 390)


async def take_screenshots_async(target: str | Path, output_dir: str | Path) -> dict:
    from playwright.async_api import async_playwright

    target_path = Path(target).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Preview target not found: {target_path}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    url = target_path.as_uri() if target_path.is_file() else target_path.as_posix()
    screenshots: dict[str, str] = {}

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        for width in BREAKPOINTS:
            page = await browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=1)
            await page.goto(url, wait_until="networkidle")
            await page.screenshot(path=str(output / f"{width}.png"), full_page=True)
            screenshots[str(width)] = str((output / f"{width}.png").resolve())
            await page.close()
        await browser.close()

    return {"screenshots": screenshots, "target": str(target_path), "breakpoints": list(BREAKPOINTS)}


def take_screenshots(target: str | Path, output_dir: str | Path) -> dict:
    return asyncio.run(take_screenshots_async(target, output_dir))


def compare_images(reference: str | Path, rendered: str | Path, output_dir: str | Path) -> dict:
    try:
        from PIL import Image, ImageChops, ImageStat
    except ImportError as error:
        raise RuntimeError("Pillow is required: pip install 'designatio[image]'") from error

    reference_path = Path(reference)
    rendered_path = Path(rendered)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    if not reference_path.is_file():
        raise FileNotFoundError(f"Reference image not found: {reference_path}")
    if not rendered_path.is_file():
        raise FileNotFoundError(f"Rendered image not found: {rendered_path}")

    with Image.open(reference_path).convert("RGB") as reference_image:
        with Image.open(rendered_path).convert("RGB") as rendered_image:
            width = min(reference_image.width, rendered_image.width)
            height = min(reference_image.height, rendered_image.height)
            reference_crop = reference_image.crop((0, 0, width, height))
            rendered_crop = rendered_image.crop((0, 0, width, height))

            difference = ImageChops.difference(reference_crop, rendered_crop)
            pixels = getattr(difference, "get_flattened_data", difference.getdata)()
            diff_pixels = sum(1 for pixel in pixels if max(pixel) > 8)
            total_pixels = width * height
            difference_ratio = diff_pixels / total_pixels if total_pixels else 1.0

            stat = ImageStat.Stat(difference)
            mean_difference = sum(stat.mean) / len(stat.mean)
            diff_output = output / "diff.png"
            difference.point(lambda value: min(255, value * 4)).save(diff_output)

    return {
        "reference": str(reference_path.resolve()),
        "rendered": str(rendered_path.resolve()),
        "width": width,
        "height": height,
        "differentPixels": diff_pixels,
        "totalPixels": total_pixels,
        "differenceRatio": round(difference_ratio, 6),
        "meanDifference": round(mean_difference, 3),
        "diffImage": str(diff_output.resolve()),
    }
