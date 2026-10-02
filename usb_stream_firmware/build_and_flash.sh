#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================="
echo "   Skyloong GK104 Pro USB LCD Firmware Builder & Flasher"
echo "======================================================="

if command -v pio &> /dev/null; then
    PIO_CMD="pio"
elif [ -f "$HOME/.local/bin/pio" ]; then
    PIO_CMD="$HOME/.local/bin/pio"
else
    echo "Instalowanie PlatformIO Core..."
    python3 -m pip install platformio --user --break-system-packages
    PIO_CMD="$HOME/.local/bin/pio"
fi

echo "1. Kompilacja oprogramowania ESP32-S3..."
$PIO_CMD run

echo "2. Kopiowanie skompilowanych plików binarnych do katalogu bin/..."
mkdir -p "$SCRIPT_DIR/bin"
cp "$SCRIPT_DIR/.pio/build/esp32s3/firmware.bin" "$SCRIPT_DIR/bin/"
cp "$SCRIPT_DIR/.pio/build/esp32s3/bootloader.bin" "$SCRIPT_DIR/bin/"
cp "$SCRIPT_DIR/.pio/build/esp32s3/partitions.bin" "$SCRIPT_DIR/bin/"

PORT="${1:-/dev/ttyACM0}"
if [ -e "$PORT" ]; then
    echo "3. Wgrywanie firmware do urządzenia na porcie $PORT..."
    python3 "$SCRIPT_DIR/flash_firmware.py" "$PORT"
else
    echo "Gotowe pliki binarne znajdują się w: $SCRIPT_DIR/bin/"
    echo "Aby wgrać: ./flash_firmware.py /dev/ttyACM0"
fi
