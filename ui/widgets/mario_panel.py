import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QComboBox, QGroupBox, QPushButton, QGridLayout, QFrame
)
from PySide6.QtCore import Signal, Qt
from lcd_core.config_manager import ConfigManager

class MarioPanel(QWidget):
    settings_changed = Signal()
    key_action = Signal(str)  # Emits key commands: "left", "right", "jump", "down", "fire", "reset"

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 1. Title & Configuration Box
        title_box = QGroupBox("🍄 Ustawienia Super Mario Retro World")
        title_layout = QVBoxLayout(title_box)

        # Level Style
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("🏰 Motyw poziomu:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("World 1-1 (Classic Overworld)", "overworld")
        self.theme_combo.addItem("World 1-2 (Underground Caverns)", "underground")
        self.theme_combo.addItem("World 1-4 (Bowser's Castle)", "castle")
        
        cur_t = self.config_mgr.get("mario_theme", "overworld")
        idx = self.theme_combo.findData(cur_t)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_row.addWidget(self.theme_combo, 1)
        title_layout.addLayout(theme_row)

        # Toggles
        self.hud_cb = QCheckBox("Wyświetlaj pasek telemetrii HUD (CPU/RAM/Score/Time)")
        self.hud_cb.setChecked(self.config_mgr.get("mario_show_hud", True))
        self.hud_cb.toggled.connect(lambda v: self.update_cfg("mario_show_hud", v))
        title_layout.addWidget(self.hud_cb)

        self.autoplay_cb = QCheckBox("Autoplay / Tryb Demo (Mario gra sam, gdy brak kliknięć)")
        self.autoplay_cb.setChecked(self.config_mgr.get("mario_autoplay", True))
        self.autoplay_cb.toggled.connect(lambda v: self.update_cfg("mario_autoplay", v))
        title_layout.addWidget(self.autoplay_cb)

        layout.addWidget(title_box)

        # 2. Interactive Game Controls Box
        ctrl_box = QGroupBox("🎮 Sterowanie Grą (Klawiatura & Przyciski)")
        ctrl_layout = QVBoxLayout(ctrl_box)

        # D-pad grid for mouse clicks
        dpad_grid = QGridLayout()
        dpad_grid.setSpacing(6)

        btn_left = QPushButton("◀ W Lewo (A)")
        btn_left.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px;")
        btn_left.clicked.connect(lambda: self.key_action.emit("left"))

        btn_right = QPushButton("▶ W Prawo (D)")
        btn_right.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px;")
        btn_right.clicked.connect(lambda: self.key_action.emit("right"))

        btn_jump = QPushButton("▲ SKOK (Spacja / W)")
        btn_jump.setStyleSheet("background: #059669; color: #ffffff; font-weight: bold; padding: 10px; font-size: 12px;")
        btn_jump.clicked.connect(lambda: self.key_action.emit("jump"))

        btn_fire = QPushButton("🔥 OGNISTA KULA (Ctrl / F)")
        btn_fire.setStyleSheet("background: #ea580c; color: #ffffff; font-weight: bold; padding: 10px; font-size: 12px;")
        btn_fire.clicked.connect(lambda: self.key_action.emit("fire"))

        dpad_grid.addWidget(btn_jump, 0, 0, 1, 2)
        dpad_grid.addWidget(btn_left, 1, 0)
        dpad_grid.addWidget(btn_right, 1, 1)
        dpad_grid.addWidget(btn_fire, 2, 0, 1, 2)

        ctrl_layout.addLayout(dpad_grid)

        # Keyboard Cheat Sheet Guide
        guide_frame = QFrame()
        guide_frame.setStyleSheet("background: #0a0f1d; border: 1px solid #1e293b; border-radius: 6px; padding: 8px;")
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setSpacing(4)

        guide_title = QLabel("⌨️ Skróty Klawiszowe w Systemie:")
        guide_title.setStyleSheet("color: #00f0ff; font-weight: bold; font-size: 11px;")
        guide_layout.addWidget(guide_title)

        shortcuts = [
            ("A / D  lub  ← / →", "Ruch w lewo i prawo"),
            ("Spacja / W / ↑", "Skok (rozbijanie bloków i skakanie po wrogach)"),
            ("S / ↓", "Kucnięcie"),
            ("Ctrl / F / J", "Wystrzelenie płomienistej kuli (Fireball)"),
        ]
        for key_t, desc_t in shortcuts:
            row = QHBoxLayout()
            k_lbl = QLabel(key_t)
            k_lbl.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 10px; min-width: 120px;")
            d_lbl = QLabel(desc_t)
            d_lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            row.addWidget(k_lbl)
            row.addWidget(d_lbl, 1)
            guide_layout.addLayout(row)

        ctrl_layout.addWidget(guide_frame)
        layout.addWidget(ctrl_box)

        layout.addStretch()

    def on_theme_changed(self):
        val = self.theme_combo.currentData()
        self.config_mgr.set("mario_theme", val)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
