"""
Detail Panel Widget for DOI Citation Manager
- 모든 인용 형식 자동 표시
- 향상된 UI/UX
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QLineEdit,
    QComboBox,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QApplication,
    QSplitter,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

from config import CITATION_FORMATS


class CitationDisplay(QFrame):
    """Widget for displaying citation in different formats)"""

    copy_requested = pyqtSignal(str)

    def __init__(self, format_name, citation_text):
        super().__init__()
        self.format_name = format_name
        self.citation_text = citation_text
        self.setup_ui()

    def setup_ui(self):
        """Setup citation display UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Header with format name and copy button
        header_layout = QHBoxLayout()

        format_label = QLabel(self.format_name)
        format_label.setStyleSheet(
            "font-weight: bold; color: #2196F3; font-size: 11px;"
        )
        header_layout.addWidget(format_label)

        header_layout.addStretch()

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setToolTip(f"Copy {self.format_name} citation to clipboard")
        copy_btn.setMaximumWidth(70)
        copy_btn.clicked.connect(self.copy_citation)
        header_layout.addWidget(copy_btn)

        layout.addLayout(header_layout)

        # Citation text with better styling
        citation_label = QLabel(self.citation_text)
        citation_label.setWordWrap(True)
        citation_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        # 인용문 타입에 따른 스타일링
        if self.is_structured_format():
            font = QFont("Courier New", 9)  # Monospace for BibTeX, RIS
            citation_label.setFont(font)
            citation_label.setStyleSheet(
                "padding: 10px; background-color: #f8f8f8; border-radius: 4px; "
                "border-left: 3px solid #2196F3; font-family: 'Courier New', monospace;"
            )
        else:
            citation_label.setStyleSheet(
                "padding: 10px; background-color: #f5f5f5; border-radius: 4px; "
                "line-height: 1.4; border-left: 3px solid #4CAF50;"
            )

        layout.addWidget(citation_label)

    def is_structured_format(self):
        """Check if format is structured (BibTeX, RIS, JSON)"""
        return self.format_name in ["BibTeX", "RIS (EndNote/Mendeley)", "CSL-JSON"]

    def copy_citation(self):
        """Copy citation to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.citation_text)
        self.copy_requested.emit(f"Copied {self.format_name} citation to clipboard")


class TagWidget(QWidget):
    """Widget for managing tags"""

    tags_changed = pyqtSignal(list)

    def __init__(self, tags=None):
        super().__init__()
        self.tags = tags or []
        self.setup_ui()

    def setup_ui(self):
        """Setup tag widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Tag input section
        input_layout = QHBoxLayout()

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Add new tag...")
        self.tag_input.setMaximumWidth(150)
        self.tag_input.returnPressed.connect(self.add_tag)
        input_layout.addWidget(self.tag_input)

        add_btn = QPushButton("Add")
        add_btn.setMaximumWidth(50)
        add_btn.clicked.connect(self.add_tag)
        input_layout.addWidget(add_btn)

        input_layout.addStretch()
        layout.addLayout(input_layout)

        # Tags display area
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.tags_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(40)

        layout.addWidget(scroll_area)

        self.refresh_tags()

    def refresh_tags(self):
        """Refresh tag display"""
        # Clear existing tags
        for i in reversed(range(self.tags_layout.count())):
            child = self.tags_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # Add new tag widgets
        for tag in self.tags:
            tag_widget = self.create_tag_widget(tag)
            self.tags_layout.addWidget(tag_widget)

        self.tags_layout.addStretch()

    def create_tag_widget(self, tag):
        """Create individual tag widget"""
        tag_frame = QFrame()
        tag_frame.setStyleSheet(
            "QFrame { background-color: #E3F2FD; border-radius: 12px; padding: 2px; }"
            "QFrame:hover { background-color: #BBDEFB; }"
        )

        layout = QHBoxLayout(tag_frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        tag_label = QLabel(tag)
        tag_label.setStyleSheet("font-size: 10px; color: #1976D2; font-weight: bold;")
        layout.addWidget(tag_label)

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet(
            "QPushButton { border: none; font-size: 10px; font-weight: bold; "
            "color: #666; background-color: transparent; border-radius: 8px; }"
            "QPushButton:hover { background-color: #f44336; color: white; }"
        )
        remove_btn.clicked.connect(lambda: self.remove_tag(tag))
        layout.addWidget(remove_btn)

        return tag_frame

    def add_tag(self):
        """Add new tag"""
        tag = self.tag_input.text().strip()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.tag_input.clear()
            self.refresh_tags()
            self.tags_changed.emit(self.tags)

    def remove_tag(self, tag):
        """Remove tag"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.refresh_tags()
            self.tags_changed.emit(self.tags)


class DetailPanelWidget(QWidget):
    """Widget for displaying paper details and citations"""

    def __init__(self):
        super().__init__()
        self.current_paper = None
        self.setup_ui()

    def setup_ui(self):
        """Setup detail panel UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_label = QLabel("📄 Paper Details")
        header_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #1976D2;"
        )
        layout.addWidget(header_label)

        # Tab widget for different views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #ccc; }
            QTabBar::tab { 
                background-color: #f0f0f0; 
                padding: 8px 16px; 
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected { 
                background-color: white; 
                border-bottom: 2px solid #2196F3;
            }
        """
        )
        layout.addWidget(self.tabs)

        # Details tab
        self.details_tab = self.create_details_tab()
        self.tabs.addTab(self.details_tab, "📋 Details")

        # Citations tab (자동으로 모든 형식 표시)
        self.citations_tab = self.create_citations_tab()
        self.tabs.addTab(self.citations_tab, "📚 Citations")

        # Abstract tab
        self.abstract_tab = self.create_abstract_tab()
        self.tabs.addTab(self.abstract_tab, "📄 Abstract")

        # Notes tab
        self.notes_tab = self.create_notes_tab()
        self.tabs.addTab(self.notes_tab, "💭 Notes")

    def create_details_tab(self):
        """Create paper details tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Paper info section
        info_group = QGroupBox("Paper Information")
        info_layout = QVBoxLayout(info_group)

        self.title_label = QLabel("No paper selected")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1976D2;"
        )
        info_layout.addWidget(self.title_label)

        self.authors_label = QLabel("")
        self.authors_label.setWordWrap(True)
        self.authors_label.setStyleSheet(
            "font-size: 11px; color: #555; margin-bottom: 4px;"
        )
        info_layout.addWidget(self.authors_label)

        self.journal_label = QLabel("")
        self.journal_label.setWordWrap(True)
        self.journal_label.setStyleSheet("font-size: 11px; margin-bottom: 8px;")
        info_layout.addWidget(self.journal_label)

        self.doi_label = QLabel("")
        self.doi_label.setWordWrap(True)
        self.doi_label.setStyleSheet(
            "font-size: 10px; color: #2196F3; margin-bottom: 12px; font-family: monospace;"
        )
        info_layout.addWidget(self.doi_label)

        scroll_layout.addWidget(info_group)

        # Tags section
        tags_group = QGroupBox("🏷️ Tags")
        tags_layout = QVBoxLayout(tags_group)

        self.tag_widget = TagWidget()
        self.tag_widget.tags_changed.connect(self.on_tags_changed)
        tags_layout.addWidget(self.tag_widget)

        scroll_layout.addWidget(tags_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        return widget

    def create_citations_tab(self):
        """Create citations tab (모든 형식 자동 표시)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter section (simplified)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.format_combo = QComboBox()
        self.format_combo.addItem("Show All Formats", "all")
        self.format_combo.addItem("Academic Formats Only", "academic")
        self.format_combo.addItem("Export Formats Only", "export")
        for format_key, format_info in CITATION_FORMATS.items():
            self.format_combo.addItem(format_info["display_name"], format_key)
        self.format_combo.currentTextChanged.connect(self.filter_citations)
        filter_layout.addWidget(self.format_combo)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Citations scroll area
        self.citations_scroll = QScrollArea()
        self.citations_scroll.setWidgetResizable(True)
        self.citations_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.citations_widget = QWidget()
        self.citations_layout = QVBoxLayout(self.citations_widget)
        self.citations_scroll.setWidget(self.citations_widget)

        layout.addWidget(self.citations_scroll)

        return widget

    def create_abstract_tab(self):
        """Create abstract tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.abstract_text = QTextEdit()
        self.abstract_text.setReadOnly(True)
        self.abstract_text.setPlaceholderText("No abstract available")
        self.abstract_text.setStyleSheet(
            "QTextEdit { font-size: 11px; line-height: 1.5; padding: 10px; }"
        )
        layout.addWidget(self.abstract_text)

        return widget

    def create_notes_tab(self):
        """Create notes tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        notes_label = QLabel("💭 Personal Notes")
        notes_label.setStyleSheet(
            "font-weight: bold; margin-bottom: 8px; color: #1976D2;"
        )
        layout.addWidget(notes_label)

        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText(
            "Add your personal notes about this paper...\n\n"
            "• Key findings\n• Methodology notes\n• Questions for further research\n• Personal insights"
        )
        self.notes_text.textChanged.connect(self.on_notes_changed)
        layout.addWidget(self.notes_text)

        return widget

    def display_paper(self, paper_data):
        """Display paper details"""
        self.current_paper = paper_data

        # Update details tab
        title = paper_data.get("title", "Unknown Title")
        self.title_label.setText(title)

        authors = paper_data.get("authors", [])
        if isinstance(authors, list):
            authors_text = ", ".join(
                [
                    f"{author.get('given', '')} {author.get('family', '')}".strip()
                    for author in authors
                    if isinstance(author, dict)
                ]
            )
            if not authors_text:
                authors_text = ", ".join([str(author) for author in authors])
        else:
            authors_text = str(authors)
        self.authors_label.setText(f"Authors: {authors_text}")

        # Journal info with enhanced formatting
        journal_parts = []
        journal = paper_data.get("container-title", ["Unknown Journal"])
        if isinstance(journal, list):
            journal = journal[0] if journal else "Unknown Journal"
        journal_parts.append(journal)

        year = self.extract_year(paper_data)
        if year:
            journal_parts.append(f"({year})")

        volume = paper_data.get("volume", "")
        if volume:
            journal_parts.append(f"Vol. {volume}")

        issue = paper_data.get("issue", "")
        if issue:
            journal_parts.append(f"Issue {issue}")

        pages = paper_data.get("page", "")
        if pages:
            journal_parts.append(f"pp. {pages}")

        self.journal_label.setText(" • ".join(journal_parts))

        # DOI with clickable link
        doi = paper_data.get("DOI", "")
        if doi:
            self.doi_label.setText(f"DOI: {doi}")
            self.doi_label.setToolTip(f"Click to open: https://doi.org/{doi}")
        else:
            self.doi_label.setText("No DOI available")

        # Tags
        tags = paper_data.get("tags", [])
        self.tag_widget.tags = tags.copy()
        self.tag_widget.refresh_tags()

        # Update citations tab (모든 형식 표시)
        self.display_citations(paper_data)

        # Update abstract tab
        abstract = paper_data.get("abstract", "")
        self.abstract_text.setPlainText(
            abstract if abstract else "No abstract available"
        )

        # Update notes tab
        notes = paper_data.get("notes", "")
        self.notes_text.setPlainText(notes)

    def extract_year(self, paper_data):
        """Extract publication year"""
        if "published-print" in paper_data:
            date_parts = paper_data["published-print"].get("date-parts", [[]])
            if date_parts and date_parts[0] and len(date_parts[0]) > 0:
                return date_parts[0][0]

        if "published-online" in paper_data:
            date_parts = paper_data["published-online"].get("date-parts", [[]])
            if date_parts and date_parts[0] and len(date_parts[0]) > 0:
                return date_parts[0][0]

        return None

    def display_citations(self, paper_data):
        """Display citations in all formats"""
        # Clear existing citations
        for i in reversed(range(self.citations_layout.count())):
            child = self.citations_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        citations = paper_data.get("citations", {})

        if not citations:
            no_citations_label = QLabel("No citations available")
            no_citations_label.setStyleSheet(
                "font-style: italic; color: #666; padding: 20px;"
            )
            no_citations_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.citations_layout.addWidget(no_citations_label)
            return

        # Group citations by category
        academic_formats = [
            "APA",
            "IEEE",
            "Nature",
            "Science",
            "Cell",
            "PNAS",
            "PLoS",
            "Vancouver",
        ]
        standard_formats = ["MLA", "Chicago", "Harvard"]
        export_formats = ["BibTeX", "RIS", "JSON"]

        # Add citations in organized groups
        self.add_citation_group("Academic Journals", academic_formats, citations)
        self.add_citation_group("Standard Formats", standard_formats, citations)
        self.add_citation_group("Export Formats", export_formats, citations)

        self.citations_layout.addStretch()

    def add_citation_group(self, group_name, format_keys, citations):
        """Add a group of citations"""
        has_citations = any(
            format_key in citations and citations[format_key]
            for format_key in format_keys
        )

        if not has_citations:
            return

        # Group header
        group_label = QLabel(group_name)
        group_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #1976D2; "
            "margin-top: 15px; margin-bottom: 5px;"
        )
        self.citations_layout.addWidget(group_label)

        # Add citations in this group
        for format_key in format_keys:
            if format_key in citations and citations[format_key]:
                format_info = CITATION_FORMATS.get(
                    format_key, {"display_name": format_key}
                )
                citation_widget = CitationDisplay(
                    format_info["display_name"], citations[format_key]
                )
                citation_widget.copy_requested.connect(self.show_copy_message)
                self.citations_layout.addWidget(citation_widget)

    def filter_citations(self):
        """Filter displayed citations"""
        filter_value = self.format_combo.currentData()

        # Show/hide citation widgets based on filter
        for i in range(self.citations_layout.count()):
            item = self.citations_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, CitationDisplay):
                    if filter_value == "all":
                        widget.show()
                    elif filter_value == "academic":
                        academic_names = [
                            CITATION_FORMATS[k]["display_name"]
                            for k in [
                                "APA",
                                "IEEE",
                                "Nature",
                                "Science",
                                "Cell",
                                "PNAS",
                                "PLoS",
                                "Vancouver",
                            ]
                            if k in CITATION_FORMATS
                        ]
                        widget.setVisible(widget.format_name in academic_names)
                    elif filter_value == "export":
                        export_names = [
                            CITATION_FORMATS[k]["display_name"]
                            for k in ["BibTeX", "RIS", "JSON"]
                            if k in CITATION_FORMATS
                        ]
                        widget.setVisible(widget.format_name in export_names)
                    else:
                        format_info = CITATION_FORMATS.get(filter_value, {})
                        widget.setVisible(
                            widget.format_name == format_info.get("display_name")
                        )

    def display_project_papers(self, papers):
        """Display list of papers in a project"""
        # Clear current display
        self.title_label.setText("📁 Project Papers")
        self.authors_label.setText(f"{len(papers)} papers in this project")
        self.journal_label.setText("")
        self.doi_label.setText("")

        # Clear other tabs
        self.abstract_text.setPlaceholderText("Select a paper to view its abstract")
        self.notes_text.setPlaceholderText("")

        # Show paper list in citations tab
        for i in reversed(range(self.citations_layout.count())):
            child = self.citations_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        if papers:
            list_widget = QListWidget()
            list_widget.setStyleSheet(
                """
                QListWidget::item { 
                    padding: 8px; 
                    border-bottom: 1px solid #eee; 
                }
                QListWidget::item:selected { 
                    background-color: #e3f2fd; 
                }
                QListWidget::item:hover { 
                    background-color: #f0f8ff; 
                }
            """
            )

            for paper in papers:
                title = paper.get("title", "Unknown Title")
                authors = paper.get("authors", [])

                if isinstance(authors, list) and authors:
                    first_author = authors[0]
                    if isinstance(first_author, dict):
                        author_name = f"{first_author.get('given', '')} {first_author.get('family', '')}".strip()
                    else:
                        author_name = str(first_author)
                else:
                    author_name = "Unknown Author"

                item_text = f"{title}\n{author_name}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, paper)
                list_widget.addItem(item)

            list_widget.itemClicked.connect(self.on_paper_list_clicked)
            self.citations_layout.addWidget(list_widget)
        else:
            empty_label = QLabel("No papers in this project")
            empty_label.setStyleSheet("font-style: italic; color: #666; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.citations_layout.addWidget(empty_label)

    def display_search_results(self, results):
        """Display search results"""
        self.title_label.setText("🔍 Search Results")
        self.authors_label.setText(f"{len(results)} papers found")
        self.journal_label.setText("")
        self.doi_label.setText("")

        # Clear other tabs
        self.abstract_text.setPlaceholderText("Select a paper to view its abstract")
        self.notes_text.setPlaceholderText("")

        # Show results in citations tab
        for i in reversed(range(self.citations_layout.count())):
            child = self.citations_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        if results:
            list_widget = QListWidget()
            list_widget.setStyleSheet(
                """
                QListWidget::item { 
                    padding: 10px; 
                    border-bottom: 1px solid #eee; 
                }
                QListWidget::item:selected { 
                    background-color: #e3f2fd; 
                }
                QListWidget::item:hover { 
                    background-color: #f0f8ff; 
                }
            """
            )

            for paper in results:
                title = paper.get("title", "Unknown Title")
                authors = paper.get("authors", [])

                if isinstance(authors, list) and authors:
                    first_author = authors[0]
                    if isinstance(first_author, dict):
                        author_name = f"{first_author.get('given', '')} {first_author.get('family', '')}".strip()
                    else:
                        author_name = str(first_author)
                else:
                    author_name = "Unknown Author"

                # Add publication year if available
                year = self.extract_year(paper)
                year_text = f" ({year})" if year else ""

                item_text = f"{title}{year_text}\n{author_name}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, paper)
                list_widget.addItem(item)

            list_widget.itemClicked.connect(self.on_paper_list_clicked)
            self.citations_layout.addWidget(list_widget)
        else:
            no_results_label = QLabel("No papers found matching your search")
            no_results_label.setStyleSheet(
                "font-style: italic; color: #666; padding: 20px;"
            )
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.citations_layout.addWidget(no_results_label)

    def on_paper_list_clicked(self, item):
        """Handle paper list item click"""
        paper_data = item.data(Qt.ItemDataRole.UserRole)
        self.display_paper(paper_data)

    def on_tags_changed(self, tags):
        """Handle tag changes"""
        if self.current_paper:
            self.current_paper["tags"] = tags
            # TODO: Save changes to storage

    def on_notes_changed(self):
        """Handle notes changes"""
        if self.current_paper:
            self.current_paper["notes"] = self.notes_text.toPlainText()
            # TODO: Save changes to storage

    def show_copy_message(self, message):
        """Show copy confirmation message"""
        # Show temporary message (could be enhanced with toast notifications)
        if hasattr(self, "parent") and hasattr(self.parent(), "statusBar"):
            self.parent().statusBar().showMessage(message, 3000)  # 3 seconds
