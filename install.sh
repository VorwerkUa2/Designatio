#!/usr/bin/env sh
set -eu

INSTALL_ALL=false
INSTALL_FLUTTER=false
INSTALL_ANDROID=false
INSTALL_SHADER=false

for arg in "$@"; do
    case "$arg" in
        --all) INSTALL_ALL=true ;;
        --flutter) INSTALL_FLUTTER=true ;;
        --android) INSTALL_ANDROID=true ;;
        --shader-tools) INSTALL_SHADER=true ;;
    esac
done

echo "Installing Designatio Python dependencies..."
python3 -m pip install -e ".[test,image,vision,browser,security]"
python3 -m playwright install chromium

if command -v tesseract >/dev/null 2>&1; then
    echo "Tesseract OCR found."
elif command -v apt-get >/dev/null 2>&1; then
    echo "Install Tesseract OCR with:"
    echo "sudo apt-get install tesseract-ocr tesseract-ocr-eng"
elif command -v dnf >/dev/null 2>&1; then
    echo "Install Tesseract OCR with:"
    echo "sudo dnf install tesseract"
elif command -v pacman >/dev/null 2>&1; then
    echo "Install Tesseract OCR with:"
    echo "sudo pacman -S tesseract"
else
    echo "Install Tesseract OCR using your platform package manager."
fi

if [ "$INSTALL_ALL" = true ] || [ "$INSTALL_FLUTTER" = true ]; then
    FLUTTER_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/flutter"
    if [ ! -d "$FLUTTER_ROOT" ] && command -v git >/dev/null 2>&1; then
        echo "Installing Flutter SDK..."
        git clone --depth 1 https://github.com/flutter/flutter.git -b stable "$FLUTTER_ROOT"
        echo "Add $FLUTTER_ROOT/bin to PATH and run flutter doctor."
    fi
fi

if [ "$INSTALL_ALL" = true ] || [ "$INSTALL_ANDROID" = true ]; then
    ANDROID_ROOT="${ANDROID_SDK_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/android}"
    mkdir -p "$ANDROID_ROOT"
    echo "Configure Android SDK at $ANDROID_ROOT."
    echo "Use https://developer.android.com/studio#command-tools to install command-line tools."
fi

if [ "$INSTALL_ALL" = true ] || [ "$INSTALL_SHADER" = true ]; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Install shader tools with:"
        echo "sudo apt-get install glslang-tools"
    else
        echo "Install glslangValidator using your platform package manager."
    fi
fi

echo "Designatio installation complete."
echo "Run: designatio-doctor"
echo "Run: designatio-run --name 'My Product' --output output/automated"
