import sys
import os
from functools import partial

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QComboBox, QPushButton, QLineEdit,
                             QFileDialog, QMessageBox, QLabel, QCheckBox,
                             QTextEdit)
from PyQt6.QtCore import Qt, QUrl, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QIcon, QDesktopServices

from pkgs.api import OrDraft
from pkgs.placeholder_replacer import WordPlaceholderReplacer

from pkgs.enums import TemplateFile, TemplateType
from pkgs.config import DEFAULT_GUIDELINES

class ViewModel(QObject):
    processing_finished = pyqtSignal(bool)

    def __init__(self, model: OrDraft):
        super().__init__()
        
        self.model = model
        self.word_processor = WordPlaceholderReplacer()
        
        self.model.data_received.connect(self._draft_dismissal)

    def main_handler(self, url, port, pdf_path, save_path, custom_prompt=None):
        self.word_processor.save_file = save_path

        self._handle_extraction(pdf_path=pdf_path, url=url, port=port, custom_prompt=custom_prompt)

    def _handle_extraction(self, pdf_path: str, url, port, custom_prompt=None) -> dict:
        self.model.pdf_path = pdf_path
        self.model.extract_information(url, port, custom_prompt)

    @pyqtSlot(dict)
    def _draft_dismissal(self, extracted: dict) -> bool:
        try:
            if len(extracted) == 0:
                raise ValueError("No data received!")

            case_number: str = extracted.get("case_number")
            extracted["case_number_only"] = case_number[-9:]

            print(extracted)

            self.word_processor.replace_placeholders(extracted)
            self.word_processor.save(case_number)
            self.processing_finished.emit(True)
        except Exception as e:
            print(e)
            self.processing_finished.emit(False)
            return


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: ViewModel):
        super().__init__()
        self.setWindowTitle("OrDraft")
        icon_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resource/icon.ico")
        self.setWindowIcon(QIcon(icon_filepath))
        self.setGeometry(100, 100, 600, 300)  # Adjusted height for extra fields
        self.setFixedHeight(350)
        self.setFixedWidth(600)
        self.viewmodel = viewmodel

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # URL and port fields
        network_layout = QHBoxLayout()
        network_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit()
        network_layout.addWidget(self.url_edit)

        network_layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("1234")
        network_layout.addWidget(self.port_edit)

        layout.addLayout(network_layout)

        # Combo box setup
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        self.combo = QComboBox()
        self.combo.addItems([template.value for template in TemplateType])
        template_layout.addWidget(self.combo, stretch=1)
        layout.addLayout(template_layout)

        # Path selection row
        doc_layout = QHBoxLayout()
        layout.addLayout(doc_layout)
        doc_layout.addWidget(QLabel("File location:"))

        self.path_edit_file = QLineEdit()
        self.path_edit_file.setReadOnly(True)
        doc_layout.addWidget(self.path_edit_file)

        self.browse_btn_file = QPushButton("Browse")
        doc_layout.addWidget(self.browse_btn_file)

        # Save location row
        save_layout = QHBoxLayout()
        layout.addLayout(save_layout)
        save_layout.addWidget(QLabel("Save Location:"))
        default_save_path = os.path.join(os.path.expanduser("~"), "Documents", "OrDraft")
        os.makedirs(default_save_path, exist_ok=True)
        self.path_edit_save = QLineEdit()
        self.path_edit_save.setReadOnly(True)
        self.path_edit_save.setText(default_save_path)
        save_layout.addWidget(self.path_edit_save)

        self.browse_btn_save = QPushButton("...")
        save_layout.addWidget(self.browse_btn_save)

        self.open_dir = QPushButton("Open")
        save_layout.addWidget(self.open_dir)

        # Checkbox for including reply
        self.include_reply_checkbox = QCheckBox("Include Reply")
        self.include_reply_checkbox.setChecked(True)  # Default: checked
        layout.addWidget(self.include_reply_checkbox)

        self.custom_prompt = QCheckBox("Customize Prompt")
        self.custom_prompt.setChecked(False)

        layout.addWidget(self.custom_prompt)
        
        self.prompt = QTextEdit()
        self.prompt.setFixedHeight(100)
        self.prompt.setEnabled(False)
        layout.addWidget(self.prompt)

        # Save button
        self.generate = QPushButton("Generate")
        layout.addWidget(self.generate, alignment=Qt.AlignmentFlag.AlignRight, stretch=1)

        # Connect signals
        self.combo.currentTextChanged.connect(self.update_template)
        self.browse_btn_file.clicked.connect(partial(self.browse_directory, 0))
        self.browse_btn_save.clicked.connect(partial(self.browse_directory, 1))
        self.generate.clicked.connect(self.save_data)
        self.open_dir.clicked.connect(self.show_dir)
        self.custom_prompt.checkStateChanged.connect(self.handle_show_prompt)
        self.viewmodel.processing_finished.connect(self._on_process_done)

        # Initialize path
        self.update_template(self.combo.currentText())

    def update_template(self, text):
        pass

    def show_dir(self):
        # Ensure the path is absolute
        full_path = os.path.abspath(self.path_edit_save.text())
        # Convert the file path to a QUrl
        url = QUrl.fromLocalFile(full_path)
        # Open the directory using QDesktopServices
        QDesktopServices.openUrl(url)

    def handle_show_prompt(self, state: Qt.CheckState):
        # _ = self.prompt.show() if state == Qt.CheckState.Checked else self.prompt.hide()
        _ = self.prompt.setEnabled(True) if state == Qt.CheckState.Checked else self.prompt.setEnabled(False)

        if state == Qt.CheckState.Checked:
            self.prompt.setText(DEFAULT_GUIDELINES)
        else:
            self.prompt.setText("")

    def browse_directory(self, type):
        if type == 0:
            file_path, _ = QFileDialog.getOpenFileName(None, "Select a File", "", "All Files (*)")
        else:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        if type == 0:
            self.path_edit_file.setText(file_path)
        elif type == 1:
            if not (directory is None or len(directory) == 0):
                self.path_edit_save.setText(directory)

    def save_data(self):
        path = self.path_edit_save.text()
        if not path:
            QMessageBox.critical(self, "Error", "Please select a save location!")
            return

        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create directory: {str(e)}")
                return

        self.process()

    @pyqtSlot(bool)
    def _on_process_done(self, success):
        self.setEnabled(True)

        if success:
            QMessageBox.information(self, "Success", f"Generated Document saved successfully to:\n{self.path_edit_save.text()}")
        else:
            QMessageBox.information(self, "Error", "Something went wrong!")


    def process(self):
        self.setEnabled(False)
        include_reply = self.include_reply_checkbox.isChecked()
        selected_template = TemplateType(self.combo.currentText())
        
        custom_prompt = self.prompt.toPlainText() if self.custom_prompt.isChecked() else None

        try:
            template_file = TemplateFile.get_template_file(selected_template, include_reply)
            # print(f"Using template: {template_file}")
            template_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), template_file)
            self.viewmodel.word_processor.template_file = template_filepath
            self.viewmodel.main_handler(
                url=self.url_edit.text(),
                port=self.port_edit.text(),
                pdf_path=self.path_edit_file.text(),
                save_path=self.path_edit_save.text(),
                custom_prompt=custom_prompt
            )
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    window = MainWindow(ViewModel(OrDraft()))

    window.setWindowFlags(window.windowFlags())  
    window.show()
    window.raise_()  
    window.activateWindow()  

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
