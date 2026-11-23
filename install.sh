#!/usr/bin/env sh
set -eu

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

echo "Designatio installation complete."
echo "Run: designatio-doctor"
echo "Run: designatio-run --name 'My Product' --output output/automated"
