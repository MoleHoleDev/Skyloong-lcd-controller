from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup,
    QGroupBox, QProgressBar, QSpinBox, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class SystemTab(QWidget):
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

        # Live Sensors Card
        live_group = QGroupBox("📊 Odczyty czujników na żywo")
        live_layout = QVBoxLayout(live_group)

        # CPU
        self.cpu_bar, self.cpu_val_lbl = self._create_metric_row("CPU (Procesor):", "#00f0ff")
        live_layout.addLayout(self.cpu_bar)

        # RAM
        self.ram_bar, self.ram_val_lbl = self._create_metric_row("RAM (Pamięć):", "#d946ef")
        live_layout.addLayout(self.ram_bar)

        # GPU
        self.gpu_bar, self.gpu_val_lbl = self._create_metric_row("GPU (Karta graficzna):", "#10b981")
        live_layout.addLayout(self.gpu_bar)

        # Live Temps Row
        temps_layout = QHBoxLayout()
        self.cpu_temp_lbl = QLabel("🔥 CPU: --.-°C")
        self.cpu_temp_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; background: #0f172a; padding: 6px 10px; border-radius: 6px; border: 1px solid #1e293b;")
        temps_layout.addWidget(self.cpu_temp_lbl)

        self.gpu_temp_lbl = QLabel("🎮 GPU: --.-°C")
        self.gpu_temp_lbl.setStyleSheet("color: #10b981; font-weight: bold; background: #0f172a; padding: 6px 10px; border-radius: 6px; border: 1px solid #1e293b;")
        temps_layout.addWidget(self.gpu_temp_lbl)

        self.nvme_temp_lbl = QLabel("💾 NVMe: --.-°C")
        self.nvme_temp_lbl.setStyleSheet("color: #f59e0b; font-weight: bold; background: #0f172a; padding: 6px 10px; border-radius: 6px; border: 1px solid #1e293b;")
        temps_layout.addWidget(self.nvme_temp_lbl)

        live_layout.addLayout(temps_layout)
        layout.addWidget(live_group)

        # Usage Visualization Style Group
        usage_group = QGroupBox("📈 Styl wizualizacji zużycia zasobów (Tryb: Zużycie)")
        usage_layout = QVBoxLayout(usage_group)

        self.usage_bg = QButtonGroup(self)
        rb_rings = QRadioButton("⭕ Pierścienie Neon (Trzy kołowe wskaźniki CPU/RAM/GPU)")
        rb_rings.setProperty("u_val", "neon_rings")
        rb_bars = QRadioButton("📊 Paski telemetryczne (Poziome wskaźniki z transferem sieci)")
        rb_bars.setProperty("u_val", "bars")

        curr_u = self.config_mgr.get("usage_style", "neon_rings")
        if curr_u == "bars":
            rb_bars.setChecked(True)
        else:
            rb_rings.setChecked(True)

        self.usage_bg.addButton(rb_rings, 1)
        self.usage_bg.addButton(rb_bars, 2)
        usage_layout.addWidget(rb_rings)
        usage_layout.addWidget(rb_bars)
        self.usage_bg.buttonToggled.connect(self.on_usage_style_toggled)
        layout.addWidget(usage_group)

        # Temperature Thresholds Group
        temp_group = QGroupBox("🌡️ Progi temperatur dla ekranu (Kolorowanie ostrzeżeń)")
        temp_layout = QVBoxLayout(temp_group)

        warn_layout = QHBoxLayout()
        warn_layout.addWidget(QLabel("Próg ostrzegawczy (Żółty/Pomarańczowy):"))
        self.warn_spin = QSpinBox()
        self.warn_spin.setRange(40, 95)
        self.warn_spin.setSuffix(" °C")
        self.warn_spin.setValue(self.config_mgr.get("temp_warn_cpu", 75))
        self.warn_spin.valueChanged.connect(lambda v: self.config_mgr.set("temp_warn_cpu", v))
        warn_layout.addWidget(self.warn_spin)
        temp_layout.addLayout(warn_layout)

        crit_layout = QHBoxLayout()
        crit_layout.addWidget(QLabel("Próg krytyczny (Czerwony / Alarm):"))
        self.crit_spin = QSpinBox()
        self.crit_spin.setRange(60, 110)
        self.crit_spin.setSuffix(" °C")
        self.crit_spin.setValue(self.config_mgr.get("temp_crit_cpu", 85))
        self.crit_spin.valueChanged.connect(lambda v: self.config_mgr.set("temp_crit_cpu", v))
        crit_layout.addWidget(self.crit_spin)
        temp_layout.addLayout(crit_layout)

        layout.addWidget(temp_group)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _create_metric_row(self, title: str, color: str):
        row = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setFixedWidth(140)
        lbl.setStyleSheet("font-weight: 600;")
        row.addWidget(lbl)

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(0)
        pbar.setFixedHeight(14)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1e293b;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        row.addWidget(pbar)

        val_lbl = QLabel("0%")
        val_lbl.setFixedWidth(50)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val_lbl.setStyleSheet("font-weight: bold; color: #f8fafc;")
        row.addWidget(val_lbl)

        return row, (pbar, val_lbl)

    def update_live_metrics(self, metrics: dict):
        """Updates live GUI labels and progress bars."""
        cpu = metrics.get('cpu_percent', 0.0)
        ram = metrics.get('ram_percent', 0.0)
        gpu = metrics.get('gpu_percent', 0.0)

        cpu_bar, cpu_lbl = self.cpu_val_lbl
        cpu_bar.setValue(int(cpu))
        cpu_lbl.setText(f"{cpu:.0f}%")

        ram_bar, ram_lbl = self.ram_val_lbl
        ram_bar.setValue(int(ram))
        ram_lbl.setText(f"{ram:.0f}%")

        gpu_bar, gpu_lbl = self.gpu_val_lbl
        gpu_bar.setValue(int(gpu))
        gpu_lbl.setText(f"{gpu:.0f}%")

        # Temps
        cpu_t = metrics.get('cpu_temp', 0.0)
        gpu_t = metrics.get('gpu_temp', 0.0)
        nvme_t = metrics.get('nvme_temp', 0.0)

        self.cpu_temp_lbl.setText(f"🔥 CPU: {cpu_t:.1f}°C")
        self.gpu_temp_lbl.setText(f"🎮 GPU: {gpu_t:.1f}°C")
        self.nvme_temp_lbl.setText(f"💾 NVMe: {nvme_t:.1f}°C")

    def on_usage_style_toggled(self, button, checked):
        if checked:
            val = button.property("u_val")
            self.config_mgr.set("usage_style", val)
            self.config_changed.emit()
