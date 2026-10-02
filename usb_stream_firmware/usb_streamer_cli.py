#!/usr/bin/env python3
"""
Standalone CLI Frame Streamer for Skyloong GK104 Pro USB Screen.
Streams live PC metrics, clock, custom images, or GIFs directly over USB (/dev/ttyACM0).
"""

import os
import sys
import time
import argparse
import glob
import struct
import io
import psutil
from PIL import Image, ImageDraw, ImageFont

try:
    import serial
except ImportError:
    print("❌ Błąd: Brak biblioteki pyserial. Zainstaluj: pip install pyserial pillow psutil")
    sys.exit(1)


MAGIC = b'SKYL'
CMD_DRAW_JPEG = 0x01
CMD_SET_BRIGHTNESS = 0x03
CMD_PING = 0x04
ACK = 0x06


def find_esp_port():
    ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    return ports[0] if ports else '/dev/ttyACM0'


class StandaloneStreamer:
    def __init__(self, port, baudrate=115200, fps=20, quality=80):
        self.port = port
        self.baudrate = baudrate
        self.target_fps = fps
        self.quality = quality
        self.ser = None

    def connect(self):
        print(f"🔌 Łączenie z ekranem Skyloong na {self.port}...")
        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.5, write_timeout=0.5)
        time.sleep(0.1)
        print("✅ Połączono przez USB!")

    def send_frame(self, pil_img):
        if pil_img.size != (320, 240):
            pil_img = pil_img.resize((320, 240), Image.Resampling.LANCZOS)
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')

        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=self.quality, optimize=True)
        jpeg_data = buf.getvalue()

        header = struct.pack('<4sBI', MAGIC, CMD_DRAW_JPEG, len(jpeg_data))
        packet = header + jpeg_data

        self.ser.write(packet)
        self.ser.flush()
        ack = self.ser.read(1)
        return bool(ack and ack[0] == ACK)

    def render_system_frame(self):
        """Generates dynamic 320x240 telemetry dashboard."""
        img = Image.new("RGB", (320, 240), (10, 15, 29))
        draw = ImageDraw.Draw(img)

        # Header
        draw.rectangle([0, 0, 320, 36], fill=(15, 23, 42))
        draw.text((12, 10), "SKYLOONG USB MONITOR", fill=(0, 240, 255))

        # Time
        now_str = time.strftime("%H:%M:%S")
        draw.text((220, 10), now_str, fill=(255, 255, 255))

        # Metrics
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        ram_gb = psutil.virtual_memory().used / (1024**3)

        # Draw CPU Bar
        draw.text((15, 50), f"CPU USAGE: {cpu:.1f}%", fill=(56, 189, 248))
        draw.rectangle([15, 72, 305, 88], outline=(56, 189, 248), width=1)
        cpu_w = int(2.9 * cpu)
        if cpu_w > 0:
            fill_col = (0, 240, 255) if cpu < 75 else (239, 68, 68)
            draw.rectangle([17, 74, 15 + cpu_w, 86], fill=fill_col)

        # Draw RAM Bar
        draw.text((15, 105), f"RAM USAGE: {ram:.1f}% ({ram_gb:.1f} GB)", fill=(168, 85, 247))
        draw.rectangle([15, 127, 305, 143], outline=(168, 85, 247), width=1)
        ram_w = int(2.9 * ram)
        if ram_w > 0:
            draw.rectangle([17, 129, 15 + ram_w, 141], fill=(168, 85, 247))

        # Footer Status
        draw.rectangle([0, 204, 320, 240], fill=(15, 23, 42))
        draw.text((15, 212), "USB STREAM: 🟢 30 FPS", fill=(16, 185, 129))

        return img

    def stream_loop(self, mode="system", file_path=None):
        print(f"🚀 Rozpoczęto strumieniowanie (Tryb: {mode}, Cel: {self.target_fps} FPS)...")
        frame_delay = 1.0 / float(self.target_fps)

        if mode == "image" and file_path and os.path.exists(file_path):
            img = Image.open(file_path)
            while True:
                self.send_frame(img)
                time.sleep(1.0)

        elif mode == "gif" and file_path and os.path.exists(file_path):
            gif = Image.open(file_path)
            while True:
                for frame_idx in range(getattr(gif, 'n_frames', 1)):
                    gif.seek(frame_idx)
                    t0 = time.time()
                    self.send_frame(gif)
                    dt = time.time() - t0
                    rem = frame_delay - dt
                    if rem > 0:
                        time.sleep(rem)

        else: # System mode
            fps_count = 0
            t_last = time.time()
            while True:
                t0 = time.time()
                frame = self.render_system_frame()
                self.send_frame(frame)
                fps_count += 1

                if time.time() - t_last >= 1.0:
                    real_fps = fps_count / (time.time() - t_last)
                    print(f"📊 USB FPS: {real_fps:.1f}", end='\r')
                    fps_count = 0
                    t_last = time.time()

                dt = time.time() - t0
                rem = frame_delay - dt
                if rem > 0:
                    time.sleep(rem)


def main():
    parser = argparse.ArgumentParser(description="Skyloong GK104 Pro USB LCD Streamer CLI")
    parser.add_argument("--port", default=find_esp_port(), help="Port USB (/dev/ttyACM0)")
    parser.add_argument("--fps", type=int, default=30, help="Docelowa liczba klatek (FPS)")
    parser.add_argument("--quality", type=int, default=80, help="Jakość kompresji JPEG (20-95)")
    parser.add_argument("--mode", choices=["system", "image", "gif"], default="system", help="Tryb strumieniowania")
    parser.add_argument("--file", help="Ścieżka do pliku graficznego/GIF")

    args = parser.parse_args()

    streamer = StandaloneStreamer(port=args.port, fps=args.fps, quality=args.quality)
    try:
        streamer.connect()
        streamer.stream_loop(mode=args.mode, file_path=args.file)
    except KeyboardInterrupt:
        print("\n👋 Zatrzymano strumieniowanie USB.")


if __name__ == "__main__":
    main()
