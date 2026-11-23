from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Iterable


def python_executable() -> str:
    candidates = [sys.executable, shutil.which("python3"), shutil.which("python"), "python"]
    for candidate in candidates:
        if candidate:
            return candidate
    return "python"


def npm_executable() -> str | None:
    if os.name == "nt":
        return shutil.which("npm.cmd") or shutil.which("npm")
    return shutil.which("npm")


def npm_command(*arguments: str) -> list[str]:
    executable = npm_executable()
    if not executable:
        raise RuntimeError("npm is not installed or not in PATH")
    return [executable, *arguments]


def tesseract_executable() -> str | None:
    for candidate in (
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def executable_for(command: str) -> str | None:
    return shutil.which(command)
