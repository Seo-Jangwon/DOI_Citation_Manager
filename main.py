#!/usr/bin/env python3
"""
DOI Citation Manager - Main Entry Point
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import MainWindow
from data.storage import Storage
from config import APP_NAME, VERSION, WINDOW_SIZE


class DOICitationApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(VERSION)
        self.setOrganizationName("DOI Tools")

        # Initialize storage
        self.storage = Storage()

        # Create main window
        self.main_window = MainWindow(self.storage)
        self.main_window.resize(*WINDOW_SIZE)

    def run(self):
        self.main_window.show()
        return self.exec()


def main():
    """Main application entry point"""

    app = DOICitationApp(sys.argv)
    sys.exit(app.run())


if __name__ == "__main__":
    main()
