$ErrorActionPreference = "Stop"

param(
    [switch]$All,
    [switch]$Flutter,
    [switch]$Android,
    [switch]$ShaderTools
)

Write-Host "Installing Designatio Python dependencies..."
python -m pip install -e ".[test,image,vision,browser,security]"
python -m playwright install chromium

if ($env:OS -eq "Windows_NT") {
    $tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
    if (-not $tesseract) {
        Write-Warning "Tesseract OCR was not found. Install it with winget:"
        Write-Host "winget install --id UB-Mannheim.TesseractOCR --exact"
    }

    if ($All -or $Flutter) {
        $flutterRoot = Join-Path $env:LOCALAPPDATA "flutter"
        if (-not (Test-Path $flutterRoot)) {
            if (Get-Command git -ErrorAction SilentlyContinue) {
                Write-Host "Installing Flutter SDK..."
                git clone --depth 1 https://github.com/flutter/flutter.git -b stable $flutterRoot
                Write-Warning "Add $flutterRoot\bin to PATH and run flutter doctor."
            } else {
                Write-Warning "Git is required to install Flutter."
            }
        }
    }

    if ($All -or $Android) {
        $androidRoot = Join-Path $env:LOCALAPPDATA "Android"
        New-Item -ItemType Directory -Force -Path $androidRoot | Out-Null
        $zip = Join-Path $env:TEMP "android-commandlinetools.zip"
        Write-Host "Downloading Android command-line tools..."
        Invoke-WebRequest -Uri "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip" -OutFile $zip
        Expand-Archive -Path $zip -DestinationPath $androidRoot -Force
        Write-Warning "Set ANDROID_SDK_ROOT=$androidRoot and run sdkmanager --licenses."
    }

    if ($All -or $ShaderTools) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "Use winget to install a Vulkan SDK or Khronos shader tools when needed."
        }
    }
}

Write-Host "Designatio installation complete."
Write-Host "Run: designatio-doctor"
Write-Host "Run: designatio-run --name 'My Product' --output output\automated"

