import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QBrush
from PIL import Image

class LCDPreviewWidget(QWidget):
    """
    Renders a realistic simulation of the Skyloong GK104 Pro 2-inch LCD screen.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pil_image: Image.Image = None
        self.current_pixmap: QPixmap = None
        self.fps_counter = 0
        self.last_mode_name = "Custom"
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Title / Status
        header_layout = QHBoxLayout()
        title_lbl = QLabel("🖥️ PODGLĄD EKRANU LCD")
        title_lbl.setStyleSheet("font-weight: bold; color: #00f0ff; font-size: 13px;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        self.fps_lbl = QLabel("30 FPS")
        self.fps_lbl.setStyleSheet("color: #10b981; font-weight: bold; background: #0f172a; padding: 2px 8px; border-radius: 4px; border: 1px solid #1e293b; font-size: 11px;")
        header_layout.addWidget(self.fps_lbl)
        layout.addLayout(header_layout)

        # LCD Hardware Bezel Container (320x240 widescreen)
        self.bezel = QFrame()
        self.bezel.setFixedSize(344, 264)
        self.bezel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a2233, stop:1 #0c111a);
                border: 3px solid #2a374f;
                border-radius: 16px;
            }
        """)
        
        bezel_layout = QVBoxLayout(self.bezel)
        bezel_layout.setContentsMargins(10, 10, 10, 10)
        bezel_layout.setAlignment(Qt.AlignCenter)

        # Actual screen label inside bezel (320x240)
        self.screen_lbl = QLabel()
        self.screen_lbl.setFixedSize(320, 240)
        self.screen_lbl.setStyleSheet("background-color: #000000; border-radius: 6px; border: 1px solid #101622;")
        self.screen_lbl.setAlignment(Qt.AlignCenter)
        bezel_layout.addWidget(self.screen_lbl)

        # Center the bezel in outer layout
        bezel_container = QHBoxLayout()
        bezel_container.addStretch()
        bezel_container.addWidget(self.bezel)
        bezel_container.addStretch()
        layout.addLayout(bezel_container)

        # Info & Action Buttons
        info_layout = QHBoxLayout()
        self.mode_lbl = QLabel("Tryb: Aktywny")
        self.mode_lbl.setStyleSheet("color: #94a3b8; font-weight: 500; font-size: 12px;")
        info_layout.addWidget(self.mode_lbl)
        info_layout.addStretch()

        screenshot_btn = QPushButton("📸 Zrzut")
        screenshot_btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
        screenshot_btn.clicked.connect(self.save_screenshot)
        info_layout.addWidget(screenshot_btn)
        layout.addLayout(info_layout)

    def update_frame(self, pil_image: Image.Image, mode_name: str = ""):
        """Updates the LCD preview with a new rendered PIL image."""
        self.current_pil_image = pil_image
        if mode_name:
            self.mode_lbl.setText(f"Tryb: {mode_name}")

        try:
            # Convert PIL Image to QImage
            if pil_image.mode != "RGBA":
                pil_image = pil_image.convert("RGBA")
            data = pil_image.tobytes("raw", "RGBA")
            qim = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
            pix = QPixmap.fromImage(qim)
            
            # Scale to fit 320x240 smoothly
            self.screen_lbl.setPixmap(pix.scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print(f"[LCD Preview] Conversion error: {e}")

    def save_screenshot(self):
        """Saves current frame to PNG image."""
        if not self.current_pil_image:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz zrzut ekranu LCD", "skyloong_lcd_frame.png", "Obrazy PNG (*.png)"
        )
        if path:
            try:
                self.current_pil_image.save(path)
            except Exception as e:
                print(f"[LCD Preview] Error saving screenshot: {e}")
