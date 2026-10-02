#!/usr/bin/env python3
"""
Skyloong GK104 Pro USB LCD Firmware Flasher.
Flashes the ultra-fast USB Frame Streamer firmware to the ESP32-S3 module.
"""

import sys
import os
import subprocess
import glob
import time

def find_esp_port():
    acm_ports = sorted(glob.glob('/dev/ttyACM*'))
    if acm_ports:
        return acm_ports[0]
    
    usb_ports = sorted(glob.glob('/dev/ttyUSB*'))
    for p in usb_ports:
        if p not in ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3']:
            return p
            
    return '/dev/ttyACM0'

def flash_firmware(port=None):
    if not port:
        port = find_esp_port()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(script_dir, "bin")
    
    bootloader = os.path.join(bin_dir, "bootloader.bin")
    partitions = os.path.join(bin_dir, "partitions.bin")
    firmware = os.path.join(bin_dir, "firmware.bin")
    
    if not (os.path.exists(bootloader) and os.path.exists(partitions) and os.path.exists(firmware)):
        print("❌ Precompiled binaries not found. Building with PlatformIO...")
        subprocess.run(["pio", "run"], cwd=script_dir, check=True)
        bootloader = os.path.join(script_dir, ".pio", "build", "esp32s3", "bootloader.bin")
        partitions = os.path.join(script_dir, ".pio", "build", "esp32s3", "partitions.bin")
        firmware = os.path.join(script_dir, ".pio", "build", "esp32s3", "firmware.bin")

    print(f"⚡ Flashing Skyloong USB Screen Firmware to {port}...")
    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", "esp32s3",
        "--port", port,
        "--baud", "921600",
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash",
        "-z",
        "--flash_mode", "dio",
        "--flash_freq", "80m",
        "--flash_size", "detect",
        "0x0", bootloader,
        "0x8000", partitions,
        "0x10000", firmware
    ]
    
    try:
        res = subprocess.run(cmd, check=True)
        print("\n✅ Firmware successfully flashed to Skyloong LCD!")
        print("Ekran jest teraz gotowy do bezpośredniego streamowania klatek przez USB!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error flashing firmware: {e}")
        return False

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else None
    flash_firmware(p)
