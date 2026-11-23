from __future__ import annotations

from pathlib import Path
from typing import Iterable
import asyncio
import json


BREAKPOINTS = (1440, 1024, 768, 390)


async def take_screenshots_async(target: str | Path, output_dir: str | Path) -> dict:
    from playwright.async_api import async_playwright

    target_text = str(target)
    if target_text.startswith("http://") or target_text.startswith("https://"):
        url = target_text
        target_path = None
    else:
        target_path = Path(target).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Preview target not found: {target_path}")
        url = target_path.as_uri() if target_path.is_file() else target_path.as_posix()

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
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

    return {
        "screenshots": screenshots,
        "target": url,
        "breakpoints": list(BREAKPOINTS),
    }


def take_screenshots(target: str | Path, output_dir: str | Path) -> dict:
    return asyncio.run(take_screenshots_async(target, output_dir))


async def inspect_preview_async(target: str | Path) -> dict:
    from playwright.async_api import async_playwright

    target_text = str(target)
    if target_text.startswith("http://") or target_text.startswith("https://"):
        url = target_text
    else:
        target_path = Path(target).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Preview target not found: {target_path}")
        url = target_path.as_uri() if target_path.is_file() else target_path.as_posix()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(url, wait_until="networkidle")
        metrics = await page.evaluate(
            """() => ({
              documentWidth: document.documentElement.scrollWidth,
              viewportWidth: document.documentElement.clientWidth,
              horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
              headings: [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map(node => node.tagName),
              h1Count: document.querySelectorAll("h1").length,
              imagesWithoutAlt: [...document.querySelectorAll("img")].filter(node => !node.hasAttribute("alt")).length,
              unlabeledButtons: [...document.querySelectorAll("button")].filter(node => !(node.textContent || "").trim() && !node.getAttribute("aria-label")).length,
              emptyLinks: [...document.querySelectorAll("a")].filter(node => !(node.textContent || "").trim() && !node.getAttribute("aria-label")).length,
              lang: document.documentElement.lang || null
            })"""
        )
        await browser.close()

    issues = []
    if metrics["horizontalOverflow"]:
        issues.append({"rule": "horizontal-overflow", "message": "Document is wider than the 1440px viewport"})
    if metrics["h1Count"] != 1:
        issues.append({"rule": "h1-count", "message": f"Expected exactly one h1; found {metrics['h1Count']}"})
    if metrics["imagesWithoutAlt"]:
        issues.append({"rule": "image-alt", "message": f"{metrics['imagesWithoutAlt']} image(s) have no alt attribute"})
    if metrics["unlabeledButtons"]:
        issues.append({"rule": "button-name", "message": f"{metrics['unlabeledButtons']} button(s) have no name"})
    if metrics["emptyLinks"]:
        issues.append({"rule": "link-name", "message": f"{metrics['emptyLinks']} link(s) have no name"})
    if not metrics["lang"]:
        issues.append({"rule": "document-language", "message": "The html element has no lang attribute"})
    return {"passed": not issues, "issues": issues, "metrics": metrics}


def inspect_preview(target: str | Path) -> dict:
    return asyncio.run(inspect_preview_async(target))


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


def compare_regions(
    reference: str | Path,
    rendered: str | Path,
    regions: list[dict],
    output_dir: str | Path,
) -> dict:
    try:
        from PIL import Image, ImageChops
    except ImportError as error:
        raise RuntimeError("Pillow is required: pip install 'designatio[image]'") from error

    reference_path = Path(reference)
    rendered_path = Path(rendered)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    reports: list[dict] = []

    with Image.open(reference_path).convert("RGB") as reference_image:
        with Image.open(rendered_path).convert("RGB") as rendered_image:
            scale_x = rendered_image.width / max(reference_image.width, 1)
            scale_y = rendered_image.height / max(reference_image.height, 1)
            for index, region in enumerate(regions):
                box = region["box"]
                left = max(0, int(box["x"] * scale_x))
                top = max(0, int(box["y"] * scale_y))
                right = min(rendered_image.width, int((box["x"] + box["width"]) * scale_x))
                bottom = min(rendered_image.height, int((box["y"] + box["height"]) * scale_y))
                if right <= left or bottom <= top:
                    reports.append({"region": index, "skipped": True, "reason": "Empty or out-of-bounds region"})
                    continue

                rendered_crop = rendered_image.crop((left, top, right, bottom))
                ref_left = max(0, box["x"])
                ref_top = max(0, box["y"])
                ref_right = min(reference_image.width, box["x"] + box["width"])
                ref_bottom = min(reference_image.height, box["y"] + box["height"])
                reference_crop = reference_image.crop((ref_left, ref_top, ref_right, ref_bottom)).resize(
                    (right - left, bottom - top),
                    Image.Resampling.LANCZOS,
                )
                difference = ImageChops.difference(reference_crop, rendered_crop)
                pixels = getattr(difference, "get_flattened_data", difference.getdata)()
                changed = sum(1 for pixel in pixels if max(pixel) > 8)
                total = max((right - left) * (bottom - top), 1)
                diff_path = output / f"region-{index}.png"
                difference.save(diff_path)
                reports.append({
                    "region": index,
                    "type": region.get("type", "zone"),
                    "box": box,
                    "differenceRatio": round(changed / total, 6),
                    "diffImage": str(diff_path.resolve()),
                })

    return {
        "reference": str(reference_path.resolve()),
        "rendered": str(rendered_path.resolve()),
        "regions": reports,
        "regionCount": len(reports),
    }
