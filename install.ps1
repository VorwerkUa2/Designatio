$ErrorActionPreference = "Stop"

Write-Host "Installing Designatio Python dependencies..."
python -m pip install -e ".[test,image,vision,browser,security]"
python -m playwright install chromium

if ($env:OS -eq "Windows_NT") {
    $tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
    if (-not $tesseract) {
        Write-Warning "Tesseract OCR was not found. Install it with winget:"
        Write-Host "winget install --id UB-Mannheim.TesseractOCR --exact"
    }
}

Write-Host "Designatio installation complete."
Write-Host "Run: designatio-doctor"
Write-Host "Run: designatio-run --name 'My Product' --output output\automated"

