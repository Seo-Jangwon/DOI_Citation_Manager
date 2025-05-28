"""
DOI Input Widget for DOI Citation Manager
- Format 선택 제거 (모든 형식을 자동으로 생성)
- 더 유연한 DOI 입력 처리
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QTextEdit,
    QDialog,
    QProgressBar,
    QMessageBox,
    QButtonGroup,
    QRadioButton,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from core.doi_converter import DOIConverter
from utils.doi_validator import DOIValidator


class DOIConversionThread(QThread):
    """Thread for DOI conversion to avoid blocking UI"""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, doi_list):
        super().__init__()
        self.doi_list = doi_list
        self.converter = DOIConverter()

    def run(self):
        results = []
        total = len(self.doi_list)

        for i, doi in enumerate(self.doi_list):
            try:
                # 모든 형식을 자동으로 생성
                paper_data = self.converter.convert_doi(doi)
                results.append(paper_data)
                self.progress.emit(int((i + 1) / total * 100))
            except Exception as e:
                self.error.emit(f"Error converting {doi}: {str(e)}")
                continue

        self.finished.emit({"papers": results})


class BatchConvertDialog(QDialog):
    """Dialog for batch DOI conversion"""

    batch_completed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch DOI Conversion")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Enter multiple DOIs or URLs (one per line):\nSupported formats: DOI, full URLs, partial URLs"
        )
        layout.addWidget(instructions)

        # Text area for DOIs
        self.doi_text = QTextEdit()
        self.doi_text.setPlaceholderText(
            "10.1038/nature12373\n"
            "https://doi.org/10.1126/science.1157784\n"
            "https://www.nature.com/articles/nature12373\n"
            "doi:10.1016/j.cell.2015.07.058"
        )
        layout.addWidget(self.doi_text)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Buttons
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("Convert All DOIs")
        self.convert_btn.clicked.connect(self.start_conversion)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def start_conversion(self):
        """Start batch conversion process"""
        doi_text = self.doi_text.toPlainText().strip()
        if not doi_text:
            QMessageBox.warning(self, "Warning", "Please enter at least one DOI or URL")
            return

        # Extract DOIs from text (improved)
        lines = [line.strip() for line in doi_text.split("\n") if line.strip()]

        # Validate and extract DOIs
        validator = DOIValidator()
        valid_dois = []
        invalid_inputs = []

        for line in lines:
            try:
                # 향상된 DOI 추출
                extracted_doi = validator.extract_doi_from_input(line)
                if extracted_doi and validator.is_valid_doi_format(extracted_doi):
                    valid_dois.append(extracted_doi)
                else:
                    invalid_inputs.append(line)
            except Exception:
                invalid_inputs.append(line)

        if invalid_inputs:
            reply = QMessageBox.question(
                self,
                "Invalid Inputs",
                f"Found {len(invalid_inputs)} invalid inputs:\n"
                + "\n".join(invalid_inputs[:5])  # Show first 5
                + ("..." if len(invalid_inputs) > 5 else "")
                + f"\n\nContinue with {len(valid_dois)} valid DOIs?",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if not valid_dois:
            QMessageBox.warning(self, "Error", "No valid DOIs found")
            return

        # Start conversion
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100)
        self.convert_btn.setEnabled(False)

        self.conversion_thread = DOIConversionThread(valid_dois)
        self.conversion_thread.finished.connect(self.on_conversion_finished)
        self.conversion_thread.error.connect(self.on_conversion_error)
        self.conversion_thread.progress.connect(self.progress_bar.setValue)
        self.conversion_thread.start()

    def on_conversion_finished(self, result):
        """Handle conversion completion"""
        self.batch_completed.emit(result["papers"])
        self.accept()

    def on_conversion_error(self, error_msg):
        """Handle conversion error"""
        QMessageBox.warning(self, "Conversion Error", error_msg)


class DOIInputWidget(QWidget):
    """Widget for DOI input and conversion"""

    doi_converted = pyqtSignal(dict)  # Single DOI conversion
    batch_converted = pyqtSignal(list)  # Batch conversion

    def __init__(self):
        super().__init__()
        self.converter = DOIConverter()
        self.validator = DOIValidator()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the input widget UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # DOI input section
        input_layout = QHBoxLayout()

        # DOI input field
        self.doi_input = QLineEdit()
        self.doi_input.setPlaceholderText(
            "Enter DOI or URL (e.g., 10.1038/nature12373, https://doi.org/..., or full article URL)"
        )
        font = QFont()
        font.setPointSize(11)
        self.doi_input.setFont(font)
        input_layout.addWidget(self.doi_input)

        # Convert button
        self.convert_btn = QPushButton("🔄 Convert")
        self.convert_btn.setMinimumWidth(100)
        self.convert_btn.setToolTip(
            "Convert DOI/URL to citation (generates all formats)"
        )
        input_layout.addWidget(self.convert_btn)

        # Batch convert button
        self.batch_btn = QPushButton("📚 Batch")
        self.batch_btn.setMinimumWidth(80)
        self.batch_btn.setToolTip("Convert multiple DOIs/URLs at once")
        input_layout.addWidget(self.batch_btn)

        layout.addLayout(input_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.status_label)

    def connect_signals(self):
        """Connect widget signals"""
        self.doi_input.returnPressed.connect(self.convert_doi)
        self.convert_btn.clicked.connect(self.convert_doi)
        self.batch_btn.clicked.connect(self.show_batch_dialog)

        # Real-time validation
        self.doi_input.textChanged.connect(self.validate_input)

    def validate_input(self, text):
        """Validate input in real-time"""
        if not text:
            self.status_label.setText("")
            self.convert_btn.setEnabled(True)
            return

        try:
            # 향상된 DOI 추출 시도
            extracted_doi = self.validator.extract_doi_from_input(text)
            if extracted_doi and self.validator.is_valid_doi_format(extracted_doi):
                self.status_label.setText(f"✓ Valid DOI found: {extracted_doi}")
                self.status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
                self.convert_btn.setEnabled(True)
            else:
                self.status_label.setText("⚠ No valid DOI found in input")
                self.status_label.setStyleSheet("color: #FF9800; font-size: 10px;")
                self.convert_btn.setEnabled(False)
        except Exception:
            self.status_label.setText("⚠ Unable to process input")
            self.status_label.setStyleSheet("color: #FF9800; font-size: 10px;")
            self.convert_btn.setEnabled(False)

    def convert_doi(self):
        """Convert single DOI/URL"""
        input_text = self.doi_input.text().strip()
        if not input_text:
            return

        try:
            # 향상된 DOI 추출
            doi = self.validator.extract_doi_from_input(input_text)
            if not doi or not self.validator.is_valid_doi_format(doi):
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Please enter a valid DOI or URL containing a DOI",
                )
                return
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to process input: {str(e)}")
            return

        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Converting...")
        self.status_label.setText("Converting...")
        self.status_label.setStyleSheet("color: #2196F3; font-size: 10px;")

        try:
            # Convert DOI (모든 형식 자동 생성)
            paper_data = self.converter.convert_doi(doi)

            # Emit signal with paper data
            self.doi_converted.emit(paper_data)

            self.status_label.setText("✓ Converted successfully")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")

            # Clear input after successful conversion
            QTimer.singleShot(2000, lambda: self.doi_input.clear())

        except Exception as e:
            error_msg = str(e)
            if "Failed to retrieve metadata" in error_msg:
                error_msg = "DOI not found or not accessible. Please check the DOI."
            elif "timeout" in error_msg.lower():
                error_msg = "Connection timeout. Please check your internet connection."

            QMessageBox.critical(
                self, "Conversion Error", f"Failed to convert DOI:\n{error_msg}"
            )
            self.status_label.setText("✗ Conversion failed")
            self.status_label.setStyleSheet("color: #F44336; font-size: 10px;")

        finally:
            self.convert_btn.setEnabled(True)
            self.convert_btn.setText("🔄 Convert")

    def show_batch_dialog(self):
        """Show batch conversion dialog"""
        dialog = BatchConvertDialog(self)
        dialog.batch_completed.connect(self.batch_converted.emit)
        dialog.exec()

    def paste_and_convert(self):
        """Paste from clipboard and convert"""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()

        if text:
            try:
                # 향상된 DOI 추출 시도
                doi = self.validator.extract_doi_from_input(text)
                if doi and self.validator.is_valid_doi_format(doi):
                    self.doi_input.setText(text)
                    self.convert_doi()
                else:
                    self.status_label.setText("No valid DOI found in clipboard")
                    self.status_label.setStyleSheet("color: #FF9800; font-size: 10px;")
            except Exception:
                self.status_label.setText("Unable to process clipboard content")
                self.status_label.setStyleSheet("color: #FF9800; font-size: 10px;")
        else:
            self.status_label.setText("Clipboard is empty")
            self.status_label.setStyleSheet("color: #FF9800; font-size: 10px;")
