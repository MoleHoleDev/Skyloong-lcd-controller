"""
Dark Modern / Cyberpunk QSS Theme for Skyloong LCD Controller
"""

STYLE_SHEET = """
QMainWindow, QDialog {
    background-color: #0d111a;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
}

QWidget {
    background-color: transparent;
    color: #e2e8f0;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #111827;
    border-radius: 8px;
    padding: 6px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background: #0f172a;
    color: #94a3b8;
    padding: 7px 11px;
    margin-right: 3px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #1e293b;
    border-bottom: none;
    font-weight: 600;
    font-size: 12px;
}

QTabBar::tab:selected {
    background: #111827;
    color: #00f0ff;
    border-top: 2px solid #00f0ff;
}

QTabBar::tab:hover:!selected {
    background: #1e293b;
    color: #f1f5f9;
}

QGroupBox {
    border: 1px solid #1e293b;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 10px 10px 10px;
    background-color: #111827;
    font-weight: bold;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #111827;
}

QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2563eb;
    border-color: #3b82f6;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #0f172a;
    color: #475569;
    border-color: #1e293b;
}

QPushButton#AccentButton {
    background-color: #0284c7;
    border: 1px solid #00f0ff;
    color: #ffffff;
}

QPushButton#AccentButton:hover {
    background-color: #00f0ff;
    color: #080c14;
}

QPushButton#DangerButton {
    background-color: #991b1b;
    border: 1px solid #ef4444;
    color: #ffffff;
}

QPushButton#DangerButton:hover {
    background-color: #ef4444;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #0284c7;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #00f0ff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #f8fafc;
    selection-background-color: #1e293b;
    border: 1px solid #334155;
}

QCheckBox, QRadioButton {
    spacing: 8px;
    color: #cbd5e1;
    font-weight: 500;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #0f172a;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #00f0ff;
    border-color: #00f0ff;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #00f0ff;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #f8fafc;
    border: 2px solid #00f0ff;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QListWidget {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 4px;
    color: #f8fafc;
}

QListWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
    margin-bottom: 2px;
}

QListWidget::item:selected {
    background-color: #1e293b;
    color: #00f0ff;
    border-left: 3px solid #00f0ff;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #0b1120;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #00f0ff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #0b1120;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 25px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #00f0ff;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QStatusBar {
    background-color: #090d16;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
}

QProgressBar {
    background-color: #1e293b;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: #00f0ff;
    border-radius: 4px;
}
"""
