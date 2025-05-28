"""
Search Bar Widget for DOI Citation Manager
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QCheckBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon


class SearchBarWidget(QWidget):
    """Widget for search functionality and filters"""

    search_requested = pyqtSignal(str)  # search query
    filter_changed = pyqtSignal(dict)  # filter parameters

    def __init__(self):
        super().__init__()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.emit_search)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup search bar UI"""
        # Main frame
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setLineWidth(1)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(frame)
        main_layout.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout(frame)
        layout.setSpacing(8)

        # Search icon/label
        search_icon = QLabel("🔍")
        layout.addWidget(search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search papers by title, author, or keyword..."
        )
        self.search_input.setMinimumWidth(300)
        layout.addWidget(self.search_input)

        # Search in dropdown
        self.search_in_combo = QComboBox()
        self.search_in_combo.addItem("All Projects", "all")
        self.search_in_combo.addItem("Current Project", "current")
        self.search_in_combo.addItem("Selected Papers", "selected")
        self.search_in_combo.setMinimumWidth(120)
        layout.addWidget(self.search_in_combo)

        # Filter separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator1)

        # Filter by type
        layout.addWidget(QLabel("Show:"))

        self.show_papers_cb = QCheckBox("Papers")
        self.show_papers_cb.setChecked(True)
        layout.addWidget(self.show_papers_cb)

        self.show_projects_cb = QCheckBox("Projects")
        self.show_projects_cb.setChecked(True)
        layout.addWidget(self.show_projects_cb)

        # Filter separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)

        # Tag filter
        layout.addWidget(QLabel("Tag:"))

        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("All Tags", "all")
        self.tag_filter_combo.setMinimumWidth(100)
        layout.addWidget(self.tag_filter_combo)

        # Year filter
        layout.addWidget(QLabel("Year:"))

        self.year_filter_combo = QComboBox()
        self.year_filter_combo.addItem("All Years", "all")
        self.year_filter_combo.setMinimumWidth(80)
        layout.addWidget(self.year_filter_combo)

        # Clear filters button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMaximumWidth(60)
        layout.addWidget(self.clear_btn)

        layout.addStretch()

    def connect_signals(self):
        """Connect widget signals"""
        # Search input with delay
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.emit_search)

        # Filter controls
        self.search_in_combo.currentTextChanged.connect(self.emit_filter_change)
        self.show_papers_cb.toggled.connect(self.emit_filter_change)
        self.show_projects_cb.toggled.connect(self.emit_filter_change)
        self.tag_filter_combo.currentTextChanged.connect(self.emit_filter_change)
        self.year_filter_combo.currentTextChanged.connect(self.emit_filter_change)

        # Clear button
        self.clear_btn.clicked.connect(self.clear_filters)

    def on_search_text_changed(self, text):
        """Handle search text change with delay"""
        # Stop previous timer
        self.search_timer.stop()

        # Start new timer for delayed search
        if text.strip():
            self.search_timer.start(500)  # 500ms delay
        else:
            self.emit_search()  # Immediate clear

    def emit_search(self):
        """Emit search signal"""
        query = self.search_input.text().strip()
        self.search_requested.emit(query)

    def emit_filter_change(self):
        """Emit filter change signal"""
        filters = self.get_current_filters()
        self.filter_changed.emit(filters)

    def get_current_filters(self):
        """Get current filter settings"""
        return {
            "search_in": self.search_in_combo.currentData(),
            "show_papers": self.show_papers_cb.isChecked(),
            "show_projects": self.show_projects_cb.isChecked(),
            "tag_filter": self.tag_filter_combo.currentData(),
            "year_filter": self.year_filter_combo.currentData(),
        }

    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.search_in_combo.setCurrentIndex(0)
        self.show_papers_cb.setChecked(True)
        self.show_projects_cb.setChecked(True)
        self.tag_filter_combo.setCurrentIndex(0)
        self.year_filter_combo.setCurrentIndex(0)

        self.emit_search()
        self.emit_filter_change()

    def focus_search(self):
        """Focus on search input"""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def update_tag_filter(self, available_tags):
        """Update tag filter options"""
        current_tag = self.tag_filter_combo.currentData()

        # Clear and repopulate
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All Tags", "all")

        for tag in sorted(available_tags):
            self.tag_filter_combo.addItem(tag, tag)

        # Restore selection if possible
        if current_tag and current_tag != "all":
            index = self.tag_filter_combo.findData(current_tag)
            if index >= 0:
                self.tag_filter_combo.setCurrentIndex(index)

    def update_year_filter(self, available_years):
        """Update year filter options"""
        current_year = self.year_filter_combo.currentData()

        # Clear and repopulate
        self.year_filter_combo.clear()
        self.year_filter_combo.addItem("All Years", "all")

        for year in sorted(available_years, reverse=True):
            self.year_filter_combo.addItem(str(year), year)

        # Restore selection if possible
        if current_year and current_year != "all":
            index = self.year_filter_combo.findData(current_year)
            if index >= 0:
                self.year_filter_combo.setCurrentIndex(index)

    def set_search_scope(self, scope):
        """Set search scope programmatically"""
        index = self.search_in_combo.findData(scope)
        if index >= 0:
            self.search_in_combo.setCurrentIndex(index)
