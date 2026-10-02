import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QComboBox, QGroupBox, QPushButton, QGridLayout, QFrame
)
from PySide6.QtCore import Signal, Qt
from lcd_core.config_manager import ConfigManager

class DoomPanel(QWidget):
    settings_changed = Signal()
    key_action = Signal(str)  # Emits key commands: "w", "s", "a", "d", "shoot", "1", "2", "3"

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 1. Title & Configuration Box
        title_box = QGroupBox("💀 Ustawienia DOOM Classic 1993")
        title_layout = QVBoxLayout(title_box)

        # Weapon Selection
        w_row = QHBoxLayout()
        w_row.addWidget(QLabel("🔫 Wybór Broni:"))
        self.weapon_combo = QComboBox()
        self.weapon_combo.addItem("Shotgun (Dwururka Pump-Action)", "shotgun")
        self.weapon_combo.addItem("Chaingun (Działko Obrotowe)", "chaingun")
        self.weapon_combo.addItem("Plasma Rifle (Działko Plazmowe)", "plasma")
        self.weapon_combo.addItem("Berserk Fist (Pięści)", "fist")

        cur_w = self.config_mgr.get("doom_weapon", "shotgun")
        idx = self.weapon_combo.findData(cur_w)
        if idx >= 0:
            self.weapon_combo.setCurrentIndex(idx)
        self.weapon_combo.currentIndexChanged.connect(self.on_weapon_changed)
        w_row.addWidget(self.weapon_combo, 1)
        title_layout.addLayout(w_row)

        # Arena Theme
        a_row = QHBoxLayout()
        a_row.addWidget(QLabel("☣️ Lokacja / Arena:"))
        self.arena_combo = QComboBox()
        self.arena_combo.addItem("E1M1: Hangar (Industrial Metal)", "hangar")
        self.arena_combo.addItem("E1M2: Nuclear Plant (Toxic Slime)", "toxic")
        self.arena_combo.addItem("E3M1: Hell Keep (Inferno Red)", "hell")

        cur_a = self.config_mgr.get("doom_arena", "hangar")
        a_idx = self.arena_combo.findData(cur_a)
        if a_idx >= 0:
            self.arena_combo.setCurrentIndex(a_idx)
        self.arena_combo.currentIndexChanged.connect(self.on_arena_changed)
        a_row.addWidget(self.arena_combo, 1)
        title_layout.addLayout(a_row)

        # Toggles
        self.hud_cb = QCheckBox("Wyświetlaj oryginalny Status Bar z twarzą Doomgaya")
        self.hud_cb.setChecked(self.config_mgr.get("doom_show_hud", True))
        self.hud_cb.toggled.connect(lambda v: self.update_cfg("doom_show_hud", v))
        title_layout.addWidget(self.hud_cb)

        self.autoplay_cb = QCheckBox("Autoplay / Tryb Demo (Doomguy patroluje i strzela sam)")
        self.autoplay_cb.setChecked(self.config_mgr.get("doom_autoplay", True))
        self.autoplay_cb.toggled.connect(lambda v: self.update_cfg("doom_autoplay", v))
        title_layout.addWidget(self.autoplay_cb)

        layout.addWidget(title_box)

        # 2. Interactive Game Controls Box
        ctrl_box = QGroupBox("🎮 Sterowanie Grą (Klawiatura & Przyciski)")
        ctrl_layout = QVBoxLayout(ctrl_box)

        # D-pad grid for mouse clicks
        dpad_grid = QGridLayout()
        dpad_grid.setSpacing(6)

        btn_fwd = QPushButton("▲ Do Przodu (W / ↑)")
        btn_fwd.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px;")
        btn_fwd.clicked.connect(lambda: self.key_action.emit("w"))

        btn_left = QPushButton("◀ Obrót w Lewo (A / ←)")
        btn_left.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px;")
        btn_left.clicked.connect(lambda: self.key_action.emit("a"))

        btn_right = QPushButton("▶ Obrót w Prawo (D / →)")
        btn_right.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px;")
        btn_right.clicked.connect(lambda: self.key_action.emit("d"))

        btn_back = QPushButton("▼ Do Tyłu (S / ↓)")
        btn_back.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 8px;")
        btn_back.clicked.connect(lambda: self.key_action.emit("s"))

        btn_shoot = QPushButton("💥 STRZAŁ / SHOOT (Spacja / Ctrl / F)")
        btn_shoot.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #ef4444); color: #ffffff; font-weight: bold; font-size: 13px; padding: 12px; border-radius: 6px; border: 1px solid #f87171;")
        btn_shoot.clicked.connect(lambda: self.key_action.emit("shoot"))

        dpad_grid.addWidget(btn_fwd, 0, 0, 1, 2)
        dpad_grid.addWidget(btn_left, 1, 0)
        dpad_grid.addWidget(btn_right, 1, 1)
        dpad_grid.addWidget(btn_back, 2, 0, 1, 2)
        dpad_grid.addWidget(btn_shoot, 3, 0, 1, 2)

        ctrl_layout.addLayout(dpad_grid)

        # Keyboard Cheat Sheet Guide
        guide_frame = QFrame()
        guide_frame.setStyleSheet("background: #0a0f1d; border: 1px solid #1e293b; border-radius: 6px; padding: 8px;")
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setSpacing(4)

        guide_title = QLabel("⌨️ Skróty Klawiszowe w Systemie:")
        guide_title.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
        guide_layout.addWidget(guide_title)

        shortcuts = [
            ("W / S  lub  ↑ / ↓", "Ruch do przodu i do tyłu"),
            ("A / D  lub  ← / →", "Obrót kamery w lewo i w prawo"),
            ("Spacja / Ctrl / F / Enter", "Strzał z aktualnej broni (odrzut, błysk i eliminacja demonów)"),
            ("1 / 2 / 3", "Szybki wybór broni (1: Pięść, 2: Shotgun, 3: Chaingun)"),
        ]
        for key_t, desc_t in shortcuts:
            row = QHBoxLayout()
            k_lbl = QLabel(key_t)
            k_lbl.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 10px; min-width: 140px;")
            d_lbl = QLabel(desc_t)
            d_lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            row.addWidget(k_lbl)
            row.addWidget(d_lbl, 1)
            guide_layout.addLayout(row)

        ctrl_layout.addWidget(guide_frame)
        layout.addWidget(ctrl_box)

        layout.addStretch()

    def on_weapon_changed(self):
        val = self.weapon_combo.currentData()
        self.config_mgr.set("doom_weapon", val)
        self.settings_changed.emit()

    def on_arena_changed(self):
        val = self.arena_combo.currentData()
        self.config_mgr.set("doom_arena", val)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
