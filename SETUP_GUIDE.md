# Designatio setup

## Requirements

- Windows 10/11
- Python 3.10+
- Node.js 20+
- Tesseract OCR
- Chromium installed through Playwright

## Python setup

Windows:

```powershell
cd C:\Users\knyaz\Desktop\Designatio
.\install.ps1
```

Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki or by:

```powershell
winget install --id UB-Mannheim.TesseractOCR --exact
```

Linux/macOS:

```sh
cd /path/to/Designatio
./install.sh
```

## Automated one-command workflow

```powershell
designatio-doctor
designatio-run --mockup C:\path\to\mockup.png --name "My Product" --output output\automated
```

## Run the complete pipeline

```powershell
python -m designatio.cli pipeline /path/to/mockup.png --name "My Product" --output output/pipeline
```

This creates:

- `project.json`
- generated React/Vite source
- React build
- screenshots at 1440, 1024, 768 and 390 px
- visual diff images
- accessibility and responsive reports

## Run MCP

```powershell
python -m designatio.mcp.server
```

Example `.claude.json` MCP registration:

```json
{
  "mcpServers": {
    "designatio": {
      "command": "python",
      "args": ["-m", "designatio.mcp.server"],
      "cwd": "C:/Users/knyaz/Desktop/Designatio"
    }
  }
}
```

