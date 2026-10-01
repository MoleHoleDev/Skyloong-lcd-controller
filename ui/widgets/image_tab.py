import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QSlider, QGroupBox, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class ImageTab(QWidget):
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

        # File Selection Group
        file_group = QGroupBox("🖼️ Wybór pliku graficznego")
        file_layout = QVBoxLayout(file_group)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Wybierz plik graficzny (PNG, JPG, BMP, WebP)...")
        self.path_edit.setText(self.config_mgr.get("image_path", ""))
        self.path_edit.textChanged.connect(self.on_path_changed)
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("Przeglądaj...")
        browse_btn.setObjectName("AccentButton")
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)
        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)

        # Display Settings Group
        settings_group = QGroupBox("⚙️ Dopasowanie i korekcja obrazu")
        settings_layout = QVBoxLayout(settings_group)

        # Fit Mode
        fit_layout = QHBoxLayout()
        fit_layout.addWidget(QLabel("Dopasowanie do ekranu:"))
        self.fit_combo = QComboBox()
        fit_items = [
            ("Wypełnij (Cover / Przytnij krawędzie)", "cover"),
            ("Dopasuj proporcje (Contain / Pasy)", "contain"),
            ("Rozciągnij (Stretch)", "stretch")
        ]
        for text, data in fit_items:
            self.fit_combo.addItem(text, data)
        current_fit = self.config_mgr.get("image_fit", "cover")
        idx = max(0, ["cover", "contain", "stretch"].index(current_fit) if current_fit in ["cover", "contain", "stretch"] else 0)
        self.fit_combo.setCurrentIndex(idx)
        self.fit_combo.currentIndexChanged.connect(self.on_fit_changed)
        fit_layout.addWidget(self.fit_combo)
        settings_layout.addLayout(fit_layout)

        # Brightness
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Jasność (%):"))
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(20, 200)
        self.bright_slider.setValue(self.config_mgr.get("image_brightness", 100))
        self.bright_lbl = QLabel(f"{self.bright_slider.value()}%")
        self.bright_slider.valueChanged.connect(self.on_brightness_changed)
        bright_layout.addWidget(self.bright_slider)
        bright_layout.addWidget(self.bright_lbl)
        settings_layout.addLayout(bright_layout)

        # Contrast
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Kontrast (%):"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(20, 200)
        self.contrast_slider.setValue(self.config_mgr.get("image_contrast", 100))
        self.contrast_lbl = QLabel(f"{self.contrast_slider.value()}%")
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_lbl)
        settings_layout.addLayout(contrast_layout)

        # Reset button
        reset_btn = QPushButton("↺ Zresetuj korekcję")
        reset_btn.clicked.connect(self.reset_filters)
        settings_layout.addWidget(reset_btn)

        layout.addWidget(settings_group)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz zdjęcie dla ekranu", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.webp *.ico)"
        )
        if path:
            self.path_edit.setText(path)

    def on_path_changed(self, text: str):
        self.config_mgr.set("image_path", text.strip())
        self.config_changed.emit()

    def on_fit_changed(self, idx: int):
        val = self.fit_combo.itemData(idx) or ["cover", "contain", "stretch"][idx]
        self.config_mgr.set("image_fit", val)
        self.config_changed.emit()

    def on_brightness_changed(self, val: int):
        self.bright_lbl.setText(f"{val}%")
        self.config_mgr.set("image_brightness", val)
        self.config_changed.emit()

    def on_contrast_changed(self, val: int):
        self.contrast_lbl.setText(f"{val}%")
        self.config_mgr.set("image_contrast", val)
        self.config_changed.emit()

    def reset_filters(self):
        self.bright_slider.setValue(100)
        self.contrast_slider.setValue(100)
