import os
import io
from typing import Dict, Any, Optional
from PIL import Image, ImageQt

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QButtonGroup, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QPixmap, QImage

from lcd_core.screen_renderer import ScreenRenderer
from lcd_core.system_monitor import SystemMonitor

SCREENS_CATALOG = [
    {
        "id": "mario",
        "title": "Super Mario Retro",
        "icon": "🍄",
        "category": "games",
        "category_label": "🎮 Gry & Retro",
        "badge": "GRYWALNY",
        "desc": "Interaktywny świat 8-bit Mario z fizyką skoków, wrogami, monetami i telemetrią."
    },
    {
        "id": "doom",
        "title": "DOOM Classic 1993",
        "icon": "💀",
        "category": "games",
        "category_label": "🎮 Gry & Retro",
        "badge": "GRYWALNY",
        "desc": "Grywalny korytarz 3D, strzelba, demony i animowany status bar z twarzą Doomgaya."
    },
    {
        "id": "retro_synthwave",
        "title": "Retro Synthwave HUD",
        "icon": "🌆",
        "category": "creative",
        "category_label": "✨ Efektowne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Perspektywiczny neonowy grid, słońce retro, zegar cyberpunk oraz telemetria."
    },
    {
        "id": "matrix_rain",
        "title": "Matrix Digital Rain",
        "icon": "🟢",
        "category": "creative",
        "category_label": "✨ Efektowne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Spływający zielony deszcz glifów Matrix z wbudowaną konsolą zegara."
    },
    {
        "id": "audio_visualizer",
        "title": "Audio Spectrum / VU",
        "icon": "🎵",
        "category": "creative",
        "category_label": "✨ Efektowne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Wielopasmowy analizator widma częstotliwości audio ze wskaźnikami Peak."
    },
    {
        "id": "dual_gauges",
        "title": "Dual Tachometers",
        "icon": "🏎️",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "NOWOŚĆ",
        "desc": "Podwójne analogowe zegary obrotomierza dla CPU i GPU oraz temperatury."
    },
    {
        "id": "pomodoro",
        "title": "Pomodoro Focus Timer",
        "icon": "⏱️",
        "category": "tools",
        "category_label": "🕒 Czas & Narzędzia",
        "badge": "NOWOŚĆ",
        "desc": "Okrągły zegar sesji skupienia (25 min) i przerw z licznikiem rund."
    },
    {
        "id": "scifi_terminal",
        "title": "Sci-Fi Starship HUD",
        "icon": "🚀",
        "category": "creative",
        "category_label": "✨ Efektowne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Panel dowodzenia z obrotowym radarem taktycznym i stanem reaktora."
    },
    {
        "id": "custom",
        "title": "Super Dashboard",
        "icon": "🧩",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "POPULARNY",
        "desc": "Modyfikowalny pulpit hybrydowy: zegar, słupki CPU/RAM/GPU i tapeta."
    },
    {
        "id": "usage",
        "title": "Telemetria Pierścienie",
        "icon": "📊",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "",
        "desc": "Trzy neonowe pierścienie obciążenia CPU, RAM i GPU z prędkością sieci."
    },
    {
        "id": "temperatures",
        "title": "Temperatury Sprzętu",
        "icon": "🌡️",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "",
        "desc": "Karty temperatur procesora, karty graficznej oraz dysku NVMe SSD."
    },
    {
        "id": "clock",
        "title": "Zegar Cyfrowy / Analog",
        "icon": "🕒",
        "category": "tools",
        "category_label": "🕒 Czas & Narzędzia",
        "badge": "",
        "desc": "5 unikalnych stylów zegara: Cyberpunk, Retro LCD, Modern, Analog."
    },
    {
        "id": "calendar",
        "title": "Kalendarz Miesięczny",
        "icon": "📅",
        "category": "tools",
        "category_label": "🕒 Czas & Narzędzia",
        "badge": "",
        "desc": "Podgląd całego bieżącego miesiąca, wyróżniony dzień dzisiejszy i weekendy."
    },
    {
        "id": "image",
        "title": "Pojedyncze Zdjęcie",
        "icon": "🖼️",
        "category": "media",
        "category_label": "🖼️ Media & Grafika",
        "badge": "",
        "desc": "Wyświetlanie grafik (PNG, JPG, BMP) z opcjami dopasowania kadru."
    },
    {
        "id": "gif",
        "title": "Animowany GIF Player",
        "icon": "🎞️",
        "category": "media",
        "category_label": "🖼️ Media & Grafika",
        "badge": "",
        "desc": "Płynne odtwarzanie animacji GIF z regulacją prędkości w czasie rzeczywistym."
    },
    {
        "id": "slideshow",
        "title": "Pokaz Slajdów",
        "icon": "📋",
        "category": "media",
        "category_label": "🖼️ Media & Grafika",
        "badge": "",
        "desc": "Rotacja wybranych zdjęć z playlisty z czasem przejścia i trybem losowym."
    }
]

# Static Preview Thumbnail Cache
_THUMBNAIL_CACHE: Dict[str, QPixmap] = {}

def get_screen_thumbnail(screen_id: str) -> QPixmap:
    """Renders or retrieves a high-quality 140x105 miniature preview for a screen mode."""
    if screen_id in _THUMBNAIL_CACHE:
        return _THUMBNAIL_CACHE[screen_id]

    try:
        renderer = ScreenRenderer(320, 240)
        metrics = {
            "cpu_percent": 42.0,
            "ram_percent": 58.0,
            "gpu_percent": 65.0,
            "cpu_temp": 48.0,
            "gpu_temp": 54.0,
            "nvme_temp": 41.0,
            "net_download_speed": 12.5,
            "net_upload_speed": 4.2
        }
        cfg = {"current_mode": screen_id, "width": 320, "height": 240}
        pil_img = renderer.render(cfg, metrics)

        # Scale down to 140x105 thumbnail
        thumb_pil = pil_img.resize((140, 105), Image.Resampling.BILINEAR)
        
        # Convert to QPixmap
        data = thumb_pil.convert("RGBA").tobytes("raw", "RGBA")
        qimg = QImage(data, 140, 105, QImage.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg)
        _THUMBNAIL_CACHE[screen_id] = pix
        return pix
    except Exception:
        # Fallback empty pixmap
        pix = QPixmap(140, 105)
        pix.fill(Qt.darkGray)
        _THUMBNAIL_CACHE[screen_id] = pix
        return pix


class ScreenTileWidget(QFrame):
    """
    Rich interactive tile card featuring a live/rendered thumbnail preview,
    title, icon, status badges, and compact description.
    """
    clicked = Signal(str)

    def __init__(self, screen_data: dict, is_selected: bool = False):
        super().__init__()
        self.screen_data = screen_data
        self.screen_id = screen_data["id"]
        self.is_selected = is_selected
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setup_ui()
        self.update_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Thumbnail Container Frame
        thumb_container = QFrame()
        thumb_container.setStyleSheet("background: #000000; border-radius: 6px; border: 1px solid #1e293b;")
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(0, 0, 0, 0)

        self.thumb_lbl = QLabel()
        self.thumb_lbl.setAlignment(Qt.AlignCenter)
        self.thumb_lbl.setPixmap(get_screen_thumbnail(self.screen_id))
        self.thumb_lbl.setStyleSheet("border-radius: 5px;")
        thumb_layout.addWidget(self.thumb_lbl)

        layout.addWidget(thumb_container)

        # 2. Header Row: Icon + Title + Badge
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        icon_lbl = QLabel(self.screen_data["icon"])
        icon_lbl.setStyleSheet("font-size: 14px;")
        header_row.addWidget(icon_lbl)

        title_lbl = QLabel(self.screen_data["title"])
        title_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")
        header_row.addWidget(title_lbl, 1)

        if self.screen_data["badge"]:
            badge = QLabel(self.screen_data["badge"])
            if self.screen_data["badge"] == "GRYWALNY":
                badge.setStyleSheet("background: #ea580c; color: #ffffff; font-weight: bold; font-size: 8px; padding: 2px 4px; border-radius: 3px;")
            elif self.screen_data["badge"] == "NOWOŚĆ":
                badge.setStyleSheet("background: #059669; color: #ffffff; font-weight: bold; font-size: 8px; padding: 2px 4px; border-radius: 3px;")
            else:
                badge.setStyleSheet("background: #7c3aed; color: #ffffff; font-weight: bold; font-size: 8px; padding: 2px 4px; border-radius: 3px;")
            header_row.addWidget(badge)

        self.active_indicator = QLabel("AKTYWNY" if self.is_selected else "")
        self.active_indicator.setStyleSheet("background: #0284c7; color: #ffffff; font-weight: bold; font-size: 8px; padding: 2px 4px; border-radius: 3px;")
        self.active_indicator.setVisible(self.is_selected)
        header_row.addWidget(self.active_indicator)

        layout.addLayout(header_row)

        # 3. Compact Description
        desc_lbl = QLabel(self.screen_data["desc"])
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 10px; line-height: 1.2;")
        desc_lbl.setFixedHeight(28)
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.screen_id)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.active_indicator.setVisible(selected)
        self.active_indicator.setText("AKTYWNY" if selected else "")
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                    border: 2px solid #00f0ff;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: #111827;
                    border: 1px solid #1f293d;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background: #1e293b;
                    border: 1px solid #38bdf8;
                }
            """)


class ScreenGalleryWidget(QWidget):
    """
    Overhauled Screen Gallery with 2-Column Responsive Tiles, Miniature Previews,
    Category Filters, and Instant Mode Activation.
    """
    screen_changed = Signal(str)

    def __init__(self, current_mode: str = "mario"):
        super().__init__()
        self.current_mode = current_mode
        self.tiles: dict[str, ScreenTileWidget] = {}
        self.active_category = "all"
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Header Title
        header_row = QHBoxLayout()
        gallery_title = QLabel("🎨 Galeria Ekranów LCD (Kafelki)")
        gallery_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00f0ff;")
        header_row.addWidget(gallery_title)

        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Filter Chips (Categories)
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(5)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        categories = [
            ("all", "Wszystkie"),
            ("games", "🎮 Gry & Retro"),
            ("creative", "✨ Efektowne"),
            ("telemetry", "📊 Telemetria"),
            ("tools", "🕒 Czas"),
            ("media", "🖼️ Media")
        ]

        for cat_id, cat_name in categories:
            btn = QPushButton(cat_name)
            btn.setCheckable(True)
            if cat_id == "all":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: #1e293b;
                    color: #94a3b8;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 4px 8px;
                    border-radius: 10px;
                    border: 1px solid #334155;
                }
                QPushButton:checked {
                    background: #0284c7;
                    color: #ffffff;
                    border: 1px solid #38bdf8;
                }
                QPushButton:hover:!checked {
                    background: #334155;
                    color: #ffffff;
                }
            """)
            btn.clicked.connect(lambda checked, c=cat_id: self.filter_category(c))
            self.filter_group.addButton(btn)
            filter_bar.addWidget(btn)

        filter_bar.addStretch()
        main_layout.addLayout(filter_bar)

        # Scroll Area for 2-Column Grid of Tiles
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.tiles_container = QWidget()
        self.grid_layout = QGridLayout(self.tiles_container)
        self.grid_layout.setContentsMargins(0, 4, 6, 4)
        self.grid_layout.setSpacing(8)

        # Build Tiles in 2 columns
        row, col = 0, 0
        for screen in SCREENS_CATALOG:
            tile = ScreenTileWidget(screen, is_selected=(screen["id"] == self.current_mode))
            tile.clicked.connect(self.select_screen)
            self.tiles[screen["id"]] = tile
            self.grid_layout.addWidget(tile, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        scroll.setWidget(self.tiles_container)
        main_layout.addWidget(scroll, 1)

    def filter_category(self, category: str):
        self.active_category = category
        self.apply_filter()

    def apply_filter(self):
        # Clear layout positions and re-grid visible tiles
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                self.grid_layout.removeWidget(item.widget())

        row, col = 0, 0
        for screen in SCREENS_CATALOG:
            sid = screen["id"]
            tile = self.tiles.get(sid)
            if not tile:
                continue

            match_cat = (self.active_category == "all" or screen["category"] == self.active_category)
            if match_cat:
                tile.show()
                self.grid_layout.addWidget(tile, row, col)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
            else:
                tile.hide()

    def select_screen(self, screen_id: str):
        self.current_mode = screen_id
        for sid, tile in self.tiles.items():
            tile.set_selected(sid == screen_id)
        self.screen_changed.emit(screen_id)

    def set_active_mode(self, mode_id: str):
        self.current_mode = mode_id
        for sid, tile in self.tiles.items():
            tile.set_selected(sid == mode_id)
