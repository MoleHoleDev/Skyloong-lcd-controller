import os
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QSpinBox, QCheckBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class SlideshowTab(QWidget):
    config_changed = Signal()

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Slideshow Playlist Group
        list_group = QGroupBox("📋 Kolejka zdjęć do pokazu slajdów")
        list_layout = QVBoxLayout(list_group)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setMinimumHeight(120)
        self.refresh_list()
        list_layout.addWidget(self.list_widget)

        # Buttons toolbar
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Dodaj zdjęcia...")
        add_btn.setObjectName("AccentButton")
        add_btn.clicked.connect(self.add_images)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("🗑️ Usuń wybrane")
        remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Wyczyść listę")
        clear_btn.setObjectName("DangerButton")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(clear_btn)
        list_layout.addLayout(btn_layout)
        layout.addWidget(list_group)

        # Timing & Transition Settings
        settings_group = QGroupBox("⏱️ Ustawienia interwału i kolejności")
        settings_layout = QVBoxLayout(settings_group)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Czas wyświetlania każdego zdjęcia (sekundy):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 300)
        self.interval_spin.setValue(self.config_mgr.get("slideshow_interval", 5))
        self.interval_spin.valueChanged.connect(self.on_interval_changed)
        interval_layout.addWidget(self.interval_spin)
        settings_layout.addLayout(interval_layout)

        self.shuffle_check = QCheckBox("🔀 Losowa kolejność wyświetlania (Shuffle)")
        self.shuffle_check.setChecked(self.config_mgr.get("slideshow_shuffle", False))
        self.shuffle_check.toggled.connect(self.on_shuffle_toggled)
        settings_layout.addWidget(self.shuffle_check)

        layout.addWidget(settings_group)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def refresh_list(self):
        self.list_widget.clear()
        images: List[str] = self.config_mgr.get("slideshow_images", [])
        for p in images:
            self.list_widget.addItem(p)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Wybierz zdjęcia do pokazu slajdów", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if files:
            current: List[str] = list(self.config_mgr.get("slideshow_images", []))
            for f in files:
                if f not in current:
                    current.append(f)
            self.config_mgr.set("slideshow_images", current)
            self.refresh_list()
            self.config_changed.emit()

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
        current: List[str] = list(self.config_mgr.get("slideshow_images", []))
        for item in selected_items:
            path = item.text()
            if path in current:
                current.remove(path)
        self.config_mgr.set("slideshow_images", current)
        self.refresh_list()
        self.config_changed.emit()

    def clear_all(self):
        self.config_mgr.set("slideshow_images", [])
        self.refresh_list()
        self.config_changed.emit()

    def on_interval_changed(self, val: int):
        self.config_mgr.set("slideshow_interval", val)
        self.config_changed.emit()

    def on_shuffle_toggled(self, checked: bool):
        self.config_mgr.set("slideshow_shuffle", checked)
        self.config_changed.emit()
