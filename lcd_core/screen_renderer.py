import os
import time
import math
import random
import calendar
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from typing import Dict, Any, List, Optional, Tuple

# Helper function to get default or custom font
def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Tries to find a clean TrueType font on Linux, fallbacks to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


class ScreenRenderer:
    """
    Renders ultra-crisp 320x240 frames for the Skyloong GK104 Pro LCD USB display.
    Supports a wide array of screens: Retro Synthwave, Matrix Rain, Audio Visualizer,
    Dual Racing Tachometer Gauges, Pomodoro Focus Timer, Sci-Fi Starship HUD,
    Custom Modular Dashboard, Hardware Thermals, Telemetry, Clocks, Calendar, Photos & GIFs.
    """

    def __init__(self, width: int = 320, height: int = 240):
        self.width = width
        self.height = height
        
        # GIF Animation State
        self.gif_path: Optional[str] = None
        self.gif_frames: List[Image.Image] = []
        self.gif_durations: List[int] = []
        self.gif_current_index: int = 0
        self.gif_last_time: float = 0
        
        # Slideshow State
        self.slideshow_index: int = 0
        self.slideshow_last_switch: float = 0
        self.slideshow_cached_img: Optional[Image.Image] = None
        
        # Custom BG Image Cache
        self.bg_image_path: Optional[str] = None
        self.bg_image_cached: Optional[Image.Image] = None
        
        # Matrix Rain State
        self.matrix_cols = 32
        self.matrix_drops = [random.randint(-20, 24) for _ in range(self.matrix_cols)]
        self.matrix_chars = [chr(random.randint(0x30A0, 0x30FF)) if random.random() > 0.5 else chr(random.randint(48, 90)) for _ in range(self.matrix_cols)]
        self.matrix_last_tick = time.time()

        # Audio Visualizer Animation State
        self.audio_bars_count = 18
        self.audio_bars_vals = [random.uniform(0.1, 0.8) for _ in range(self.audio_bars_count)]
        self.audio_peaks = [0.0] * self.audio_bars_count
        self.audio_last_tick = time.time()

        # Sci-Fi Radar Animation State
        self.radar_angle = 0.0

        # Last rendered frame
        self.current_frame: Optional[Image.Image] = None

    def get_current_frame(self) -> Optional[Image.Image]:
        """Returns the most recently rendered frame."""
        return self.current_frame

    def render(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        """Main dispatcher based on current_mode."""
        mode = config.get("current_mode", "retro_synthwave")
        self.width = config.get("width", 320)
        self.height = config.get("height", 240)

        img: Image.Image
        if mode == "retro_synthwave":
            img = self.render_retro_synthwave_mode(config, metrics)
        elif mode == "matrix_rain":
            img = self.render_matrix_rain_mode(config, metrics)
        elif mode == "audio_visualizer":
            img = self.render_audio_visualizer_mode(config, metrics)
        elif mode == "dual_gauges":
            img = self.render_dual_gauges_mode(config, metrics)
        elif mode == "pomodoro":
            img = self.render_pomodoro_mode(config)
        elif mode == "scifi_terminal":
            img = self.render_scifi_terminal_mode(config, metrics)
        elif mode == "custom":
            img = self.render_custom_mode(config, metrics)
        elif mode == "usage":
            img = self.render_usage_mode(config, metrics)
        elif mode == "temperatures":
            img = self.render_temperatures_mode(config, metrics)
        elif mode == "clock":
            img = self.render_clock_mode(config)
        elif mode == "calendar":
            img = self.render_calendar_mode(config)
        elif mode == "image":
            img = self.render_image_mode(config)
        elif mode == "gif":
            img = self.render_gif_mode(config)
        elif mode == "slideshow":
            img = self.render_slideshow_mode(config)
        else:
            img = self.render_custom_mode(config, metrics)

        self.current_frame = img
        return img

    # =============================================================
    # 1. RETRO SYNTHWAVE / CYBER HUD MODE
    # =============================================================
    def render_retro_synthwave_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0a0518")
        draw = ImageDraw.Draw(img)

        horizon_y = 110

        # Gradient Sky
        for y in range(0, horizon_y):
            ratio = y / horizon_y
            r = int(20 + ratio * (255 - 20))
            g = int(5 + ratio * (40 - 5))
            b = int(45 + ratio * (150 - 45))
            draw.line([0, y, self.width, y], fill=(r // 4, g // 5, b // 3))

        # Synthwave Sun
        if config.get("synthwave_show_sun", True):
            sun_cx = self.width // 2
            sun_cy = horizon_y
            sun_radius = 48
            for r in range(sun_radius, 0, -1):
                col = (255, int(180 * (1 - r / sun_radius)), int(20 * (1 - r / sun_radius)))
                draw.ellipse([sun_cx - r, sun_cy - r, sun_cx + r, sun_cy + r], fill=col)
            # Sun horizontal scanlines
            for sy in range(sun_cy - sun_radius, sun_cy, 6):
                strip_h = int(1 + (sy - (sun_cy - sun_radius)) / 10)
                draw.rectangle([sun_cx - sun_radius, sy, sun_cx + sun_radius, sy + strip_h], fill="#0a0518")

        # Horizon Glow Line
        draw.line([0, horizon_y, self.width, horizon_y], fill="#ff007f", width=2)

        # Perspective Grid
        t = time.time()
        grid_offset = int((t * 25) % 20)
        # Horizontal moving lines
        for i in range(1, 9):
            gy = horizon_y + int(math.pow(i / 8.0, 1.8) * (self.height - horizon_y)) + (grid_offset * i // 12)
            if gy < self.height:
                alpha_col = (0, 240, 255)
                draw.line([0, gy, self.width, gy], fill=alpha_col, width=1)

        # Perspective vertical lines converging to center horizon
        for vx in range(-self.width, self.width * 2, 35):
            draw.line([self.width // 2, horizon_y, vx, self.height], fill="#7928ca", width=1)

        # Foreground HUD: Clock & Telemetry Badges
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        f_time = get_font(26, bold=True)
        f_sub = get_font(10, bold=True)
        f_stat = get_font(11, bold=True)

        # Time Banner at top
        if config.get("synthwave_show_clock", True):
            draw.rounded_rectangle([15, 8, 150, 42], radius=6, fill=(15, 10, 30, 220), outline="#00f0ff", width=1)
            draw.text((25, 12), time_str, fill="#00f0ff", font=f_time)

        # Custom text badge (top right)
        custom_txt = config.get("synthwave_custom_text", "CYBERPUNK 2077")
        draw.rounded_rectangle([self.width - 150, 8, self.width - 15, 42], radius=6, fill=(15, 10, 30, 220), outline="#ff007f", width=1)
        draw.text((self.width - 140, 14), custom_txt[:16], fill="#ff007f", font=f_sub)
        draw.text((self.width - 140, 26), now.strftime("%Y.%m.%d - %A")[:16], fill="#e2e8f0", font=get_font(9, bold=False))

        # Bottom Telemetry Gauges (CPU, GPU, RAM)
        if config.get("synthwave_show_telemetry", True):
            cpu = metrics.get('cpu_percent', 0.0)
            gpu = metrics.get('gpu_percent', 0.0)
            ram = metrics.get('ram_percent', 0.0)
            cpu_t = metrics.get('cpu_temp', 0.0)

            # Left Card: CPU
            draw.rounded_rectangle([15, self.height - 56, 105, self.height - 10], radius=6, fill=(10, 8, 25, 230), outline="#00f0ff", width=1)
            draw.text((22, self.height - 52), "CPU LOAD", fill="#00f0ff", font=f_sub)
            draw.text((22, self.height - 38), f"{cpu:.0f}%", fill="#ffffff", font=f_stat)
            draw.text((65, self.height - 38), f"{cpu_t:.0f}°C", fill="#f59e0b", font=get_font(10, bold=False))
            self._draw_compact_bar(draw, 22, self.height - 20, 72, 4, cpu, "#00f0ff")

            # Center Card: GPU
            draw.rounded_rectangle([115, self.height - 56, 205, self.height - 10], radius=6, fill=(10, 8, 25, 230), outline="#ff007f", width=1)
            draw.text((122, self.height - 52), "GPU CORE", fill="#ff007f", font=f_sub)
            draw.text((122, self.height - 38), f"{gpu:.0f}%", fill="#ffffff", font=f_stat)
            self._draw_compact_bar(draw, 122, self.height - 20, 72, 4, gpu, "#ff007f")

            # Right Card: RAM
            draw.rounded_rectangle([215, self.height - 56, 305, self.height - 10], radius=6, fill=(10, 8, 25, 230), outline="#a855f7", width=1)
            draw.text((222, self.height - 52), "MEM USED", fill="#a855f7", font=f_sub)
            draw.text((222, self.height - 38), f"{ram:.0f}%", fill="#ffffff", font=f_stat)
            self._draw_compact_bar(draw, 222, self.height - 20, 72, 4, ram, "#a855f7")

        return img

    # =============================================================
    # 2. MATRIX DIGITAL RAIN & TERMINAL HUD
    # =============================================================
    def render_matrix_rain_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#020803")
        draw = ImageDraw.Draw(img)

        # Update rain drops
        now_time = time.time()
        speed = config.get("matrix_speed", 1.0)
        if now_time - self.matrix_last_tick > (0.05 / speed):
            for i in range(self.matrix_cols):
                self.matrix_drops[i] += 1
                if self.matrix_drops[i] * 12 > self.height and random.random() > 0.85:
                    self.matrix_drops[i] = random.randint(-8, 0)
                if random.random() > 0.7:
                    self.matrix_chars[i] = chr(random.randint(0x30A0, 0x30DF)) if random.random() > 0.4 else hex(random.randint(0, 15))[2:].upper()
            self.matrix_last_tick = now_time

        f_matrix = get_font(10, bold=True)
        col_theme = config.get("matrix_color", "matrix_green")
        
        main_color = (0, 255, 70)
        glow_color = (180, 255, 180)
        if col_theme == "amber_crt":
            main_color = (255, 170, 0)
            glow_color = (255, 230, 180)
        elif col_theme == "cyber_cyan":
            main_color = (0, 240, 255)
            glow_color = (200, 255, 255)
        elif col_theme == "red_alert":
            main_color = (255, 40, 40)
            glow_color = (255, 200, 200)

        # Draw matrix rain columns
        col_w = self.width // self.matrix_cols
        for i in range(self.matrix_cols):
            x = i * col_w + 2
            head_y = self.matrix_drops[i] * 12
            # Draw tail
            for tail in range(8):
                y = head_y - (tail * 12)
                if 0 <= y < self.height:
                    alpha = max(0, 255 - tail * 32)
                    c = glow_color if tail == 0 else (int(main_color[0] * alpha / 255), int(main_color[1] * alpha / 255), int(main_color[2] * alpha / 255))
                    char = self.matrix_chars[(i + tail) % self.matrix_cols]
                    draw.text((x, y), char, fill=c, font=f_matrix)

        # Center Terminal Overlay Box
        draw.rounded_rectangle([25, 40, self.width - 25, self.height - 40], radius=8, fill=(3, 15, 6, 235), outline=main_color, width=2)
        
        # Terminal Header
        draw.rectangle([25, 40, self.width - 25, 64], fill=(5, 30, 10, 240))
        draw.text((36, 46), "SYSTEM MATRIX // TERMINAL ACCESS", fill=main_color, font=get_font(10, bold=True))
        draw.line([25, 64, self.width - 25, 64], fill=main_color, width=1)

        # Center Digital Clock
        now = datetime.now()
        f_clk = get_font(28, bold=True)
        draw.text((self.width // 2 - 62, 75), now.strftime("%H:%M:%S"), fill=glow_color, font=f_clk)

        # Telemetry Metrics Grid
        cpu = metrics.get('cpu_percent', 0.0)
        ram = metrics.get('ram_percent', 0.0)
        gpu = metrics.get('gpu_percent', 0.0)
        temp = metrics.get('cpu_temp', 0.0)

        f_info = get_font(10, bold=True)
        draw.text((40, 122), f"CPU CORE: {cpu:04.1f}%", fill=main_color, font=f_info)
        draw.text((40, 142), f"RAM ALLOC: {ram:04.1f}%", fill=main_color, font=f_info)
        
        draw.text((180, 122), f"GPU ENG: {gpu:04.1f}%", fill=main_color, font=f_info)
        draw.text((180, 142), f"CORE TEMP: {temp:04.1f}°C", fill=main_color, font=f_info)

        # Bottom Sub-status
        draw.line([35, 168, self.width - 35, 168], fill=(20, 80, 30), width=1)
        uptime_str = f"CONN: USB CDC HIGH-SPEED • 320x240 @ 30FPS"
        draw.text((40, 175), uptime_str, fill=(120, 220, 140), font=get_font(9, bold=False))

        return img

    # =============================================================
    # 3. AUDIO VU METER & SPECTRUM VISUALIZER
    # =============================================================
    def render_audio_visualizer_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#060913")
        draw = ImageDraw.Draw(img)

        # Top Bar: Spectrum Title & Status
        draw.rectangle([0, 0, self.width, 32], fill="#0f172a")
        draw.line([0, 32, self.width, 32], fill="#1e293b", width=1)
        draw.text((14, 8), "AUDIO SPECTRUM ANALYZER", fill="#38bdf8", font=get_font(11, bold=True))
        
        # CPU Activity pulse
        cpu = metrics.get('cpu_percent', 0.0)
        draw.text((self.width - 100, 9), f"SYS AUDIO • {cpu:.0f}%", fill="#10b981", font=get_font(10, bold=True))

        # Dynamic Audio Simulation / Sound Waves
        now = time.time()
        dt = now - self.audio_last_tick
        self.audio_last_tick = now

        for i in range(self.audio_bars_count):
            # Target height based on frequency harmonics and real activity
            base_freq = math.sin(now * 5.0 + i * 0.4) * 0.3 + math.cos(now * 3.2 - i * 0.6) * 0.2 + (cpu / 200.0)
            target = min(0.98, max(0.08, base_freq + random.uniform(-0.15, 0.25)))
            
            # Smooth attack and decay
            self.audio_bars_vals[i] += (target - self.audio_bars_vals[i]) * 0.35
            
            # Peak hold
            if self.audio_bars_vals[i] > self.audio_peaks[i]:
                self.audio_peaks[i] = self.audio_bars_vals[i]
            else:
                self.audio_peaks[i] = max(0.0, self.audio_peaks[i] - dt * 0.4)

        # Draw Multi-band Spectrum Bars
        bar_area_x = 16
        bar_area_w = self.width - 32
        bar_area_y = 44
        bar_area_h = 120
        
        single_w = (bar_area_w - (self.audio_bars_count - 1) * 3) // self.audio_bars_count

        for i in range(self.audio_bars_count):
            bx = bar_area_x + i * (single_w + 3)
            val = self.audio_bars_vals[i]
            bh = int(val * bar_area_h)
            by = bar_area_y + bar_area_h - bh

            # Frequency segments (LED Blocks)
            segment_h = 4
            for seg_y in range(bar_area_y + bar_area_h - segment_h, by, -(segment_h + 2)):
                ratio = 1.0 - ((seg_y - bar_area_y) / float(bar_area_h))
                if ratio < 0.6:
                    col = "#00f0ff"  # Cyan low/mid
                elif ratio < 0.85:
                    col = "#facc15"  # Amber high
                else:
                    col = "#ef4444"  # Red peak
                draw.rectangle([bx, seg_y, bx + single_w, seg_y + segment_h], fill=col)

            # Peak Marker
            peak_val = self.audio_peaks[i]
            peak_y = bar_area_y + bar_area_h - int(peak_val * bar_area_h)
            draw.rectangle([bx, peak_y, bx + single_w, peak_y + 2], fill="#ffffff")

        # Bottom Stereo Dual VU Meter (L & R Channels)
        draw.rounded_rectangle([14, 176, self.width - 14, self.height - 10], radius=6, fill="#0b1120", outline="#1e293b", width=1)
        
        # Left channel VU
        draw.text((22, 182), "CH-L", fill="#94a3b8", font=get_font(9, bold=True))
        l_val = (self.audio_bars_vals[2] + self.audio_bars_vals[4]) / 2.0
        self._draw_vu_meter_bar(draw, 55, 184, self.width - 80, 8, l_val)

        # Right channel VU
        draw.text((22, 202), "CH-R", fill="#94a3b8", font=get_font(9, bold=True))
        r_val = (self.audio_bars_vals[12] + self.audio_bars_vals[14]) / 2.0
        self._draw_vu_meter_bar(draw, 55, 204, self.width - 80, 8, r_val)

        return img

    def _draw_vu_meter_bar(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, val: float):
        draw.rectangle([x, y, x + w, y + h], fill="#1e293b")
        fill_w = int(max(0.0, min(1.0, val)) * w)
        
        # Green / Yellow / Red zones
        g_w = min(fill_w, int(w * 0.65))
        y_w = max(0, min(fill_w - g_w, int(w * 0.22)))
        r_w = max(0, fill_w - g_w - y_w)

        if g_w > 0:
            draw.rectangle([x, y, x + g_w, y + h], fill="#10b981")
        if y_w > 0:
            draw.rectangle([x + g_w, y, x + g_w + y_w, y + h], fill="#f59e0b")
        if r_w > 0:
            draw.rectangle([x + g_w + y_w, y, x + g_w + y_w + r_w, y + h], fill="#ef4444")

    # =============================================================
    # 4. DUAL TACHOMETER RACING CLUSTER
    # =============================================================
    def render_dual_gauges_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0a0a0c")
        draw = ImageDraw.Draw(img)

        # Carbon fiber style grid background
        for cy in range(0, self.height, 4):
            draw.line([0, cy, self.width, cy], fill="#121216", width=1)

        cpu = metrics.get('cpu_percent', 0.0)
        gpu = metrics.get('gpu_percent', 0.0)
        cpu_temp = metrics.get('cpu_temp', 0.0)
        gpu_temp = metrics.get('gpu_temp', 0.0)
        ram = metrics.get('ram_percent', 0.0)

        # Left Dial: CPU
        self._draw_racing_gauge(draw, cx=82, cy=105, radius=65, val=cpu, label="CPU LOAD", unit="%", accent="#00f0ff")

        # Right Dial: GPU
        self._draw_racing_gauge(draw, cx=238, cy=105, radius=65, val=gpu, label="GPU CORE", unit="%", accent="#ff0055")

        # Center Digital Info Box
        draw.rounded_rectangle([125, 42, 195, 148], radius=8, fill="#13141f", outline="#2a2b3d", width=1)
        f_mid_lbl = get_font(9, bold=True)
        f_mid_val = get_font(13, bold=True)

        draw.text((135, 50), "CPU TEMP", fill="#94a3b8", font=f_mid_lbl)
        draw.text((135, 64), f"{cpu_temp:.0f}°C", fill="#f59e0b", font=f_mid_val)

        draw.line([132, 94, 188, 94], fill="#2a2b3d", width=1)

        draw.text((135, 102), "GPU TEMP", fill="#94a3b8", font=f_mid_lbl)
        draw.text((135, 116), f"{gpu_temp:.0f}°C", fill="#f59e0b", font=f_mid_val)

        # Bottom Telemetry Bar (RAM & NVMe Storage)
        draw.rounded_rectangle([20, 188, self.width - 20, 226], radius=6, fill="#12131c", outline="#222333", width=1)
        draw.text((32, 198), f"RAM: {ram:.0f}%", fill="#e2e8f0", font=get_font(10, bold=True))
        self._draw_compact_bar(draw, 100, 202, 100, 8, ram, "#a855f7")
        draw.text((215, 198), f"NVMe: {metrics.get('nvme_temp', 0.0):.0f}°C", fill="#38bdf8", font=get_font(10, bold=True))

        return img

    def _draw_racing_gauge(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, val: float, label: str, unit: str, accent: str):
        # Outer bezel
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill="#14141c", outline="#282836", width=2)
        
        # Arc Angles: 135 deg to 405 deg (270 deg sweep)
        start_ang = 135.0
        sweep_ang = 270.0
        end_ang = start_ang + sweep_ang

        # Background track ticks
        for deg in range(int(start_ang), int(end_ang) + 1, 15):
            rad = math.radians(deg)
            x1 = cx + math.cos(rad) * (radius - 12)
            y1 = cy + math.sin(rad) * (radius - 12)
            x2 = cx + math.cos(rad) * (radius - 4)
            y2 = cy + math.sin(rad) * (radius - 4)
            tick_col = "#ef4444" if deg > (start_ang + sweep_ang * 0.8) else "#475569"
            draw.line([x1, y1, x2, y2], fill=tick_col, width=2)

        # Needle Calculation
        norm_val = max(0.0, min(100.0, val)) / 100.0
        needle_deg = start_ang + norm_val * sweep_ang
        n_rad = math.radians(needle_deg)
        
        nx = cx + math.cos(n_rad) * (radius - 8)
        ny = cy + math.sin(n_rad) * (radius - 8)

        # Needle line
        draw.line([cx, cy, nx, ny], fill=accent, width=3)
        # Center pin
        draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill="#ffffff", outline=accent, width=2)

        # Label & Value
        f_lbl = get_font(9, bold=True)
        f_val = get_font(12, bold=True)
        draw.text((cx - 24, cy + radius - 26), label, fill="#94a3b8", font=f_lbl)
        draw.text((cx - 16, cy + 14), f"{val:.0f}{unit}", fill="#ffffff", font=f_val)

    # =============================================================
    # 5. POMODORO & FOCUS TIMER
    # =============================================================
    def render_pomodoro_mode(self, config: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0c0e17")
        draw = ImageDraw.Draw(img)

        mode = config.get("pomodoro_mode", "focus")  # focus or break
        time_left = config.get("pomodoro_time_left", 1500)
        total_time = config.get("pomodoro_focus_min", 25) * 60 if mode == "focus" else config.get("pomodoro_break_min", 5) * 60
        total_time = max(1, total_time)
        
        minutes = time_left // 60
        seconds = time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        accent = "#ef4444" if mode == "focus" else "#10b981"
        badge_text = "🎯 SESJA SKUPIENIA (FOCUS)" if mode == "focus" else "☕ PRZERWA REGENERACYJNA (BREAK)"

        # Top Header Badge
        draw.rounded_rectangle([20, 10, self.width - 20, 38], radius=6, fill="#151928", outline=accent, width=1)
        draw.text((36, 17), badge_text, fill=accent, font=get_font(10, bold=True))

        # Circular Progress Arc
        cx, cy, radius = self.width // 2, 130, 70
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill="#111422", outline="#1e2438", width=4)

        progress = 1.0 - (time_left / float(total_time))
        # Draw active progress dots around circle
        for deg in range(-90, int(-90 + progress * 360), 6):
            rad = math.radians(deg)
            px = cx + math.cos(rad) * (radius - 2)
            py = cy + math.sin(rad) * (radius - 2)
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=accent)

        # Big Timer Text inside circle
        f_timer = get_font(34, bold=True)
        draw.text((cx - 50, cy - 22), time_str, fill="#ffffff", font=f_timer)

        # Status text below timer
        task_name = config.get("pomodoro_task_name", "Deep Work Session")
        rounds = config.get("pomodoro_rounds_done", 0)
        draw.text((cx - 45, cy + 18), f"Runda: #{rounds + 1}", fill="#94a3b8", font=get_font(10, bold=False))

        # Bottom Task Box
        draw.text((30, 214), f"Zadanie: {task_name[:32]}", fill="#64748b", font=get_font(10, bold=True))

        return img

    # =============================================================
    # 6. SCI-FI STARSHIP / TERMINAL HUD
    # =============================================================
    def render_scifi_terminal_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#050b14")
        draw = ImageDraw.Draw(img)

        # Futuristic sci-fi frame
        accent = "#00f0ff"
        draw.rectangle([10, 10, self.width - 10, self.height - 10], outline="#172e48", width=1)
        
        # Corner Brackets
        c_len = 16
        draw.line([10, 10, 10 + c_len, 10], fill=accent, width=2)
        draw.line([10, 10, 10, 10 + c_len], fill=accent, width=2)
        draw.line([self.width - 10, 10, self.width - 10 - c_len, 10], fill=accent, width=2)
        draw.line([self.width - 10, 10, self.width - 10, 10 + c_len], fill=accent, width=2)
        draw.line([10, self.height - 10, 10 + c_len, self.height - 10], fill=accent, width=2)
        draw.line([10, self.height - 10, 10, self.height - 10 - c_len], fill=accent, width=2)
        draw.line([self.width - 10, self.height - 10, self.width - 10 - c_len, self.height - 10], fill=accent, width=2)
        draw.line([self.width - 10, self.height - 10, self.width - 10, self.height - 10 - c_len], fill=accent, width=2)

        # Sci-Fi Header
        ship_name = config.get("scifi_ship_name", "GK104-PRO ORBITAL")
        draw.text((20, 15), f"▶ {ship_name} // HUD v3.4", fill=accent, font=get_font(10, bold=True))
        now = datetime.now()
        draw.text((self.width - 95, 15), now.strftime("%H:%M:%S"), fill="#ffffff", font=get_font(10, bold=True))

        draw.line([15, 30, self.width - 15, 30], fill="#1e3a5f", width=1)

        # Left: Tactical Radar
        rcx, rcy, rradius = 70, 95, 50
        draw.ellipse([rcx - rradius, rcy - rradius, rcx + rradius, rcy + rradius], fill="#081422", outline="#1c4166", width=1)
        draw.ellipse([rcx - 28, rcy - 28, rcx + 28, rcy + 28], outline="#1c4166", width=1)
        draw.line([rcx - rradius, rcy, rcx + rradius, rcy], fill="#1c4166", width=1)
        draw.line([rcx, rcy - rradius, rcx, rcy + rradius], fill="#1c4166", width=1)

        # Radar Sweep Animation
        self.radar_angle = (self.radar_angle + 5) % 360
        r_rad = math.radians(self.radar_angle)
        draw.line([rcx, rcy, rcx + math.cos(r_rad) * rradius, rcy + math.sin(r_rad) * rradius], fill="#00ffcc", width=2)

        # Radar blips
        draw.ellipse([rcx + 18, rcy - 12, rcx + 22, rcy - 8], fill="#ff0055")
        draw.ellipse([rcx - 22, rcy + 16, rcx - 18, rcy + 20], fill="#00f0ff")

        # Right: Reactor Core Telemetry
        cpu = metrics.get('cpu_percent', 0.0)
        gpu = metrics.get('gpu_percent', 0.0)
        ram = metrics.get('ram_percent', 0.0)

        f_sec = get_font(9, bold=True)
        f_val = get_font(11, bold=True)

        rx = 135
        # CPU Core
        draw.text((rx, 42), "REACTOR CORE (CPU)", fill="#38bdf8", font=f_sec)
        draw.text((self.width - 55, 42), f"{cpu:.0f}%", fill="#ffffff", font=f_val)
        self._draw_compact_bar(draw, rx, 56, self.width - rx - 20, 6, cpu, "#38bdf8")

        # GPU Thrusters
        draw.text((rx, 72), "WARP ENGINE (GPU)", fill="#d946ef", font=f_sec)
        draw.text((self.width - 55, 72), f"{gpu:.0f}%", fill="#ffffff", font=f_val)
        self._draw_compact_bar(draw, rx, 86, self.width - rx - 20, 6, gpu, "#d946ef")

        # Memory Hull
        draw.text((rx, 102), "SHIELD BUFFER (RAM)", fill="#10b981", font=f_sec)
        draw.text((self.width - 55, 102), f"{ram:.0f}%", fill="#ffffff", font=f_val)
        self._draw_compact_bar(draw, rx, 116, self.width - rx - 20, 6, ram, "#10b981")

        # Bottom Diagnostic Matrix
        draw.rounded_rectangle([15, 155, self.width - 15, self.height - 15], radius=4, fill="#0a192c", outline="#1c4166", width=1)
        
        cpu_t = metrics.get('cpu_temp', 0.0)
        gpu_t = metrics.get('gpu_temp', 0.0)
        nvme_t = metrics.get('nvme_temp', 0.0)

        f_diag = get_font(9, bold=True)
        draw.text((25, 164), f"CORE TEMP: {cpu_t:.0f}°C", fill="#f59e0b", font=f_diag)
        draw.text((120, 164), f"GPU TEMP: {gpu_t:.0f}°C", fill="#f59e0b", font=f_diag)
        draw.text((215, 164), f"STORAGE: {nvme_t:.0f}°C", fill="#10b981", font=f_diag)

        draw.text((25, 184), "SYS DIAGNOSTIC: ALL SYSTEMS NOMINAL • USB DMA ONLINE", fill="#00f0ff", font=get_font(9, bold=False))

        return img

    # =============================================================
    # 7. IMAGE MODE
    # =============================================================
    def render_image_mode(self, config: Dict[str, Any]) -> Image.Image:
        img_path = config.get("image_path", "")
        if not img_path or not os.path.exists(img_path):
            return self._create_placeholder("Brak wybranego zdjęcia", "Wybierz plik w menu Zdjęcia")

        try:
            with Image.open(img_path) as raw:
                img = raw.convert("RGBA")
                fit = config.get("image_fit", "cover")
                img = self._fit_image(img, self.width, self.height, fit)
                
                # Brightness / Contrast
                bright = config.get("image_brightness", 100)
                contrast = config.get("image_contrast", 100)
                if bright != 100:
                    img = ImageEnhance.Brightness(img).enhance(bright / 100.0)
                if contrast != 100:
                    img = ImageEnhance.Contrast(img).enhance(contrast / 100.0)
                return img
        except Exception as e:
            return self._create_placeholder("Błąd wczytywania", str(e)[:30])

    # =============================================================
    # 8. GIF MODE
    # =============================================================
    def render_gif_mode(self, config: Dict[str, Any]) -> Image.Image:
        gif_path = config.get("gif_path", "")
        if not gif_path or not os.path.exists(gif_path):
            return self._create_placeholder("Brak wybranego GIFa", "Wybierz animację w menu GIF")

        if self.gif_path != gif_path:
            self._load_gif(gif_path)

        if not self.gif_frames:
            return self._create_placeholder("Niepoprawny GIF", "Brak klatek animacji")

        speed = max(0.1, config.get("gif_speed", 1.0))
        now = time.time()
        curr_duration = (self.gif_durations[self.gif_current_index] / 1000.0) / speed

        if now - self.gif_last_time >= curr_duration:
            self.gif_current_index = (self.gif_current_index + 1) % len(self.gif_frames)
            self.gif_last_time = now

        return self.gif_frames[self.gif_current_index]

    def _load_gif(self, path: str):
        self.gif_path = path
        self.gif_frames = []
        self.gif_durations = []
        self.gif_current_index = 0
        self.gif_last_time = time.time()
        try:
            with Image.open(path) as gif:
                for frame_idx in range(getattr(gif, 'n_frames', 1)):
                    gif.seek(frame_idx)
                    frame = gif.convert("RGBA")
                    frame = self._fit_image(frame, self.width, self.height, "cover")
                    duration = gif.info.get('duration', 100)
                    if duration <= 10:
                        duration = 100
                    self.gif_frames.append(frame)
                    self.gif_durations.append(duration)
        except Exception as e:
            print(f"[ScreenRenderer] Error loading GIF: {e}")

    # =============================================================
    # 9. SLIDESHOW MODE
    # =============================================================
    def render_slideshow_mode(self, config: Dict[str, Any]) -> Image.Image:
        images: List[str] = config.get("slideshow_images", [])
        if not images:
            return self._create_placeholder("Pokaz slajdów", "Dodaj zdjęcia do listy")

        valid_images = [img for img in images if os.path.exists(img)]
        if not valid_images:
            return self._create_placeholder("Brak plików", "Zdjęcia z listy nie istnieją")

        interval = max(1, config.get("slideshow_interval", 5))
        now = time.time()

        if now - self.slideshow_last_switch >= interval or self.slideshow_cached_img is None:
            self.slideshow_index = (self.slideshow_index + 1) % len(valid_images)
            self.slideshow_last_switch = now
            current_path = valid_images[self.slideshow_index]
            try:
                with Image.open(current_path) as raw:
                    img = raw.convert("RGBA")
                    self.slideshow_cached_img = self._fit_image(img, self.width, self.height, "cover")
            except Exception:
                self.slideshow_cached_img = self._create_placeholder("Błąd zdjęcia", os.path.basename(current_path))

        return self.slideshow_cached_img or self._create_placeholder("Wczytywanie...", "")

    # =============================================================
    # 10. CLOCK MODE
    # =============================================================
    def render_clock_mode(self, config: Dict[str, Any]) -> Image.Image:
        style = config.get("clock_style", "cyberpunk")
        accent = config.get("clock_accent_color", "#00f0ff")
        now = datetime.now()

        if style == "analog":
            return self._render_analog_clock(now, accent)
        elif style == "retro_lcd":
            return self._render_retro_lcd_clock(now, accent)
        elif style == "minimal":
            return self._render_minimal_clock(now, accent)
        else:
            return self._render_cyberpunk_clock(now, accent, config)

    def _render_cyberpunk_clock(self, now: datetime, accent: str, config: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0a0c14")
        draw = ImageDraw.Draw(img)

        # Tech Grid Accents
        draw.rectangle([12, 12, self.width - 12, self.height - 12], outline="#1e293b", width=1)
        draw.line([12, 45, self.width - 12, 45], fill="#1e293b", width=1)

        # Header Badge
        draw.text((20, 20), "NEON CLOCK // TIME CORE", fill=accent, font=get_font(10, bold=True))

        # Big Digital Time
        time_str = now.strftime("%H:%M:%S") if config.get("clock_show_seconds", True) else now.strftime("%H:%M")
        f_time = get_font(42, bold=True)
        draw.text((25, 70), time_str, fill="#ffffff", font=f_time)

        # Date & Day
        date_str = now.strftime("%A, %d %B %Y").upper()
        draw.text((25, 140), date_str[:30], fill=accent, font=get_font(12, bold=True))

        # Bottom Bar
        draw.line([12, 185, self.width - 12, 185], fill="#1e293b", width=1)
        sec_ratio = now.second / 60.0
        self._draw_compact_bar(draw, 25, 198, self.width - 50, 8, sec_ratio * 100, accent)

        return img

    def _render_analog_clock(self, now: datetime, accent: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0a0d14")
        draw = ImageDraw.Draw(img)

        cx, cy, r = self.width // 2, self.height // 2, 95
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#111827", outline=accent, width=2)

        # Dial Ticks
        for h in range(12):
            rad = math.radians(h * 30 - 90)
            x1 = cx + math.cos(rad) * (r - 12)
            y1 = cy + math.sin(rad) * (r - 12)
            x2 = cx + math.cos(rad) * (r - 4)
            y2 = cy + math.sin(rad) * (r - 4)
            draw.line([x1, y1, x2, y2], fill="#e2e8f0", width=2)

        # Hour Hand
        h_deg = (now.hour % 12 + now.minute / 60.0) * 30 - 90
        h_rad = math.radians(h_deg)
        draw.line([cx, cy, cx + math.cos(h_rad) * (r * 0.5), cy + math.sin(h_rad) * (r * 0.5)], fill="#ffffff", width=4)

        # Minute Hand
        m_deg = (now.minute + now.second / 60.0) * 6 - 90
        m_rad = math.radians(m_deg)
        draw.line([cx, cy, cx + math.cos(m_rad) * (r * 0.75), cy + math.sin(m_rad) * (r * 0.75)], fill=accent, width=3)

        # Second Hand
        s_deg = now.second * 6 - 90
        s_rad = math.radians(s_deg)
        draw.line([cx, cy, cx + math.cos(s_rad) * (r * 0.85), cy + math.sin(s_rad) * (r * 0.85)], fill="#ef4444", width=2)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="#ef4444")

        return img

    def _render_retro_lcd_clock(self, now: datetime, accent: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0d1b10")
        draw = ImageDraw.Draw(img)

        # LCD Frame
        draw.rounded_rectangle([15, 25, self.width - 15, self.height - 25], radius=10, fill="#16291a", outline="#2f5737", width=3)
        draw.text((30, 40), "CASIO RETRO LCD", fill="#4ade80", font=get_font(10, bold=True))

        time_str = now.strftime("%H:%M:%S")
        draw.text((35, 75), time_str, fill="#4ade80", font=get_font(38, bold=True))

        date_str = now.strftime("%Y-%m-%d  %a").upper()
        draw.text((35, 145), date_str, fill="#22c55e", font=get_font(14, bold=True))

        return img

    def _render_minimal_clock(self, now: datetime, accent: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#000000")
        draw = ImageDraw.Draw(img)

        time_str = now.strftime("%H:%M")
        sec_str = now.strftime(":%S")
        draw.text((25, 55), time_str, fill="#ffffff", font=get_font(52, bold=True))
        draw.text((220, 75), sec_str, fill=accent, font=get_font(26, bold=True))

        date_str = now.strftime("%d %B, %A").upper()
        draw.text((28, 145), date_str, fill="#94a3b8", font=get_font(12, bold=False))

        return img

    # =============================================================
    # 11. CALENDAR MODE
    # =============================================================
    def render_calendar_mode(self, config: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#080c14")
        draw = ImageDraw.Draw(img)

        now = datetime.now()
        year = now.year
        month = now.month
        today = now.day

        # Header Month & Year
        draw.rectangle([0, 0, self.width, 36], fill="#0f172a")
        month_name = now.strftime("%B %Y").upper()
        draw.text((16, 8), month_name, fill="#00f0ff", font=get_font(14, bold=True))
        draw.text((self.width - 70, 10), now.strftime("%H:%M"), fill="#ffffff", font=get_font(12, bold=True))

        # Days of week
        days_header = ["PO", "WT", "ŚR", "CZ", "PT", "SO", "ND"]
        col_w = (self.width - 24) // 7
        for i, d in enumerate(days_header):
            dx = 12 + i * col_w
            col = "#f43f5e" if i >= 5 else "#94a3b8"
            draw.text((dx + 8, 44), d, fill=col, font=get_font(9, bold=True))

        # Month Matrix
        cal = calendar.monthcalendar(year, month)
        row_y = 66
        f_day = get_font(11, bold=True)

        for week in cal:
            for i, day in enumerate(week):
                if day != 0:
                    dx = 12 + i * col_w
                    if day == today:
                        draw.rounded_rectangle([dx + 2, row_y - 2, dx + col_w - 2, row_y + 18], radius=4, fill="#00f0ff")
                        draw.text((dx + 8, row_y), f"{day:2d}", fill="#000000", font=f_day)
                    else:
                        d_col = "#ff79c6" if i >= 5 else "#ffffff"
                        draw.text((dx + 8, row_y), f"{day:2d}", fill=d_col, font=f_day)
            row_y += 24

        return img

    # =============================================================
    # 12. USAGE GAUGES MODE
    # =============================================================
    def render_usage_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#080b12")
        draw = ImageDraw.Draw(img)

        # Header
        draw.rectangle([0, 0, self.width, 32], fill="#0f172a")
        draw.text((16, 8), "SYSTEM TELEMETRY PRO", fill="#00f0ff", font=get_font(11, bold=True))

        cpu = metrics.get('cpu_percent', 0.0)
        ram = metrics.get('ram_percent', 0.0)
        gpu = metrics.get('gpu_percent', 0.0)

        # 3 Neon Gauge Rings
        self._draw_neon_ring(draw, 55, 95, 38, cpu, "CPU", "#00f0ff")
        self._draw_neon_ring(draw, 160, 95, 38, ram, "RAM", "#d946ef")
        self._draw_neon_ring(draw, 265, 95, 38, gpu, "GPU", "#10b981")

        # Bottom Bar Stats Cards
        draw.rounded_rectangle([15, 160, self.width - 15, self.height - 15], radius=6, fill="#0f172a", outline="#1e293b", width=1)
        
        cpu_t = metrics.get('cpu_temp', 0.0)
        gpu_t = metrics.get('gpu_temp', 0.0)
        nvme_t = metrics.get('nvme_temp', 0.0)
        
        f_sub = get_font(9, bold=True)
        draw.text((25, 172), f"CPU: {cpu_t:.0f}°C", fill="#38bdf8", font=f_sub)
        draw.text((120, 172), f"GPU: {gpu_t:.0f}°C", fill="#d946ef", font=f_sub)
        draw.text((215, 172), f"NVMe: {nvme_t:.0f}°C", fill="#10b981", font=f_sub)

        rx = metrics.get('net_rx_kb', 0.0)
        tx = metrics.get('net_tx_kb', 0.0)
        draw.text((25, 196), f"NET: ▼ {rx:.1f} KB/s   ▲ {tx:.1f} KB/s", fill="#94a3b8", font=get_font(9, bold=False))

        return img

    def _draw_neon_ring(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, val: float, label: str, col: str):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#1e293b", width=4)
        sweep = int(max(0.0, min(100.0, val)) * 3.6)
        
        for deg in range(-90, -90 + sweep, 6):
            rad = math.radians(deg)
            px = cx + math.cos(rad) * r
            py = cy + math.sin(rad) * r
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=col)

        draw.text((cx - 12, cy - 10), f"{val:.0f}%", fill="#ffffff", font=get_font(11, bold=True))
        draw.text((cx - 12, cy + 16), label, fill=col, font=get_font(9, bold=True))

    # =============================================================
    # 13. TEMPERATURES MODE
    # =============================================================
    def render_temperatures_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0a0d14")
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((16, 12), "HARDWARE THERMALS", fill="#f43f5e", font=get_font(12, bold=True))
        draw.line([12, 30, self.width - 12, 30], fill="#1f293d", width=1)

        cpu_t = metrics.get('cpu_temp', 0.0)
        gpu_t = metrics.get('gpu_temp', 0.0)
        nvme_t = metrics.get('nvme_temp', 0.0)

        sensors = [
            ("CPU CORE", cpu_t, "AMD Ryzen / Intel Core"),
            ("GPU DIE", gpu_t, "Radeon / GeForce GPU"),
            ("NVMe SSD", nvme_t, "High-Speed Storage")
        ]

        f_name = get_font(12, bold=True)
        f_sub = get_font(9, bold=False)
        f_temp = get_font(18, bold=True)

        card_y = 38
        for name, temp_val, desc in sensors:
            color = self._get_temp_color(temp_val)
            
            draw.rounded_rectangle([14, card_y, self.width - 14, card_y + 56], radius=8, fill="#121826", outline="#1e293b", width=1)
            draw.rounded_rectangle([14, card_y, 19, card_y + 56], radius=2, fill=color)

            draw.text((28, card_y + 10), name, fill="#ffffff", font=f_name)
            draw.text((28, card_y + 32), desc, fill="#64748b", font=f_sub)

            temp_str = f"{temp_val:.1f}°C"
            draw.text((self.width - 92, card_y + 16), temp_str, fill=color, font=f_temp)

            card_y += 64

        return img

    def _get_temp_color(self, temp: float) -> str:
        if temp < 55.0:
            return "#10b981"
        elif temp < 75.0:
            return "#f59e0b"
        else:
            return "#ef4444"

    # =============================================================
    # 14. CUSTOM / HYBRID SUPER DASHBOARD
    # =============================================================
    def render_custom_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        bg_type = config.get("custom_background_type", "gradient")
        
        if bg_type == "image":
            img = self._get_custom_bg_image(config.get("custom_bg_image", ""))
        else:
            img = Image.new("RGBA", (self.width, self.height), "#080c14")
            draw_bg = ImageDraw.Draw(img)
            draw_bg.rectangle([0, 0, self.width, 36], fill="#0f1626")
            draw_bg.line([0, 36, self.width, 36], fill="#1e293b", width=1)

        draw = ImageDraw.Draw(img)
        now = datetime.now()

        # 1. Compact Header / Clock
        if config.get("custom_show_clock", True):
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%d.%m")
            f_clk = get_font(15, bold=True)
            f_dt = get_font(12, bold=False)
            
            draw.text((14, 8), time_str, fill="#00f0ff", font=f_clk)
            draw.text((self.width - 50, 10), date_str, fill="#94a3b8", font=f_dt)

        # 2. Performance Bars
        y_pos = 46
        f_stat = get_font(10, bold=True)
        f_stat_val = get_font(10, bold=False)

        # CPU Bar
        if config.get("custom_show_cpu_bar", True):
            cpu = metrics.get('cpu_percent', 0.0)
            draw.text((14, y_pos), "CPU", fill="#38bdf8", font=f_stat)
            draw.text((self.width - 50, y_pos), f"{cpu:.0f}%", fill="#ffffff", font=f_stat_val)
            self._draw_compact_bar(draw, 50, y_pos + 2, self.width - 110, 8, cpu, "#00f0ff")
            y_pos += 24

        # RAM Bar
        if config.get("custom_show_ram_bar", True):
            ram = metrics.get('ram_percent', 0.0)
            draw.text((14, y_pos), "RAM", fill="#d946ef", font=f_stat)
            draw.text((self.width - 50, y_pos), f"{ram:.0f}%", fill="#ffffff", font=f_stat_val)
            self._draw_compact_bar(draw, 50, y_pos + 2, self.width - 110, 8, ram, "#d946ef")
            y_pos += 24

        # GPU Bar
        if config.get("custom_show_gpu_bar", True):
            gpu = metrics.get('gpu_percent', 0.0)
            draw.text((14, y_pos), "GPU", fill="#10b981", font=f_stat)
            draw.text((self.width - 50, y_pos), f"{gpu:.0f}%", fill="#ffffff", font=f_stat_val)
            self._draw_compact_bar(draw, 50, y_pos + 2, self.width - 110, 8, gpu, "#10b981")
            y_pos += 26

        # 3. Temperatures row
        if config.get("custom_show_temps", True) and y_pos < self.height - 40:
            draw.rounded_rectangle([14, y_pos, self.width - 14, self.height - 12], radius=6, fill="#0c121e", outline="#1e293b", width=1)
            cpu_t = metrics.get('cpu_temp', 0.0)
            gpu_t = metrics.get('gpu_temp', 0.0)
            nvme_t = metrics.get('nvme_temp', 0.0)

            f_t = get_font(10, bold=True)
            f_tv = get_font(13, bold=True)
            
            draw.text((24, y_pos + 6), "CPU", fill="#94a3b8", font=f_t)
            draw.text((24, y_pos + 22), f"{cpu_t:.0f}°C", fill="#38bdf8", font=f_tv)

            draw.text((120, y_pos + 6), "GPU", fill="#94a3b8", font=f_t)
            draw.text((120, y_pos + 22), f"{gpu_t:.0f}°C", fill="#d946ef", font=f_tv)

            draw.text((215, y_pos + 6), "NVMe", fill="#94a3b8", font=f_t)
            draw.text((215, y_pos + 22), f"{nvme_t:.0f}°C", fill="#10b981", font=f_tv)

        return img

    # =============================================================
    # UTILITY METHODS
    # =============================================================
    def _draw_compact_bar(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, val: float, color: str):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill="#1e293b")
        fill_w = int(max(0.0, min(100.0, val)) / 100.0 * w)
        if fill_w > 0:
            draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=3, fill=color)

    def _fit_image(self, img: Image.Image, target_w: int, target_h: int, mode: str) -> Image.Image:
        iw, ih = img.size
        if mode == "stretch":
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        elif mode == "contain":
            ratio = min(target_w / iw, target_h / ih)
            nw, nh = int(iw * ratio), int(ih * ratio)
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            bg = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 255))
            bg.paste(resized, ((target_w - nw) // 2, (target_h - nh) // 2))
            return bg
        else:  # cover
            ratio = max(target_w / iw, target_h / ih)
            nw, nh = int(iw * ratio), int(ih * ratio)
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            x0 = (nw - target_w) // 2
            y0 = (nh - target_h) // 2
            return resized.crop((x0, y0, x0 + target_w, y0 + target_h))

    def _get_custom_bg_image(self, path: str) -> Image.Image:
        if not path or not os.path.exists(path):
            img = Image.new("RGBA", (self.width, self.height), "#080c14")
            return img
        if self.bg_image_path == path and self.bg_image_cached is not None:
            return self.bg_image_cached.copy()
        try:
            with Image.open(path) as raw:
                self.bg_image_path = path
                self.bg_image_cached = self._fit_image(raw.convert("RGBA"), self.width, self.height, "cover")
                return self.bg_image_cached.copy()
        except Exception:
            return Image.new("RGBA", (self.width, self.height), "#080c14")

    def _create_placeholder(self, title: str, subtitle: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#080c14")
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, self.width - 10, self.height - 10], outline="#1e293b", width=1)
        draw.text((self.width // 2 - 60, self.height // 2 - 20), title, fill="#00f0ff", font=get_font(12, bold=True))
        draw.text((self.width // 2 - 80, self.height // 2 + 10), subtitle, fill="#64748b", font=get_font(9, bold=False))
        return img
