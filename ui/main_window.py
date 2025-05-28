"""
Main Window UI for DOI Citation Manager
- UI 간소화
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QMenuBar,
    QStatusBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from .doi_input import DOIInputWidget
from .project_tree import ProjectTreeWidget
from .detail_panel import DetailPanelWidget
from .search_bar import SearchBarWidget
from .theme_manager import ThemeManager
from core.doi_converter import DOIConverter
from core.project_manager import ProjectManager
from core.paper_manager import PaperManager
from config import APP_NAME, VERSION, SHORTCUTS


class MainWindow(QMainWindow):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.current_theme = "light"

        # Initialize managers
        self.doi_converter = DOIConverter()
        self.project_manager = ProjectManager(storage)
        self.paper_manager = PaperManager(storage)
        self.theme_manager = ThemeManager()

        # Setup UI
        self.setup_ui()
        self.setup_menus()
        self.setup_shortcuts()
        self.setup_statusbar()

        # Connect signals
        self.connect_signals()

        # Load data
        self.load_initial_data()

        # Apply theme
        self.theme_manager.apply_theme(self, self.current_theme)

    def setup_ui(self):
        """Setup the main UI layout"""
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(1000, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Search bar
        self.search_bar = SearchBarWidget()
        main_layout.addWidget(self.search_bar)

        # DOI input widget
        self.doi_input = DOIInputWidget()
        main_layout.addWidget(self.doi_input)

        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Project tree
        self.project_tree = ProjectTreeWidget(self.project_manager)
        splitter.addWidget(self.project_tree)

        # Right panel - Detail panel
        self.detail_panel = DetailPanelWidget()
        splitter.addWidget(self.detail_panel)

        # Set splitter proportions
        splitter.setSizes([300, 900])

    def setup_menus(self):
        """Setup menu bar (중복 기능 정리됨)"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_project_action = QAction("&New Project", self)
        new_project_action.setShortcut(QKeySequence(SHORTCUTS["new_project"]))
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        file_menu.addSeparator()

        import_action = QAction("&Import...", self)
        import_action.setShortcut(QKeySequence(SHORTCUTS["import"]))
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

        export_action = QAction("&Export...", self)
        export_action.setShortcut(QKeySequence(SHORTCUTS["export"]))
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        search_action = QAction("&Search", self)
        search_action.setShortcut(QKeySequence(SHORTCUTS["search"]))
        search_action.triggered.connect(self.focus_search)
        edit_menu.addAction(search_action)

        paste_doi_action = QAction("&Paste DOI and Convert", self)
        paste_doi_action.setShortcut(QKeySequence(SHORTCUTS["paste_doi"]))
        paste_doi_action.triggered.connect(self.paste_and_convert_doi)
        edit_menu.addAction(paste_doi_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        toggle_theme_action = QAction("Toggle &Theme", self)
        toggle_theme_action.setShortcut(QKeySequence(SHORTCUTS["toggle_theme"]))
        toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        batch_convert_action = QAction("&Batch Convert DOIs", self)
        batch_convert_action.triggered.connect(self.batch_convert)
        tools_menu.addAction(batch_convert_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Paste and convert DOI shortcut
        paste_shortcut = QKeySequence(SHORTCUTS["paste_doi"])
        paste_action = QAction(self)
        paste_action.setShortcut(paste_shortcut)
        paste_action.triggered.connect(self.paste_and_convert_doi)
        self.addAction(paste_action)

    def setup_statusbar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def connect_signals(self):
        """Connect widget signals"""
        # DOI input signals
        self.doi_input.doi_converted.connect(self.on_doi_converted)
        self.doi_input.batch_converted.connect(self.on_batch_converted)

        # Project tree signals
        self.project_tree.project_selected.connect(self.on_project_selected)
        self.project_tree.paper_selected.connect(self.on_paper_selected)

        # Search signals
        self.search_bar.search_requested.connect(self.on_search_requested)
        self.search_bar.filter_changed.connect(self.on_filter_changed)

    def load_initial_data(self):
        """Load initial data from storage"""
        projects = self.project_manager.get_all_projects()
        self.project_tree.load_projects(projects)

    # Slot methods
    def on_doi_converted(self, paper_data):
        """Handle single DOI conversion"""
        if self.project_tree.current_project:
            # Add paper to current project
            project_id = self.project_tree.current_project
            try:
                added_paper = self.paper_manager.add_paper_to_project(
                    project_id, paper_data
                )
                self.project_tree.refresh_current_project()
                self.detail_panel.display_paper(added_paper)

                title = paper_data.get("title", "Unknown Title")[:50]
                self.status_bar.showMessage(f"Added: {title}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to add paper to project:\n{str(e)}"
                )
        else:
            # Show dialog to select project or create new one
            self.show_project_selection_dialog(paper_data)

    def on_batch_converted(self, papers_data):
        """Handle batch DOI conversion"""
        if self.project_tree.current_project:
            project_id = self.project_tree.current_project
            for paper_data in papers_data:
                self.paper_manager.add_paper_to_project(project_id, paper_data)
            self.project_tree.refresh_current_project()
            self.status_bar.showMessage(f"Added {len(papers_data)} papers")
        else:
            self.status_bar.showMessage("Please select a project first")

    def on_project_selected(self, project_id):
        """Handle project selection"""
        papers = self.paper_manager.get_papers_in_project(project_id)
        self.detail_panel.display_project_papers(papers)

    def on_paper_selected(self, paper_data):
        """Handle paper selection"""
        self.detail_panel.display_paper(paper_data)

    def on_search_requested(self, query):
        """Handle search request"""
        results = self.paper_manager.search_papers(query)
        self.detail_panel.display_search_results(results)

    def on_filter_changed(self, filters):
        """Handle filter changes"""
        # Apply filters to current view
        pass

    # Action methods
    def new_project(self):
        """Create new project"""
        self.project_tree.create_new_project()

    def import_data(self):
        """Import data from file"""
        QMessageBox.information(self, "Import", "Import functionality coming soon!")

    def export_data(self):
        """Export data to file"""
        QMessageBox.information(self, "Export", "Export functionality coming soon!")

    def batch_convert(self):
        """Open batch convert dialog"""
        self.doi_input.show_batch_dialog()

    def focus_search(self):
        """Focus search bar"""
        self.search_bar.focus_search()

    def paste_and_convert_doi(self):
        """Paste DOI from clipboard and convert"""
        self.doi_input.paste_and_convert()

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_manager.apply_theme(self, self.current_theme)
        self.status_bar.showMessage(f"Switched to {self.current_theme} theme")

    def show_project_selection_dialog(self, paper_data):
        """Show dialog to select project for new paper"""
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QComboBox,
            QPushButton,
            QDialogButtonBox,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Project")
        dialog.setModal(True)
        dialog.resize(400, 150)

        layout = QVBoxLayout(dialog)

        # Paper info
        title = paper_data.get("title", "Unknown Title")
        info_label = QLabel(
            f"Add paper to project:\n{title[:60]}{'...' if len(title) > 60 else ''}"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Project selection
        project_layout = QHBoxLayout()
        project_layout.addWidget(QLabel("Project:"))

        project_combo = QComboBox()
        projects = self.project_manager.get_all_projects()

        if not projects:
            # No projects exist, create default one
            default_project = self.project_manager.create_project("My Papers")
            projects = [default_project]

        for project in projects:
            project_combo.addItem(project["name"], project["id"])

        project_layout.addWidget(project_combo)

        # New project button
        new_project_btn = QPushButton("New Project")
        new_project_btn.clicked.connect(
            lambda: self.create_project_from_dialog(dialog, project_combo)
        )
        project_layout.addWidget(new_project_btn)

        layout.addLayout(project_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_project_id = project_combo.currentData()
            if selected_project_id:
                try:
                    added_paper = self.paper_manager.add_paper_to_project(
                        selected_project_id, paper_data
                    )
                    self.project_tree.load_projects(
                        self.project_manager.get_all_projects()
                    )
                    self.detail_panel.display_paper(added_paper)

                    title = paper_data.get("title", "Unknown Title")[:50]
                    self.status_bar.showMessage(f"Added: {title}")

                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Failed to add paper:\n{str(e)}"
                    )

    def create_project_from_dialog(self, dialog, combo):
        """Create new project from dialog"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(dialog, "New Project", "Enter project name:")
        if ok and name.strip():
            try:
                new_project = self.project_manager.create_project(name.strip())
                combo.addItem(new_project["name"], new_project["id"])
                combo.setCurrentIndex(combo.count() - 1)
            except Exception as e:
                QMessageBox.critical(
                    dialog, "Error", f"Failed to create project:\n{str(e)}"
                )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About",
            f"{APP_NAME} v{VERSION}\n\n"
            "A tool for managing DOI citations and references.\n\n"
            "Built with PyQt6",
        )

    def closeEvent(self, event):
        """Handle window close event"""
        # Save any unsaved data
        try:
            self.storage.save_all()
            event.accept()
        except Exception as e:
            reply = QMessageBox.question(
                self,
                "Error Saving",
                f"Error saving data: {e}\n\nExit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
