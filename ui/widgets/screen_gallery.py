import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QButtonGroup, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

SCREENS_CATALOG = [
    {
        "id": "retro_synthwave",
        "title": "Retro Synthwave HUD",
        "icon": "🌆",
        "category": "creative",
        "category_label": "✨ Kreatywne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Perspektywiczny neonowy grid, słońce retro, zegar cyberpunk oraz wskaźniki telemetrii CPU/GPU/RAM."
    },
    {
        "id": "matrix_rain",
        "title": "Matrix Digital Rain",
        "icon": "🟢",
        "category": "creative",
        "category_label": "✨ Kreatywne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Spływający zielony deszcz glifów Matrix z wbudowaną konsolą zegara i macierzą obciążenia rdzeni."
    },
    {
        "id": "audio_visualizer",
        "title": "Audio Spectrum / VU Meter",
        "icon": "🎵",
        "category": "creative",
        "category_label": "✨ Kreatywne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Wielopasmowy analizator widma częstotliwości audio ze wskaźnikami Peak i stereofonicznym VU Meter L/R."
    },
    {
        "id": "dual_gauges",
        "title": "Dual Racing Tachometers",
        "icon": "🏎️",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "NOWOŚĆ",
        "desc": "Podwójne analogowe zegary obrotomierza dla CPU i GPU, cyfrowy odczyt temperatur i pasek NVMe/RAM."
    },
    {
        "id": "pomodoro",
        "title": "Pomodoro & Focus Timer",
        "icon": "⏱️",
        "category": "tools",
        "category_label": "🕒 Czas & Narzędzia",
        "badge": "NOWOŚĆ",
        "desc": "Okrągły zegar sesji głębokiego skupienia (25 min) i przerw regeneracyjnych z licznikiem rund."
    },
    {
        "id": "scifi_terminal",
        "title": "Sci-Fi Starship HUD",
        "icon": "🚀",
        "category": "creative",
        "category_label": "✨ Kreatywne & HUD",
        "badge": "NOWOŚĆ",
        "desc": "Futurystyczny panel dowodzenia z obrotowym radarem taktycznym, stanem reaktora i diagnostyką."
    },
    {
        "id": "custom",
        "title": "Super Dashboard (Modułowy)",
        "icon": "🧩",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "POPULARNY",
        "desc": "W pełni modyfikowalny pulpit hybrydowy: zegar, słupki CPU/RAM/GPU, temperatury i własna tapeta."
    },
    {
        "id": "usage",
        "title": "Telemetria PC (Pierścienie)",
        "icon": "📊",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "",
        "desc": "Trzy neonowe pierścienie obciążenia CPU, pamięci RAM i karty graficznej z prędkością sieci."
    },
    {
        "id": "temperatures",
        "title": "Temperatury Podzespołów",
        "icon": "🌡️",
        "category": "telemetry",
        "category_label": "📊 Telemetria",
        "badge": "",
        "desc": "Karty temperatur procesora, karty graficznej oraz dysku NVMe SSD z 3-stopniowym systemem alertów."
    },
    {
        "id": "clock",
        "title": "Zegar Cyfrowy i Analogowy",
        "icon": "🕒",
        "category": "tools",
        "category_label": "🕒 Czas & Narzędzia",
        "badge": "",
        "desc": "5 unikalnych stylów zegara: Cyberpunk Neon, Retro Zielony LCD, Cyfrowy Modern, Minimal, Analog."
    },
    {
        "id": "calendar",
        "title": "Kalendarz Miesięczny",
        "icon": "📅",
        "category": "tools",
        "category_label": "🕒 Czas & Narzędzia",
        "badge": "",
        "desc": "Podgląd całego bieżącego miesiąca, wyróżniony dzień dzisiejszy, weekendy i zegar w nagłówku."
    },
    {
        "id": "image",
        "title": "Pojedyncze Zdjęcie / Tapeta",
        "icon": "🖼️",
        "category": "media",
        "category_label": "🖼️ Media & Grafika",
        "badge": "",
        "desc": "Wyświetlanie grafik (PNG, JPG, BMP) z opcjami dopasowania kadru, jasności i kontrastu."
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
        "desc": "Rotacja wybranych zdjęć z playlisty z konfigurowalnym czasem przejścia i trybem losowym."
    }
]

class ScreenCardWidget(QFrame):
    """Interactive card representing a selectable screen mode in the gallery."""
    clicked = Signal(str)

    def __init__(self, screen_data: dict, is_selected: bool = False):
        super().__init__()
        self.screen_data = screen_data
        self.screen_id = screen_data["id"]
        self.is_selected = is_selected
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setup_ui()
        self.update_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top row: Icon + Title + Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        icon_lbl = QLabel(self.screen_data["icon"])
        icon_lbl.setStyleSheet("font-size: 20px;")
        top_row.addWidget(icon_lbl)

        title_lbl = QLabel(self.screen_data["title"])
        title_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
        top_row.addWidget(title_lbl, 1)

        if self.screen_data["badge"]:
            badge = QLabel(self.screen_data["badge"])
            if self.screen_data["badge"] == "NOWOŚĆ":
                badge.setStyleSheet("background: #059669; color: #ffffff; font-weight: bold; font-size: 9px; padding: 2px 6px; border-radius: 4px;")
            else:
                badge.setStyleSheet("background: #7c3aed; color: #ffffff; font-weight: bold; font-size: 9px; padding: 2px 6px; border-radius: 4px;")
            top_row.addWidget(badge)

        self.active_indicator = QLabel("AKTYWNY" if self.is_selected else "")
        self.active_indicator.setStyleSheet("background: #0284c7; color: #ffffff; font-weight: bold; font-size: 9px; padding: 2px 6px; border-radius: 4px;")
        self.active_indicator.setVisible(self.is_selected)
        top_row.addWidget(self.active_indicator)

        layout.addLayout(top_row)

        # Description
        desc_lbl = QLabel(self.screen_data["desc"])
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.3;")
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
    Left-column screen gallery with category filters, search and interactive cards.
    """
    screen_changed = Signal(str)

    def __init__(self, current_mode: str = "retro_synthwave"):
        super().__init__()
        self.current_mode = current_mode
        self.cards: dict[str, ScreenCardWidget] = {}
        self.active_category = "all"
        self.search_text = ""
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Header Title
        header_row = QHBoxLayout()
        gallery_title = QLabel("🎨 Galeria Ekranów LCD")
        gallery_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00f0ff;")
        header_row.addWidget(gallery_title)

        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Filter Chips (Categories)
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(6)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        categories = [
            ("all", "Wszystkie"),
            ("creative", "✨ Nowe & Efektowne"),
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
                    font-size: 11px;
                    font-weight: 600;
                    padding: 5px 10px;
                    border-radius: 12px;
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

        # Scroll Area for Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 4, 8, 4)
        self.cards_layout.setSpacing(8)

        # Build cards
        for screen in SCREENS_CATALOG:
            card = ScreenCardWidget(screen, is_selected=(screen["id"] == self.current_mode))
            card.clicked.connect(self.select_screen)
            self.cards[screen["id"]] = card
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll, 1)

    def filter_category(self, category: str):
        self.active_category = category
        self.apply_filter()

    def apply_filter(self):
        for screen in SCREENS_CATALOG:
            sid = screen["id"]
            card = self.cards.get(sid)
            if not card:
                continue

            match_cat = (self.active_category == "all" or screen["category"] == self.active_category)
            match_search = (self.search_text == "" or self.search_text in screen["title"].lower() or self.search_text in screen["desc"].lower())

            card.setVisible(match_cat and match_search)

    def select_screen(self, screen_id: str):
        if self.current_mode != screen_id:
            # Unselect previous
            if self.current_mode in self.cards:
                self.cards[self.current_mode].set_selected(False)
            
            self.current_mode = screen_id
            
            # Select new
            if screen_id in self.cards:
                self.cards[screen_id].set_selected(True)

            self.screen_changed.emit(screen_id)

    def set_current_mode(self, mode: str):
        if mode in self.cards:
            self.select_screen(mode)
