import os
import time
import math
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
    Renders high-quality 240x240 (or custom size) frames for the Skyloong LCD display.
    Supports Photos, Animated GIFs, Slideshows, Clocks, Calendars, Usage Gauges,
    Temperatures, and Hybrid/Custom Multi-Widget Dashboards.
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
        
        # Last rendered frame
        self.current_frame: Optional[Image.Image] = None

    def get_current_frame(self) -> Optional[Image.Image]:
        """Returns the most recently rendered frame."""
        return self.current_frame

    def render(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        """Main dispatcher based on current_mode."""
        mode = config.get("current_mode", "custom")
        self.width = config.get("width", 320)
        self.height = config.get("height", 240)

        img: Image.Image
        if mode == "image":
            img = self.render_image_mode(config)
        elif mode == "gif":
            img = self.render_gif_mode(config)
        elif mode == "slideshow":
            img = self.render_slideshow_mode(config)
        elif mode == "clock":
            img = self.render_clock_mode(config)
        elif mode == "calendar":
            img = self.render_calendar_mode(config)
        elif mode == "usage":
            img = self.render_usage_mode(config, metrics)
        elif mode == "temperatures":
            img = self.render_temperatures_mode(config, metrics)
        elif mode == "custom":
            img = self.render_custom_mode(config, metrics)
        else:
            img = self.render_custom_mode(config, metrics)

        self.current_frame = img
        return img

    # -------------------------------------------------------------
    # 1. IMAGE MODE
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 2. GIF MODE
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 3. SLIDESHOW MODE
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 4. CLOCK MODE
    # -------------------------------------------------------------
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
        else: # cyberpunk / digital_modern
            return self._render_cyberpunk_clock(now, accent, config)

    def _render_cyberpunk_clock(self, now: datetime, accent: str, config: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0a0c14")
        draw = ImageDraw.Draw(img)

        # Background glowing tech accents
        draw.rectangle([6, 6, self.width - 6, self.height - 6], outline="#1b2234", width=2)
        draw.line([10, 10, 30, 10], fill=accent, width=2)
        draw.line([10, 10, 10, 30], fill=accent, width=2)
        draw.line([self.width - 30, self.height - 10, self.width - 10, self.height - 10], fill=accent, width=2)
        draw.line([self.width - 10, self.height - 30, self.width - 10, self.height - 10], fill=accent, width=2)

        # Header tag
        f_small = get_font(11, bold=True)
        draw.text((16, 14), "SKYLOONG // TIME", fill="#4f5d7e", font=f_small)

        # Time String
        f_time = get_font(42, bold=True)
        time_str = now.strftime("%H:%M")
        sec_str = now.strftime("%S")
        
        # Center Time
        draw.text((24, 60), time_str, fill="#ffffff", font=f_time)
        f_sec = get_font(20, bold=True)
        draw.text((165, 68), f":{sec_str}", fill=accent, font=f_sec)

        # Horizontal progress bar for seconds (0-60)
        sec_val = now.second + now.microsecond / 1_000_000.0
        bar_w = int((self.width - 40) * (sec_val / 60.0))
        draw.rounded_rectangle([20, 130, self.width - 20, 136], radius=3, fill="#151b2a")
        if bar_w > 0:
            draw.rounded_rectangle([20, 130, 20 + bar_w, 136], radius=3, fill=accent)

        # Date & Day
        days_pl = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        day_name = days_pl[now.weekday()].upper()
        date_str = now.strftime("%d.%m.%Y")
        
        f_day = get_font(13, bold=True)
        f_date = get_font(14, bold=False)
        
        draw.text((20, 155), day_name, fill=accent, font=f_day)
        draw.text((20, 178), date_str, fill="#94a3b8", font=f_date)

        # System Status Tag
        draw.rounded_rectangle([self.width - 75, 165, self.width - 20, 195], radius=6, fill="#131b2e", outline="#253554")
        f_chip = get_font(10, bold=True)
        draw.text((self.width - 68, 173), "ONLINE", fill="#10b981", font=f_chip)

        return img

    def _render_retro_lcd_clock(self, now: datetime, accent: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0d1b10")
        draw = ImageDraw.Draw(img)

        # Green LCD grid pattern
        for y in range(0, self.height, 4):
            draw.line([0, y, self.width, y], fill="#112415", width=1)

        draw.rounded_rectangle([10, 10, self.width - 10, self.height - 10], radius=8, outline="#1f4f29", width=2)

        f_title = get_font(12, bold=True)
        draw.text((20, 20), "DIGITAL QUARTZ", fill="#39a852", font=f_title)

        f_time = get_font(38, bold=True)
        time_str = now.strftime("%H:%M:%S")
        draw.text((20, 75), time_str, fill="#4aff75", font=f_time)

        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        draw.text((20, 150), f"{days[now.weekday()]}  {now.strftime('%d/%m/%Y')}", fill="#39a852", font=get_font(16, bold=True))

        return img

    def _render_analog_clock(self, now: datetime, accent: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0f172a")
        draw = ImageDraw.Draw(img)

        cx, cy = self.width // 2, self.height // 2
        radius = int(min(cx, cy) * 0.85)

        # Dial border
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline="#334155", width=3)
        draw.ellipse([cx - radius + 4, cy - radius + 4, cx + radius - 4, cy + radius - 4], fill="#1e293b")

        # Ticks
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            inner_r = radius - 12 if (i % 3 == 0) else radius - 7
            x1 = cx + int(math.cos(angle) * (radius - 2))
            y1 = cy + int(math.sin(angle) * (radius - 2))
            x2 = cx + int(math.cos(angle) * inner_r)
            y2 = cy + int(math.sin(angle) * inner_r)
            w = 3 if (i % 3 == 0) else 1
            color = accent if (i % 3 == 0) else "#64748b"
            draw.line([x1, y1, x2, y2], fill=color, width=w)

        # Hour Hand
        h_val = (now.hour % 12) + now.minute / 60.0
        h_angle = math.radians(h_val * 30 - 90)
        hx = cx + int(math.cos(h_angle) * (radius * 0.5))
        hy = cy + int(math.sin(h_angle) * (radius * 0.5))
        draw.line([cx, cy, hx, hy], fill="#ffffff", width=4)

        # Minute Hand
        m_val = now.minute + now.second / 60.0
        m_angle = math.radians(m_val * 6 - 90)
        mx = cx + int(math.cos(m_angle) * (radius * 0.72))
        my = cy + int(math.sin(m_angle) * (radius * 0.72))
        draw.line([cx, cy, mx, my], fill="#cbd5e1", width=3)

        # Second Hand
        s_val = now.second + now.microsecond / 1_000_000.0
        s_angle = math.radians(s_val * 6 - 90)
        sx = cx + int(math.cos(s_angle) * (radius * 0.8))
        sy = cy + int(math.sin(s_angle) * (radius * 0.8))
        draw.line([cx, cy, sx, sy], fill=accent, width=2)

        # Center cap
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=accent)

        return img

    def _render_minimal_clock(self, now: datetime, accent: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#000000")
        draw = ImageDraw.Draw(img)

        f_huge = get_font(52, bold=True)
        draw.text((25, 40), now.strftime("%H"), fill="#ffffff", font=f_huge)
        draw.text((25, 100), now.strftime("%M"), fill=accent, font=f_huge)

        f_sub = get_font(13, bold=False)
        draw.text((120, 60), f":{now.strftime('%S')}", fill="#666666", font=get_font(20, bold=True))
        draw.text((120, 120), now.strftime("%a %d %b"), fill="#999999", font=f_sub)

        return img

    # -------------------------------------------------------------
    # 5. CALENDAR MODE
    # -------------------------------------------------------------
    def render_calendar_mode(self, config: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0d1117")
        draw = ImageDraw.Draw(img)

        now = datetime.now()
        year, month, today = now.year, now.month, now.day

        months_pl = [
            "", "STYCZEŃ", "LUTY", "MARZEC", "KWIECIEŃ", "MAJ", "CZERWIEC",
            "LIPIEC", "SIERPIEŃ", "WRZESIEŃ", "PAŹDZIERNIK", "LISTOPAD", "GRUDZIEŃ"
        ]

        # Top Month Bar
        draw.rounded_rectangle([10, 10, self.width - 10, 42], radius=6, fill="#161b22", outline="#30363d")
        f_header = get_font(13, bold=True)
        draw.text((20, 18), f"{months_pl[month]} {year}", fill="#58a6ff", font=f_header)

        # Mini clock in top right
        f_clock = get_font(12, bold=True)
        draw.text((self.width - 65, 18), now.strftime("%H:%M"), fill="#8b949e", font=f_clock)

        # Weekdays header
        headers = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
        col_w = (self.width - 24) / 7.0
        start_y = 52
        f_day_head = get_font(10, bold=True)

        for i, h in enumerate(headers):
            x = 12 + int(i * col_w) + int(col_w / 4)
            color = "#f85149" if i >= 5 else "#8b949e"
            draw.text((x, start_y), h, fill=color, font=f_day_head)

        # Calendar Matrix
        cal = calendar.monthcalendar(year, month)
        f_num = get_font(11, bold=False)
        f_num_today = get_font(11, bold=True)

        row_h = 24
        for r_idx, week in enumerate(cal):
            for c_idx, day_val in enumerate(week):
                if day_val == 0:
                    continue
                x_box = int(12 + c_idx * col_w)
                y_box = start_y + 18 + r_idx * row_h
                
                if day_val == today:
                    # Highlight Today
                    draw.rounded_rectangle([x_box + 1, y_box - 2, x_box + int(col_w) - 3, y_box + 16], radius=4, fill="#1f6feb")
                    draw.text((x_box + 7, y_box), str(day_val), fill="#ffffff", font=f_num_today)
                else:
                    color = "#f85149" if c_idx >= 5 else "#c9d1d9"
                    offset_x = 7 if day_val >= 10 else 10
                    draw.text((x_box + offset_x, y_box), str(day_val), fill=color, font=f_num)

        # Bottom info bar
        draw.line([12, self.height - 24, self.width - 12, self.height - 24], fill="#21262d", width=1)
        f_bot = get_font(10, bold=False)
        week_num = now.isocalendar()[1]
        draw.text((14, self.height - 18), f"Tydzień {week_num}", fill="#8b949e", font=f_bot)
        draw.text((self.width - 80, self.height - 18), now.strftime("%A")[:3].upper(), fill="#58a6ff", font=f_bot)

        return img

    # -------------------------------------------------------------
    # 6. RESOURCE USAGE MODE (CPU, RAM, GPU)
    # -------------------------------------------------------------
    def render_usage_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        style = config.get("usage_style", "neon_rings")
        if style == "bars":
            return self._render_usage_bars(metrics)
        else:
            return self._render_usage_rings(metrics)

    def _render_usage_rings(self, metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#090d16")
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((15, 12), "SYSTEM RESOURCE USAGE", fill="#4f5d7e", font=get_font(11, bold=True))
        draw.line([12, 28, self.width - 12, 28], fill="#161f30", width=1)

        cpu = metrics.get('cpu_percent', 0.0)
        ram = metrics.get('ram_percent', 0.0)
        gpu = metrics.get('gpu_percent', 0.0)

        # 3 Circular Gauges Side-by-Side or Centered
        # 1. CPU Gauge (Left Top)
        self._draw_mini_gauge(draw, 50, 75, 34, cpu, "CPU", f"{cpu:.0f}%", "#00f0ff")

        # 2. RAM Gauge (Right Top)
        self._draw_mini_gauge(draw, 155, 75, 34, ram, "RAM", f"{ram:.0f}%", "#d946ef")

        # 3. GPU Gauge (Center Bottom)
        self._draw_mini_gauge(draw, 102, 160, 36, gpu, "GPU", f"{gpu:.0f}%", "#10b981")

        # Extra metrics
        ram_used = metrics.get('ram_used_gb', 0.0)
        ram_total = metrics.get('ram_total_gb', 0.0)
        f_sub = get_font(10, bold=False)
        draw.text((16, self.height - 18), f"RAM: {ram_used:.1f}/{ram_total:.1f} GB", fill="#64748b", font=f_sub)
        draw.text((self.width - 70, self.height - 18), f"UP: {metrics.get('uptime_str', '')}", fill="#64748b", font=f_sub)

        return img

    def _draw_mini_gauge(self, draw: ImageDraw.ImageDraw, x: int, y: int, r: int, pct: float, label: str, val_str: str, color: str):
        # Background arc
        draw.ellipse([x - r, y - r, x + r, y + r], outline="#151d2f", width=6)
        
        # Value arc
        sweep = max(1, int((pct / 100.0) * 360))
        draw.arc([x - r, y - r, x + r, y + r], start=-90, end=-90 + sweep, fill=color, width=6)

        # Text inside
        f_lbl = get_font(9, bold=True)
        f_val = get_font(13, bold=True)
        draw.text((x - 12, y - 14), label, fill="#94a3b8", font=f_lbl)
        draw.text((x - 14, y + 2), val_str, fill="#ffffff", font=f_val)

    def _render_usage_bars(self, metrics: Dict[str, Any]) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#080c14")
        draw = ImageDraw.Draw(img)

        draw.text((16, 14), "PERFORMANCE MONITOR", fill="#38bdf8", font=get_font(12, bold=True))

        items = [
            ("CPU USAGE", metrics.get('cpu_percent', 0.0), "#00f0ff", f"{metrics.get('cpu_percent', 0):.1f}%"),
            ("RAM USAGE", metrics.get('ram_percent', 0.0), "#d946ef", f"{metrics.get('ram_percent', 0):.1f}% ({metrics.get('ram_used_gb', 0):.1f}G)"),
            ("GPU LOAD", metrics.get('gpu_percent', 0.0), "#10b981", f"{metrics.get('gpu_percent', 0):.1f}%"),
        ]

        f_label = get_font(11, bold=True)
        f_val = get_font(11, bold=False)

        start_y = 48
        for label, val, color, text_val in items:
            draw.text((16, start_y), label, fill="#94a3b8", font=f_label)
            draw.text((self.width - 100, start_y), text_val, fill="#ffffff", font=f_val)
            
            # Progress bar
            bar_y = start_y + 18
            draw.rounded_rectangle([16, bar_y, self.width - 16, bar_y + 10], radius=4, fill="#161f30")
            w = int((self.width - 32) * (val / 100.0))
            if w > 0:
                draw.rounded_rectangle([16, bar_y, 16 + w, bar_y + 10], radius=4, fill=color)
            start_y += 48

        # Network transfer row
        rx = metrics.get('net_rx_kb', 0.0)
        tx = metrics.get('net_tx_kb', 0.0)
        f_net = get_font(10, bold=False)
        draw.text((16, self.height - 24), f"▼ {rx:.1f} KB/s   ▲ {tx:.1f} KB/s", fill="#64748b", font=f_net)

        return img

    # -------------------------------------------------------------
    # 7. TEMPERATURES MODE (CPU, GPU, NVME)
    # -------------------------------------------------------------
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
            ("CPU TEMP", cpu_t, "AMD / Intel Core"),
            ("GPU TEMP", gpu_t, "Radeon / Geforce"),
            ("NVMe SSD", nvme_t, "High-Speed Storage")
        ]

        f_name = get_font(12, bold=True)
        f_sub = get_font(9, bold=False)
        f_temp = get_font(18, bold=True)

        card_y = 40
        for name, temp_val, desc in sensors:
            color = self._get_temp_color(temp_val)
            
            # Card background
            draw.rounded_rectangle([14, card_y, self.width - 14, card_y + 54], radius=8, fill="#121826", outline="#1e293b", width=1)
            
            # Accent pill / left marker
            draw.rounded_rectangle([14, card_y, 19, card_y + 54], radius=2, fill=color)

            # Name and subtext
            draw.text((28, card_y + 8), name, fill="#ffffff", font=f_name)
            draw.text((28, card_y + 28), desc, fill="#64748b", font=f_sub)

            # Big Temp Value
            temp_str = f"{temp_val:.1f}°C"
            draw.text((self.width - 88, card_y + 14), temp_str, fill=color, font=f_temp)

            card_y += 62

        return img

    def _get_temp_color(self, temp: float) -> str:
        if temp < 55.0:
            return "#10b981"  # Emerald Green
        elif temp < 75.0:
            return "#f59e0b"  # Amber / Orange
        else:
            return "#ef4444"  # Hot Red

    # -------------------------------------------------------------
    # 8. CUSTOM / HYBRID DASHBOARD (DO WYBORU)
    # -------------------------------------------------------------
    def render_custom_mode(self, config: Dict[str, Any], metrics: Dict[str, Any]) -> Image.Image:
        bg_type = config.get("custom_background_type", "gradient")
        
        # Base Background
        if bg_type == "image":
            img = self._get_custom_bg_image(config.get("custom_bg_image", ""))
        else:
            img = Image.new("RGBA", (self.width, self.height), "#080c14")
            # Cyberpunk subtle grid / background accents
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
            y_pos += 22

        # RAM Bar
        if config.get("custom_show_ram_bar", True):
            ram = metrics.get('ram_percent', 0.0)
            draw.text((14, y_pos), "RAM", fill="#d946ef", font=f_stat)
            draw.text((self.width - 50, y_pos), f"{ram:.0f}%", fill="#ffffff", font=f_stat_val)
            self._draw_compact_bar(draw, 50, y_pos + 2, self.width - 110, 8, ram, "#d946ef")
            y_pos += 22

        # GPU Bar
        if config.get("custom_show_gpu_bar", True):
            gpu = metrics.get('gpu_percent', 0.0)
            draw.text((14, y_pos), "GPU", fill="#10b981", font=f_stat)
            draw.text((self.width - 50, y_pos), f"{gpu:.0f}%", fill="#ffffff", font=f_stat_val)
            self._draw_compact_bar(draw, 50, y_pos + 2, self.width - 110, 8, gpu, "#10b981")
            y_pos += 24

        # 3. Temperatures Section
        if config.get("custom_show_temps", True):
            draw.line([12, y_pos, self.width - 12, y_pos], fill="#161f30", width=1)
            y_pos += 8
            
            draw.text((14, y_pos), "TEMPERATURES", fill="#64748b", font=get_font(9, bold=True))
            y_pos += 16

            cpu_t = metrics.get('cpu_temp', 0.0)
            gpu_t = metrics.get('gpu_temp', 0.0)
            nvme_t = metrics.get('nvme_temp', 0.0)

            # 3 Mini Temp Badges
            badge_w = (self.width - 36) // 3
            badges = [
                ("CPU", cpu_t),
                ("GPU", gpu_t),
                ("NVMe", nvme_t)
            ]

            f_b_lbl = get_font(9, bold=True)
            f_b_val = get_font(12, bold=True)

            for i, (b_lbl, b_val) in enumerate(badges):
                bx = 14 + i * (badge_w + 4)
                color = self._get_temp_color(b_val)
                draw.rounded_rectangle([bx, y_pos, bx + badge_w, y_pos + 42], radius=6, fill="#101726", outline="#1e293b")
                draw.text((bx + 8, y_pos + 4), b_lbl, fill="#94a3b8", font=f_b_lbl)
                draw.text((bx + 6, y_pos + 20), f"{b_val:.0f}°C", fill=color, font=f_b_val)

        # 4. Footer Info / Network
        f_foot = get_font(9, bold=False)
        rx = metrics.get('net_rx_kb', 0.0)
        tx = metrics.get('net_tx_kb', 0.0)
        draw.text((14, self.height - 16), f"▼ {rx:.0f}KB/s ▲ {tx:.0f}KB/s", fill="#475569", font=f_foot)
        draw.text((self.width - 70, self.height - 16), "GK104 PRO", fill="#00f0ff", font=f_foot)

        return img

    def _draw_compact_bar(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, pct: float, color: str):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill="#161f30")
        fill_w = max(0, min(w, int(w * (pct / 100.0))))
        if fill_w > 0:
            draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=3, fill=color)

    def _get_custom_bg_image(self, path: str) -> Image.Image:
        if path and os.path.exists(path):
            if self.bg_image_path != path or self.bg_image_cached is None:
                try:
                    with Image.open(path) as raw:
                        img = raw.convert("RGBA")
                        img = self._fit_image(img, self.width, self.height, "cover")
                        # Add a dark translucent overlay for text readability
                        dark_overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 160))
                        img = Image.alpha_composite(img, dark_overlay)
                        self.bg_image_cached = img
                        self.bg_image_path = path
                except Exception:
                    self.bg_image_cached = None
        if self.bg_image_cached:
            return self.bg_image_cached.copy()
        return Image.new("RGBA", (self.width, self.height), "#080c14")

    # -------------------------------------------------------------
    # HELPER UTILITIES
    # -------------------------------------------------------------
    def _fit_image(self, img: Image.Image, target_w: int, target_h: int, fit: str) -> Image.Image:
        """Scales image according to cover/contain/stretch."""
        if fit == "stretch":
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        iw, ih = img.size
        if iw == 0 or ih == 0:
            return Image.new("RGBA", (target_w, target_h), "#000000")

        if fit == "contain":
            ratio = min(target_w / iw, target_h / ih)
            nw, nh = int(iw * ratio), int(ih * ratio)
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            bg = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 255))
            offset_x = (target_w - nw) // 2
            offset_y = (target_h - nh) // 2
            bg.paste(resized, (offset_x, offset_y), resized if resized.mode == "RGBA" else None)
            return bg
        else: # cover
            ratio = max(target_w / iw, target_h / ih)
            nw, nh = int(iw * ratio), int(ih * ratio)
            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - target_w) // 2
            top = (nh - target_h) // 2
            return resized.crop((left, top, left + target_w, top + target_h))

    def _create_placeholder(self, title: str, subtitle: str) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), "#0d1117")
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, self.width - 10, self.height - 10], outline="#21262d", width=2)
        
        f_t = get_font(14, bold=True)
        f_s = get_font(10, bold=False)
        
        draw.text((25, self.height // 2 - 20), title, fill="#58a6ff", font=f_t)
        draw.text((25, self.height // 2 + 10), subtitle, fill="#8b949e", font=f_s)
        return img
