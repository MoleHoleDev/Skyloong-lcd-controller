#!/usr/bin/env python3
import sys
import os
import signal
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

# Ensure current folder is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ui.main_window import MainWindow

def main():
    parser = argparse.ArgumentParser(description="Skyloong LCD Controller — GK104 Pro Linux Software")
    parser.add_argument("--daemon", action="store_true", help="Start application minimized to system tray in background")
    parser.add_argument("--minimized", action="store_true", help="Start minimized to system tray")
    args = parser.parse_args()

    # Enable Ctrl+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("Skyloong LCD Controller")
    app.setOrganizationName("SkyloongLinux")
    app.setQuitOnLastWindowClosed(False)

    # Allow Python signals to be handled by Qt
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    window = MainWindow(daemon_mode=(args.daemon or args.minimized))
    if not (args.daemon or args.minimized):
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
