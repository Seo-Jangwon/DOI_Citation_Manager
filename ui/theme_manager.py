"""
Theme Manager for DOI Citation Manager
- 리소스 파일 경로 수정
- 번들된 테마 파일 지원
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject
from config import THEMES, RESOURCES_DIR
import os
import sys
import logging

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """Manager for application themes (배포용 개선)"""

    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.ensure_theme_files()

    def ensure_theme_files(self):
        """테마 파일들이 존재하는지 확인하고 필요시 생성"""
        try:
            # 스타일 디렉토리 생성
            styles_dir = RESOURCES_DIR / "styles"
            styles_dir.mkdir(parents=True, exist_ok=True)

            # 라이트 테마 파일 생성/확인
            light_theme_path = styles_dir / "light_theme.qss"
            if not light_theme_path.exists():
                self.create_light_theme(light_theme_path)

            # 다크 테마 파일 생성/확인
            dark_theme_path = styles_dir / "dark_theme.qss"
            if not dark_theme_path.exists():
                self.create_dark_theme(dark_theme_path)

            logger.info(f"Theme files ensured in: {styles_dir}")

        except Exception as e:
            logger.error(f"Error ensuring theme files: {e}")

    def create_light_theme(self, path):
        """Create light theme stylesheet"""
        light_qss = """
/* Light Theme for DOI Citation Manager */

/* Main Window */
QMainWindow {
    background-color: #ffffff;
    color: #333333;
}

/* Widgets */
QWidget {
    background-color: #ffffff;
    color: #333333;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}

/* Buttons */
QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 16px;
}

QPushButton:hover {
    background-color: #e6e6e6;
    border-color: #2196F3;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #999;
    border-color: #ddd;
}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
    selection-background-color: #2196F3;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #2196F3;
    outline: none;
}

/* Combo Boxes */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
    min-width: 60px;
}

QComboBox:hover {
    border-color: #2196F3;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ccc;
    selection-background-color: #e3f2fd;
}

/* Tree Widget */
QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #ccc;
    alternate-background-color: #f8f8f8;
    outline: none;
}

QTreeWidget::item {
    padding: 4px;
    border: none;
}

QTreeWidget::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

QTreeWidget::item:hover {
    background-color: #f0f8ff;
}

QTreeWidget::branch:closed:has-children {
    image: none;
    border: none;
}

QTreeWidget::branch:open:has-children {
    image: none;
    border: none;
}

/* List Widget */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #ccc;
    alternate-background-color: #f8f8f8;
    outline: none;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #eee;
}

QListWidget::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

QListWidget::item:hover {
    background-color: #f0f8ff;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #ccc;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: 1px solid #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #e6e6e6;
}

/* Group Box */
QGroupBox {
    font-weight: bold;
    border: 2px solid #cccccc;
    border-radius: 4px;
    margin-top: 1ex;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

/* Frames */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: #fafafa;
}

/* Scroll Areas */
QScrollArea {
    border: 1px solid #ccc;
    background-color: #ffffff;
}

QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #ccc;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #999;
}

/* Menu Bar */
QMenuBar {
    background-color: #f8f8f8;
    border-bottom: 1px solid #ddd;
}

QMenuBar::item {
    padding: 6px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #e6e6e6;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #ccc;
}

QMenu::item {
    padding: 6px 12px;
}

QMenu::item:selected {
    background-color: #e3f2fd;
}

/* Status Bar */
QStatusBar {
    background-color: #f8f8f8;
    border-top: 1px solid #ddd;
    color: #666;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #ccc;
    border-radius: 4px;
    text-align: center;
    background-color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: #2196F3;
    border-radius: 3px;
}

/* Check Box */
QCheckBox {
    spacing: 6px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #ccc;
    border-radius: 2px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #2196F3;
    border-color: #2196F3;
}

/* Radio Button */
QRadioButton {
    spacing: 6px;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #ccc;
    border-radius: 7px;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    background-color: #2196F3;
    border-color: #2196F3;
}
"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(light_qss)
            logger.info(f"Light theme created: {path}")
        except Exception as e:
            logger.error(f"Error creating light theme: {e}")

    def create_dark_theme(self, path):
        """Create dark theme stylesheet"""
        dark_qss = """
/* Dark Theme for DOI Citation Manager */

/* Main Window */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

/* Widgets */
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}

/* Buttons */
QPushButton {
    background-color: #404040;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 16px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #64b5f6;
}

QPushButton:pressed {
    background-color: #363636;
}

QPushButton:disabled {
    background-color: #333;
    color: #666;
    border-color: #444;
}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #404040;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
    selection-background-color: #64b5f6;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #64b5f6;
    outline: none;
}

/* Combo Boxes */
QComboBox {
    background-color: #404040;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    min-width: 60px;
    color: #ffffff;
}

QComboBox:hover {
    border-color: #64b5f6;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border: none;
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #404040;
    border: 1px solid #555;
    selection-background-color: #1e88e5;
    color: #ffffff;
}

/* Tree Widget */
QTreeWidget {
    background-color: #363636;
    border: 1px solid #555;
    alternate-background-color: #404040;
    outline: none;
    color: #ffffff;
}

QTreeWidget::item {
    padding: 4px;
    border: none;
}

QTreeWidget::item:selected {
    background-color: #1e88e5;
    color: #ffffff;
}

QTreeWidget::item:hover {
    background-color: #424242;
}

/* List Widget */
QListWidget {
    background-color: #363636;
    border: 1px solid #555;
    alternate-background-color: #404040;
    outline: none;
    color: #ffffff;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #444;
}

QListWidget::item:selected {
    background-color: #1e88e5;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #424242;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #555;
    background-color: #363636;
}

QTabBar::tab {
    background-color: #404040;
    border: 1px solid #555;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
    color: #ffffff;
}

QTabBar::tab:selected {
    background-color: #363636;
    border-bottom: 1px solid #363636;
}

QTabBar::tab:hover:!selected {
    background-color: #4a4a4a;
}

/* Group Box */
QGroupBox {
    font-weight: bold;
    border: 2px solid #555555;
    border-radius: 4px;
    margin-top: 1ex;
    padding-top: 10px;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

/* Frames */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    border: 1px solid #555;
    border-radius: 4px;
    background-color: #333;
}

/* Scroll Areas */
QScrollArea {
    border: 1px solid #555;
    background-color: #363636;
}

QScrollBar:vertical {
    background-color: #404040;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #666;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #888;
}

/* Menu Bar */
QMenuBar {
    background-color: #333;
    border-bottom: 1px solid #555;
    color: #ffffff;
}

QMenuBar::item {
    padding: 6px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #4a4a4a;
}

QMenu {
    background-color: #404040;
    border: 1px solid #555;
    color: #ffffff;
}

QMenu::item {
    padding: 6px 12px;
}

QMenu::item:selected {
    background-color: #1e88e5;
}

/* Status Bar */
QStatusBar {
    background-color: #333;
    border-top: 1px solid #555;
    color: #ccc;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
    background-color: #404040;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #64b5f6;
    border-radius: 3px;
}

/* Check Box */
QCheckBox {
    spacing: 6px;
    color: #ffffff;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #666;
    border-radius: 2px;
    background-color: #404040;
}

QCheckBox::indicator:checked {
    background-color: #64b5f6;
    border-color: #64b5f6;
}

/* Radio Button */
QRadioButton {
    spacing: 6px;
    color: #ffffff;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #666;
    border-radius: 7px;
    background-color: #404040;
}

QRadioButton::indicator:checked {
    background-color: #64b5f6;
    border-color: #64b5f6;
}
"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(dark_qss)
            logger.info(f"Dark theme created: {path}")
        except Exception as e:
            logger.error(f"Error creating dark theme: {e}")

    def apply_theme(self, app_or_widget, theme_name):
        """Apply theme to application or widget"""
        self.current_theme = theme_name

        if theme_name in THEMES:
            theme_path = THEMES[theme_name]

            if theme_path.exists():
                try:
                    with open(theme_path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()

                    if hasattr(app_or_widget, "setStyleSheet"):
                        app_or_widget.setStyleSheet(stylesheet)
                    else:
                        # Assume it's QApplication
                        app_or_widget.setStyleSheet(stylesheet)

                    logger.info(f"Applied theme: {theme_name}")

                except Exception as e:
                    logger.error(f"Error loading theme {theme_name}: {e}")
                    self.apply_default_theme(app_or_widget)
            else:
                logger.warning(f"Theme file not found: {theme_path}")
                # Try to create the theme file
                self.ensure_theme_files()
                # Retry once
                if theme_path.exists():
                    self.apply_theme(app_or_widget, theme_name)
                else:
                    self.apply_default_theme(app_or_widget)
        else:
            logger.warning(f"Unknown theme: {theme_name}")
            self.apply_default_theme(app_or_widget)

    def apply_default_theme(self, app_or_widget):
        """Apply default (light) theme"""
        # Ensure theme files exist
        self.ensure_theme_files()
        self.apply_theme(app_or_widget, "light")

    def get_available_themes(self):
        """Get list of available themes"""
        return list(THEMES.keys())

    def get_current_theme(self):
        """Get current theme name"""
        return self.current_theme

    def toggle_theme(self, app_or_widget):
        """Toggle between light and dark theme"""
        if self.current_theme == "light":
            self.apply_theme(app_or_widget, "dark")
        else:
            self.apply_theme(app_or_widget, "light")

        return self.current_theme

    def theme_exists(self, theme_name):
        """Check if theme file exists"""
        if theme_name in THEMES:
            return THEMES[theme_name].exists()
        return False

    def get_theme_info(self):
        """Get information about available themes"""
        theme_info = {}
        for theme_name, theme_path in THEMES.items():
            theme_info[theme_name] = {
                "path": str(theme_path),
                "exists": theme_path.exists(),
                "size": theme_path.stat().st_size if theme_path.exists() else 0,
            }
        return theme_info
