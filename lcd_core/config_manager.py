import os
import json
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "current_mode": "custom",  # image, gif, slideshow, clock, calendar, usage, temperatures, custom
    "width": 320,
    "height": 240,
    "fps": 30,
    "theme": "dark_cyberpunk",
    
    # Image Settings
    "image_path": "",
    "image_fit": "cover",  # cover, contain, stretch
    "image_brightness": 100,
    "image_contrast": 100,
    
    # GIF Settings
    "gif_path": "",
    "gif_speed": 1.0,
    
    # Slideshow Settings
    "slideshow_images": [],
    "slideshow_interval": 5,
    "slideshow_shuffle": False,
    "slideshow_transition": "instant",  # instant, fade
    
    # Clock Settings
    "clock_style": "cyberpunk",  # cyberpunk, digital_modern, retro_lcd, minimal, analog
    "clock_24h": True,
    "clock_show_seconds": True,
    "clock_show_date": True,
    "clock_accent_color": "#00f0ff",
    
    # Calendar Settings
    "calendar_theme": "neon_cyan",  # neon_cyan, purple_matrix, amoled_gold, minimal_mono
    "calendar_show_clock": True,
    
    # Resource Usage Settings
    "usage_style": "neon_rings",  # neon_rings, bars, cards
    "usage_show_cpu": True,
    "usage_show_ram": True,
    "usage_show_gpu": True,
    "usage_show_net": True,
    
    # Temperatures Settings
    "temp_style": "cards",  # cards, vertical_bars, radial
    "temp_show_cpu": True,
    "temp_show_gpu": True,
    "temp_show_nvme": True,
    "temp_warn_cpu": 75,
    "temp_crit_cpu": 85,
    
    # Custom / Hybrid Dashboard Settings
    "custom_background_type": "gradient",  # gradient, solid, image
    "custom_bg_image": "",
    "custom_show_clock": True,
    "custom_clock_compact": True,
    "custom_show_cpu_bar": True,
    "custom_show_ram_bar": True,
    "custom_show_gpu_bar": True,
    "custom_show_temps": True,
    "custom_show_net": False,
    
    # Network & Serial
    "tcp_server_enabled": True,
    "tcp_port": 1648,
    "tcp_host": "0.0.0.0",
    "serial_port": "/dev/ttyACM0",
    "serial_baudrate": 115200,
    "serial_auto_connect": False
}

class ConfigManager:
    def __init__(self, config_dir: str = "~/.config/skyloong_lcd"):
        self.config_dir = os.path.expanduser(config_dir)
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.config: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
        except Exception as e:
            print(f"[ConfigManager] Error loading config: {e}")

    def save(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        self.config[key] = value
        if auto_save:
            self.save()
