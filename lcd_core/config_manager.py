import os
import json
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "current_mode": "retro_synthwave",  # retro_synthwave, matrix_rain, audio_visualizer, dual_gauges, pomodoro, scifi_terminal, custom, usage, temperatures, clock, calendar, image, gif, slideshow
    "width": 320,
    "height": 240,
    "fps": 30,
    "brightness": 200,
    "theme": "dark_cyberpunk",
    
    # 1. Retro Synthwave HUD
    "synthwave_theme": "neon_sunset",  # neon_sunset, cyber_grid, outrun_purple, laser_blue
    "synthwave_show_sun": True,
    "synthwave_show_clock": True,
    "synthwave_show_telemetry": True,
    "synthwave_custom_text": "CYBERPUNK 2077",

    # 2. Matrix Digital Rain HUD
    "matrix_color": "matrix_green",  # matrix_green, amber_crt, cyber_cyan, red_alert
    "matrix_speed": 1.0,
    "matrix_show_clock": True,
    "matrix_show_stats": True,

    # 3. Audio VU Meter & Spectrum Visualizer
    "audio_style": "spectrum_bars",  # spectrum_bars, dual_vu_meter, waveform_pulse
    "audio_color": "neon_gradient",  # neon_gradient, cyber_cyan, fire_amber, vaporwave
    "audio_sensitivity": 1.0,
    "audio_show_peaks": True,

    # 4. Dual Tachometer Racing Cluster
    "gauges_style": "sport_tachometer",  # sport_tachometer, turbo_boost, classic_analog
    "gauges_color": "amber_red",  # amber_red, neon_cyan, emerald_green, hyper_purple
    "gauges_show_temps": True,
    "gauges_show_ram": True,

    # 5. Pomodoro & Focus Timer
    "pomodoro_focus_min": 25,
    "pomodoro_break_min": 5,
    "pomodoro_state": "stopped",  # running, paused, stopped
    "pomodoro_mode": "focus",  # focus, break
    "pomodoro_time_left": 1500,  # seconds
    "pomodoro_rounds_done": 0,
    "pomodoro_task_name": "Deep Work Session",

    # 6. Sci-Fi Starship / Terminal HUD
    "scifi_theme": "tactical_blue",  # tactical_blue, red_alert, alien_emerald, orange_hazard
    "scifi_show_radar": True,
    "scifi_ship_name": "GK104-PRO ORBITAL",
    "scifi_show_diagnostics": True,

    # 7. Image Settings
    "image_path": "",
    "image_fit": "cover",  # cover, contain, stretch
    "image_brightness": 100,
    "image_contrast": 100,
    
    # 8. GIF Settings
    "gif_path": "",
    "gif_speed": 1.0,
    
    # 9. Slideshow Settings
    "slideshow_images": [],
    "slideshow_interval": 5,
    "slideshow_shuffle": False,
    "slideshow_transition": "instant",
    
    # 10. Clock Settings
    "clock_style": "cyberpunk",  # cyberpunk, digital_modern, retro_lcd, minimal, analog
    "clock_24h": True,
    "clock_show_seconds": True,
    "clock_show_date": True,
    "clock_accent_color": "#00f0ff",
    
    # 11. Calendar Settings
    "calendar_theme": "neon_cyan",  # neon_cyan, purple_matrix, amoled_gold, minimal_mono
    "calendar_show_clock": True,
    
    # 12. Resource Usage Settings
    "usage_style": "neon_rings",  # neon_rings, bars, cards
    "usage_show_cpu": True,
    "usage_show_ram": True,
    "usage_show_gpu": True,
    "usage_show_net": True,
    
    # 13. Temperatures Settings
    "temp_style": "cards",  # cards, vertical_bars, radial
    "temp_show_cpu": True,
    "temp_show_gpu": True,
    "temp_show_nvme": True,
    "temp_warn_cpu": 75,
    "temp_crit_cpu": 85,
    
    # 14. Custom / Hybrid Dashboard Settings
    "custom_background_type": "gradient",  # gradient, solid, image
    "custom_bg_image": "",
    "custom_show_clock": True,
    "custom_clock_compact": True,
    "custom_show_cpu_bar": True,
    "custom_show_ram_bar": True,
    "custom_show_gpu_bar": True,
    "custom_show_temps": True,
    "custom_show_net": False,
    "custom_user_title": "MY RIG STATUS",
    
    # USB Streamer Settings
    "usb_stream_port": "/dev/ttyACM0",
    "usb_stream_baud": 115200,
    "usb_stream_fps": 30,
    "usb_stream_quality": 85,
    "usb_stream_auto_start": True
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
