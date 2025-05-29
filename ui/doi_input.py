"""
DOI Input Widget for DOI Citation Manager
- Format 선택 제거 (모든 형식을 자동으로 생성)
- 더 유연한 DOI 입력 처리
- 로딩 UI
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
    QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QMovie

from core.doi_converter import DOIConverter
from utils.doi_validator import DOIValidator


class LoadingWidget(QFrame):
    """로딩 애니메이션을 위한 커스텀 위젯"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """로딩 UI 설정"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame { background-color: #f0f8ff; border: 1px solid #2196F3; "
            "border-radius: 4px; padding: 4px; }"
        )
        self.setMaximumHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # 로딩 아이콘 (회전하는 이모지)
        self.loading_icon = QLabel("🔄")
        self.loading_icon.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.loading_icon)

        # 로딩 텍스트
        self.loading_text = QLabel("Converting DOI...")
        self.loading_text.setStyleSheet(
            "font-size: 11px; color: #1976D2; font-weight: bold;"
        )
        layout.addWidget(self.loading_text)

        layout.addStretch()

        # 숨김 상태로 시작
        self.hide()

    def setup_animation(self):
        """회전 애니메이션 설정"""
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_icon)
        self.rotation_angle = 0

    def rotate_icon(self):
        """아이콘 회전"""
        icons = ["🔄", "🔃", "⟳", "⟲"]
        self.rotation_angle = (self.rotation_angle + 1) % len(icons)
        self.loading_icon.setText(icons[self.rotation_angle])

    def start_loading(self, message="Converting DOI..."):
        """로딩 시작"""
        self.loading_text.setText(message)
        self.show()
        self.rotation_timer.start(200)  # 200ms마다 회전

    def stop_loading(self):
        """로딩 중지"""
        self.rotation_timer.stop()
        self.hide()


class DOIConversionThread(QThread):
    """Thread for DOI conversion to avoid blocking UI"""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)  # 상태 업데이트용

    def __init__(self, doi_list):
        super().__init__()
        self.doi_list = doi_list
        self.converter = DOIConverter()

    def run(self):
        results = []
        total = len(self.doi_list)

        for i, doi in enumerate(self.doi_list):
            try:
                self.status_update.emit(f"Converting {i+1}/{total}: {doi[:30]}...")

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
        self.resize(600, 450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Enter multiple DOIs or URLs (one per line):\n"
            "Supported formats: DOI, full URLs, partial URLs"
        )
        instructions.setStyleSheet("font-size: 11px; margin-bottom: 8px;")
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

        # Progress section
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(progress_frame)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 10px; color: #666;")
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #ccc; border-radius: 4px; text-align: center; }"
            "QProgressBar::chunk { background-color: #2196F3; border-radius: 3px; }"
        )
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(progress_frame)
        self.progress_frame = progress_frame

        # Buttons
        button_layout = QHBoxLayout()

        self.convert_btn = QPushButton("🔄 Convert All DOIs")
        self.convert_btn.setStyleSheet(
            "QPushButton { font-size: 11px; padding: 8px 16px; }"
        )
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
        self.progress_frame.setVisible(True)
        self.progress_bar.setMaximum(100)
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Converting...")

        self.conversion_thread = DOIConversionThread(valid_dois)
        self.conversion_thread.finished.connect(self.on_conversion_finished)
        self.conversion_thread.error.connect(self.on_conversion_error)
        self.conversion_thread.progress.connect(self.progress_bar.setValue)
        self.conversion_thread.status_update.connect(self.status_label.setText)
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
        self.conversion_thread = None
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
        self.convert_btn.setStyleSheet(
            "QPushButton { font-size: 11px; padding: 6px 12px; }"
        )
        input_layout.addWidget(self.convert_btn)

        # Batch convert button
        self.batch_btn = QPushButton("📚 Batch")
        self.batch_btn.setMinimumWidth(80)
        self.batch_btn.setToolTip("Convert multiple DOIs/URLs at once")
        self.batch_btn.setStyleSheet(
            "QPushButton { font-size: 11px; padding: 6px 12px; }"
        )
        input_layout.addWidget(self.batch_btn)

        layout.addLayout(input_layout)

        # Status section
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(4)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        status_layout.addWidget(self.status_label)

        # Loading widget
        self.loading_widget = LoadingWidget()
        status_layout.addWidget(self.loading_widget)

        layout.addWidget(status_frame)

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

        # UI 상태 변경
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Converting...")
        self.batch_btn.setEnabled(False)
        self.doi_input.setEnabled(False)

        # 로딩 시작
        self.loading_widget.start_loading("Fetching paper metadata...")
        self.status_label.setText("🔍 Connecting to DOI service...")
        self.status_label.setStyleSheet("color: #2196F3; font-size: 10px;")

        # 백그라운드 스레드에서 변환 수행
        self.conversion_thread = SingleDOIConversionThread(doi)
        self.conversion_thread.finished.connect(self.on_single_conversion_finished)
        self.conversion_thread.error.connect(self.on_single_conversion_error)
        self.conversion_thread.status_update.connect(self.on_conversion_status_update)
        self.conversion_thread.start()

    def on_conversion_status_update(self, message):
        """Handle status updates during conversion"""
        self.loading_widget.loading_text.setText(message)

    def on_single_conversion_finished(self, paper_data):
        """Handle successful DOI conversion"""
        # UI 상태 복원
        self.reset_ui_state()

        # 성공 메시지
        self.status_label.setText("✓ Converted successfully")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")

        # Emit signal with paper data
        self.doi_converted.emit(paper_data)

        # Clear input after successful conversion
        QTimer.singleShot(2000, lambda: self.doi_input.clear())

    def on_single_conversion_error(self, error_msg):
        """Handle DOI conversion error"""
        # UI 상태 복원
        self.reset_ui_state()

        # 에러 메시지 개선
        if "Failed to retrieve metadata" in error_msg:
            error_msg = "DOI not found or not accessible. Please check the DOI."
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout. Please check your internet connection."
        elif "invalid doi format" in error_msg.lower():
            error_msg = "Invalid DOI format. Please check and try again."

        QMessageBox.critical(
            self, "Conversion Error", f"Failed to convert DOI:\n{error_msg}"
        )

        self.status_label.setText("✗ Conversion failed")
        self.status_label.setStyleSheet("color: #F44336; font-size: 10px;")

    def reset_ui_state(self):
        """Reset UI to normal state"""
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("🔄 Convert")
        self.batch_btn.setEnabled(True)
        self.doi_input.setEnabled(True)
        self.loading_widget.stop_loading()

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


class SingleDOIConversionThread(QThread):
    """Thread for single DOI conversion"""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, doi):
        super().__init__()
        self.doi = doi
        self.converter = DOIConverter()

    def run(self):
        try:
            self.status_update.emit("Fetching metadata...")

            # Convert DOI (모든 형식 자동 생성)
            paper_data = self.converter.convert_doi(self.doi)

            self.status_update.emit("Generating citations...")

            # 짧은 지연으로 사용자가 진행상황을 볼 수 있게 함
            self.msleep(500)

            self.finished.emit(paper_data)

        except Exception as e:
            self.error.emit(str(e))
