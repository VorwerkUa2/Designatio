# Designatio setup

## Requirements

- Windows 10/11
- Python 3.10+
- Node.js 20+
- Tesseract OCR
- Chromium installed through Playwright

## Python setup

```powershell
cd C:\Users\knyaz\Desktop\Designatio
py -m pip install -e ".[test,image,vision,browser]"
py -m playwright install chromium
```

Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki or by:

```powershell
winget install --id UB-Mannheim.TesseractOCR --exact
```

## Run the complete pipeline

```powershell
py -m designatio.cli pipeline C:\path\to\mockup.png --name "My Product" --output output\pipeline
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
py -m designatio.mcp.server
```

Example `.claude.json` MCP registration:

```json
{
  "mcpServers": {
    "designatio": {
      "command": "py",
      "args": ["-m", "designatio.mcp.server"],
      "cwd": "C:/Users/knyaz/Desktop/Designatio"
    }
  }
}
```

