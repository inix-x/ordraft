import sys
import os
from functools import partial

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QComboBox, QPushButton, QLineEdit,
                             QFileDialog, QMessageBox, QLabel, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from pkgs.api import OrDraft
from pkgs.placeholder_replacer import WordPlaceholderReplacer

from pkgs.enums import TemplateFile, TemplateType

class ViewModel:

    def __init__(self, model: OrDraft):
        self.model = model
        self.word_processor = WordPlaceholderReplacer()

    def main_handler(self, url, port, pdf_path, save_path):
        self.word_processor.save_file = save_path

        extracted = self._handle_extraction(pdf_path=pdf_path, url=url, port=port)

        self._draft_dismissal(extracted=extracted)

    def _handle_extraction(self, pdf_path: str, url, port) -> dict:
        self.model.pdf_path = pdf_path
        return self.model.extract_information(url, port)

    def _draft_dismissal(self, extracted: dict) -> bool:
        try:
            case_number: str = extracted.get("case_number")
            extracted["case_number_only"] = case_number[-9:]

            print(extracted)

            self.word_processor.replace_placeholders(extracted)
            self.word_processor.save(case_number)
        except Exception as e:
            print(e)
            return


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: ViewModel):
        super().__init__()
        self.setWindowTitle("OrDraft")
        icon_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resource/icon.ico")
        self.setWindowIcon(QIcon(icon_filepath))
        self.setGeometry(100, 100, 600, 300)  # Adjusted height for extra fields
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
        path_layout = QHBoxLayout()
        layout.addLayout(path_layout)
        path_layout.addWidget(QLabel("File location:"))

        self.path_edit_file = QLineEdit()
        self.path_edit_file.setReadOnly(True)
        path_layout.addWidget(self.path_edit_file)

        self.browse_btn_file = QPushButton("Browse")
        path_layout.addWidget(self.browse_btn_file)

        # Save location row
        path_layout.addWidget(QLabel("Save Location:"))
        default_save_path = os.path.join(os.path.expanduser("~"), "Documents", "OrDraft")
        os.makedirs(default_save_path, exist_ok=True)
        self.path_edit_save = QLineEdit()
        self.path_edit_save.setReadOnly(True)
        self.path_edit_save.setText(default_save_path)
        path_layout.addWidget(self.path_edit_save)

        self.browse_btn_save = QPushButton("Browse")
        path_layout.addWidget(self.browse_btn_save)

        # Checkbox for including reply
        self.include_reply_checkbox = QCheckBox("Include Reply")
        self.include_reply_checkbox.setChecked(True)  # Default: checked
        layout.addWidget(self.include_reply_checkbox)

        # Save button
        self.save_btn = QPushButton("Save")
        layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignHCenter, stretch=2)

        # Connect signals
        self.combo.currentTextChanged.connect(self.update_template)
        self.browse_btn_file.clicked.connect(partial(self.browse_directory, 0))
        self.browse_btn_save.clicked.connect(partial(self.browse_directory, 1))
        self.save_btn.clicked.connect(self.save_data)

        # Initialize path
        self.update_template(self.combo.currentText())

    def update_template(self, text):
        pass

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
        QMessageBox.information(self, "Success", f"Data saved successfully to:\n{path}")

    def process(self):
        include_reply = self.include_reply_checkbox.isChecked()
        selected_template = TemplateType(self.combo.currentText())

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
            )
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    window = MainWindow(ViewModel(OrDraft()))

    window.setWindowFlags(window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)  
    window.show()
    window.raise_()  
    window.activateWindow()  

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
