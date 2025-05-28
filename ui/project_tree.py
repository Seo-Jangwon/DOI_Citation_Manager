"""
Project Tree Widget for DOI Citation Manager
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QInputDialog,
    QMessageBox,
    QMenu,
    QLabel,
    QLineEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction


class NewProjectDialog(QDialog):
    """Dialog for creating new project"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(300, 120)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter project name")
        form_layout.addRow("Project Name:", self.name_input)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_input.textChanged.connect(self.validate_input)
        self.validate_input()

    def validate_input(self):
        """Validate project name input"""
        name = self.name_input.text().strip()
        buttons = self.findChild(QDialogButtonBox)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(bool(name))

    def get_project_name(self):
        """Get the entered project name"""
        return self.name_input.text().strip()


class ProjectTreeWidget(QWidget):
    """Widget for displaying project tree structure"""

    project_selected = pyqtSignal(str)  # project_id
    paper_selected = pyqtSignal(dict)  # paper_data

    def __init__(self, project_manager):
        super().__init__()
        self.project_manager = project_manager
        self.current_project = None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the tree widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header with title and buttons
        header_layout = QHBoxLayout()

        title_label = QLabel("📁 Projects")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Action buttons
        self.new_btn = QPushButton("New Project")
        self.new_btn.setToolTip("Create New Project")
        header_layout.addWidget(self.new_btn)

        layout.addLayout(header_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        # Stats label
        self.stats_label = QLabel("No projects")
        self.stats_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.stats_label)

    def connect_signals(self):
        """Connect widget signals"""
        self.new_btn.clicked.connect(self.create_new_project)

        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemExpanded.connect(self.on_item_expanded)

    def load_projects(self, projects):
        """Load projects into tree"""
        self.tree.clear()

        for project in projects:
            project_item = QTreeWidgetItem(self.tree)
            project_item.setText(0, f"📁 {project['name']}")
            project_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"type": "project", "id": project["id"], "data": project},
            )

            # Load papers in project
            papers = self.project_manager.get_papers_in_project(project["id"])
            for paper in papers:
                paper_item = QTreeWidgetItem(project_item)
                title = paper.get("title", "Unknown Title")[:50]
                if len(paper.get("title", "")) > 50:
                    title += "..."
                paper_item.setText(0, f"📄 {title}")
                paper_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {"type": "paper", "id": paper.get("id"), "data": paper},
                )

            # Set project item expanded by default if it has papers
            if papers:
                project_item.setExpanded(True)

        self.update_stats()

    def on_item_expanded(self, item):
        """Handle item expansion"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data and item_data["type"] == "project":
            # Refresh papers when project is expanded
            self.refresh_project_papers(item, item_data["id"])

    def refresh_project_papers(self, project_item, project_id):
        """Refresh papers for a specific project item"""
        # Clear existing children
        project_item.takeChildren()

        # Reload papers
        papers = self.project_manager.get_papers_in_project(project_id)
        for paper in papers:
            paper_item = QTreeWidgetItem(project_item)
            title = paper.get("title", "Unknown Title")[:50]
            if len(paper.get("title", "")) > 50:
                title += "..."
            paper_item.setText(0, f"📄 {title}")
            paper_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"type": "paper", "id": paper.get("id"), "data": paper},
            )

    def update_stats(self):
        """Update statistics label"""
        project_count = self.tree.topLevelItemCount()
        total_papers = 0

        for i in range(project_count):
            project_item = self.tree.topLevelItem(i)
            papers = self.project_manager.get_papers_in_project(
                project_item.data(0, Qt.ItemDataRole.UserRole)["id"]
            )
            total_papers += len(papers)

        self.stats_label.setText(f"{project_count} projects, {total_papers} papers")

    def on_selection_changed(self):
        """Handle tree selection change"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        item_data = item.data(0, Qt.ItemDataRole.UserRole)

        if item_data["type"] == "project":
            self.current_project = item_data["id"]
            self.project_selected.emit(item_data["id"])

        elif item_data["type"] == "paper":
            # Get parent project
            parent_item = item.parent()
            if parent_item:
                parent_data = parent_item.data(0, Qt.ItemDataRole.UserRole)
                self.current_project = parent_data["id"]

            self.paper_selected.emit(item_data["data"])

    def on_item_double_clicked(self, item, column):
        """Handle item double click"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)

        if item_data["type"] == "project":
            # Toggle expand/collapse
            item.setExpanded(not item.isExpanded())
        elif item_data["type"] == "paper":
            # Show paper details
            self.paper_selected.emit(item_data["data"])

    def show_context_menu(self, position):
        """Show context menu"""
        item = self.tree.itemAt(position)
        if not item:
            return

        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        if item_data["type"] == "project":
            rename_action = QAction("Rename Project", self)
            rename_action.triggered.connect(lambda: self.rename_project(item))
            menu.addAction(rename_action)

            delete_action = QAction("Delete Project", self)
            delete_action.triggered.connect(lambda: self.delete_project(item))
            menu.addAction(delete_action)

            menu.addSeparator()

            expand_action = QAction("Expand All", self)
            expand_action.triggered.connect(lambda: item.setExpanded(True))
            menu.addAction(expand_action)

            collapse_action = QAction("Collapse All", self)
            collapse_action.triggered.connect(lambda: item.setExpanded(False))
            menu.addAction(collapse_action)

        elif item_data["type"] == "paper":
            view_action = QAction("View Details", self)
            view_action.triggered.connect(
                lambda: self.paper_selected.emit(item_data["data"])
            )
            menu.addAction(view_action)

            remove_action = QAction("Remove from Project", self)
            remove_action.triggered.connect(lambda: self.remove_paper(item))
            menu.addAction(remove_action)

        menu.exec(self.tree.mapToGlobal(position))

    def create_new_project(self):
        """Create new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_project_name()
            if name:
                try:
                    project = self.project_manager.create_project(name)
                    self.add_project_to_tree(project)
                    self.update_stats()
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Failed to create project:\n{str(e)}"
                    )

    def rename_project(self, item):
        """Rename selected project"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)

        if item_data["type"] != "project":
            return

        current_name = item_data["data"]["name"]
        new_name, ok = QInputDialog.getText(
            self, "Rename Project", "Enter new name:", text=current_name
        )

        if ok and new_name.strip() and new_name.strip() != current_name:
            try:
                self.project_manager.rename_project(item_data["id"], new_name.strip())
                item.setText(0, f"📁 {new_name.strip()}")
                item_data["data"]["name"] = new_name.strip()
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to rename project:\n{str(e)}"
                )

    def delete_project(self, item):
        """Delete selected project"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)

        if item_data["type"] != "project":
            return

        project_name = item_data["data"]["name"]
        paper_count = item.childCount()

        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Delete project '{project_name}' and its {paper_count} papers?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.project_manager.delete_project(item_data["id"])
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
                self.update_stats()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to delete project:\n{str(e)}"
                )

    def remove_paper(self, paper_item):
        """Remove paper from project"""
        paper_data = paper_item.data(0, Qt.ItemDataRole.UserRole)
        project_item = paper_item.parent()

        reply = QMessageBox.question(
            self,
            "Remove Paper",
            "Remove this paper from the project?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                project_data = project_item.data(0, Qt.ItemDataRole.UserRole)
                self.project_manager.remove_paper_from_project(
                    project_data["id"], paper_data["id"]
                )
                project_item.removeChild(paper_item)
                self.update_stats()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to remove paper:\n{str(e)}"
                )

    def add_project_to_tree(self, project):
        """Add new project to tree"""
        project_item = QTreeWidgetItem(self.tree)
        project_item.setText(0, f"📁 {project['name']}")
        project_item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {"type": "project", "id": project["id"], "data": project},
        )

    def refresh_current_project(self):
        """Refresh papers in current project"""
        if not self.current_project:
            return

        # Find project item
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item_data = item.data(0, Qt.ItemDataRole.UserRole)

            if item_data["id"] == self.current_project:
                # Refresh papers for this project
                self.refresh_project_papers(item, self.current_project)
                self.update_stats()
                break
