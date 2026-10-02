import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from lcd_core.config_manager import ConfigManager

class PomodoroPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        
        # 1-second Pomodoro tick timer
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self.on_timer_tick)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        box = QGroupBox("⏱️ Ustawienia Pomodoro & Focus Timer")
        b_layout = QVBoxLayout(box)

        # Durations
        d_row = QHBoxLayout()
        d_row.addWidget(QLabel("🎯 Czas skupienia (min):"))
        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 120)
        self.focus_spin.setValue(self.config_mgr.get("pomodoro_focus_min", 25))
        self.focus_spin.valueChanged.connect(self.on_focus_time_changed)
        d_row.addWidget(self.focus_spin)

        d_row.addWidget(QLabel("☕ Przerwa (min):"))
        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(self.config_mgr.get("pomodoro_break_min", 5))
        self.break_spin.valueChanged.connect(self.on_break_time_changed)
        d_row.addWidget(self.break_spin)
        b_layout.addLayout(d_row)

        # Task Name
        t_row = QHBoxLayout()
        t_row.addWidget(QLabel("📝 Nazwa zadania:"))
        self.task_input = QLineEdit()
        self.task_input.setText(self.config_mgr.get("pomodoro_task_name", "Deep Work Session"))
        self.task_input.textChanged.connect(self.on_task_changed)
        t_row.addWidget(self.task_input, 1)
        b_layout.addLayout(t_row)

        # Action Buttons
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶ Rozpocznij")
        self.start_btn.setStyleSheet("background: #059669; color: white; font-weight: bold; padding: 8px;")
        self.start_btn.clicked.connect(self.start_timer)
        btn_row.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pauza")
        self.pause_btn.setStyleSheet("background: #d97706; color: white; font-weight: bold; padding: 8px;")
        self.pause_btn.clicked.connect(self.pause_timer)
        btn_row.addWidget(self.pause_btn)

        self.reset_btn = QPushButton("🔄 Resetuj")
        self.reset_btn.setStyleSheet("background: #dc2626; color: white; font-weight: bold; padding: 8px;")
        self.reset_btn.clicked.connect(self.reset_timer)
        btn_row.addWidget(self.reset_btn)

        b_layout.addLayout(btn_row)

        # Switch Mode buttons
        mode_row = QHBoxLayout()
        self.switch_focus_btn = QPushButton("🎯 Tryb Focus (25m)")
        self.switch_focus_btn.clicked.connect(lambda: self.switch_mode("focus"))
        mode_row.addWidget(self.switch_focus_btn)

        self.switch_break_btn = QPushButton("☕ Tryb Przerwy (5m)")
        self.switch_break_btn.clicked.connect(lambda: self.switch_mode("break"))
        mode_row.addWidget(self.switch_break_btn)
        b_layout.addLayout(mode_row)

        layout.addWidget(box)
        layout.addStretch()

    def start_timer(self):
        self.config_mgr.set("pomodoro_state", "running")
        if not self.tick_timer.isActive():
            self.tick_timer.start(1000)
        self.settings_changed.emit()

    def pause_timer(self):
        self.config_mgr.set("pomodoro_state", "paused")
        self.tick_timer.stop()
        self.settings_changed.emit()

    def reset_timer(self):
        self.tick_timer.stop()
        self.config_mgr.set("pomodoro_state", "stopped")
        mode = self.config_mgr.get("pomodoro_mode", "focus")
        dur = self.focus_spin.value() * 60 if mode == "focus" else self.break_spin.value() * 60
        self.config_mgr.set("pomodoro_time_left", dur)
        self.settings_changed.emit()

    def switch_mode(self, mode: str):
        self.config_mgr.set("pomodoro_mode", mode)
        dur = self.focus_spin.value() * 60 if mode == "focus" else self.break_spin.value() * 60
        self.config_mgr.set("pomodoro_time_left", dur)
        self.settings_changed.emit()

    def on_timer_tick(self):
        t_left = self.config_mgr.get("pomodoro_time_left", 1500)
        if t_left > 0:
            t_left -= 1
            self.config_mgr.set("pomodoro_time_left", t_left, auto_save=False)
        else:
            # Switch modes automatically
            curr_mode = self.config_mgr.get("pomodoro_mode", "focus")
            if curr_mode == "focus":
                rounds = self.config_mgr.get("pomodoro_rounds_done", 0) + 1
                self.config_mgr.set("pomodoro_rounds_done", rounds)
                self.switch_mode("break")
            else:
                self.switch_mode("focus")
        self.settings_changed.emit()

    def on_focus_time_changed(self, val: int):
        self.config_mgr.set("pomodoro_focus_min", val)
        if self.config_mgr.get("pomodoro_mode", "focus") == "focus" and self.config_mgr.get("pomodoro_state") == "stopped":
            self.config_mgr.set("pomodoro_time_left", val * 60)
        self.settings_changed.emit()

    def on_break_time_changed(self, val: int):
        self.config_mgr.set("pomodoro_break_min", val)
        if self.config_mgr.get("pomodoro_mode") == "break" and self.config_mgr.get("pomodoro_state") == "stopped":
            self.config_mgr.set("pomodoro_time_left", val * 60)
        self.settings_changed.emit()

    def on_task_changed(self, text: str):
        self.config_mgr.set("pomodoro_task_name", text)
        self.settings_changed.emit()
