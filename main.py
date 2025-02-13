import sys
import pathlib
import os
import traceback
from typing import Any
from functools import partial

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QComboBox, QPushButton, QLineEdit,
                             QFileDialog, QMessageBox, QLabel, QCheckBox,
                             QTextEdit, QListWidget, QListWidgetItem, QMenu)
from PyQt6.QtCore import Qt, QUrl, pyqtSlot, QStandardPaths, QDir
from PyQt6.QtGui import QIcon, QDesktopServices, QAction

from pkgs import (
    DEFAULT_GUIDELINES, 
    TemplateType, 
    MainViewModel, 
    GenerateDocData,
    Data,
    UpdateDocData,
    CustomListItem,
    Utils,
    Models
)

from pkgs import SettingsViewModel, SettingsModel


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: MainViewModel):
        super().__init__()
        self.setWindowTitle("OrDraft")
        icon_filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resource/icon.ico"
        )
        self.setWindowIcon(QIcon(icon_filepath))
        self.setGeometry(100, 100, 600, 500)
        self.setFixedHeight(500)
        self.setFixedWidth(600)

        # ViewModels
        self.viewmodel = viewmodel
        self.settings_vm = SettingsViewModel(SettingsModel())

        self._utils = Utils()

        self.setup_menu()
        self._setup_ui()
        self._setup_connections()
        self._load_settings()

    def _load_settings(self):
        try:
            # Window Properties
            settings = self.settings_vm.settings
            self.resize(settings.windowGeometry.size)
            self.move(settings.windowGeometry.pos)
            # Fields
            self.url_edit.setText(settings.api_url)
        except Exception:
            print(traceback.format_exc())

    def _setup_ui(self):

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # List widget
        layout.addWidget(QLabel("Tasks"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setHorizontalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self.list_widget)

        network_layout = QHBoxLayout()
        network_layout.addWidget(QLabel("URL:"))
        self.url_edit = QLineEdit()
        network_layout.addWidget(self.url_edit)

        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Assistant:"))
        self.assisant = QComboBox()
        self.assisant.addItems([template.value for template in Models])
        model_layout.addWidget(self.assisant, stretch=1)

        # network_layout.addWidget(QLabel("Port:"))
        # self.port_edit = QLineEdit()
        # self.port_edit.setPlaceholderText("1234")
        # network_layout.addWidget(self.port_edit)

        layout.addLayout(network_layout)
        layout.addLayout(model_layout)

        # Combo box setup
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        self.combo = QComboBox()
        self.combo.addItems([template.value for template in TemplateType])
        template_layout.addWidget(self.combo, stretch=1)

        # Checkbox for including reply
        self.include_reply_checkbox = QCheckBox("with Reply")
        self.include_reply_checkbox.setChecked(True)  # Default: checked
        template_layout.addWidget(self.include_reply_checkbox)
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
        default_save_path = os.path.join(
            os.path.expanduser("~"), "Documents", "OrDraft"
        )
        os.makedirs(default_save_path, exist_ok=True)
        self.path_edit_save = QLineEdit()
        self.path_edit_save.setReadOnly(True)
        self.path_edit_save.setText(default_save_path)
        save_layout.addWidget(self.path_edit_save)

        self.browse_btn_save = QPushButton("...")
        save_layout.addWidget(self.browse_btn_save)

        self.open_dir = QPushButton("Open")
        save_layout.addWidget(self.open_dir)

        self.custom_prompt = QCheckBox("Customize Prompt")
        self.custom_prompt.setChecked(False)

        layout.addWidget(self.custom_prompt)

        self.prompt = QTextEdit()
        self.prompt.setFixedHeight(100)
        self.prompt.setEnabled(False)
        layout.addWidget(self.prompt)

        # Save button
        self.generate = QPushButton("Generate")
        layout.addWidget(
            self.generate, alignment=Qt.AlignmentFlag.AlignRight, stretch=1
        )

        # Initialize path
        self.update_template(self.combo.currentText())

    def _setup_connections(self):
        # Connect signals
        self.combo.currentTextChanged.connect(self.update_template)
        self.browse_btn_file.clicked.connect(partial(self.browse_directory, 0))
        self.browse_btn_save.clicked.connect(partial(self.browse_directory, 1))
        self.generate.clicked.connect(self.save_data)
        self.open_dir.clicked.connect(self.show_dir)
        self.custom_prompt.checkStateChanged.connect(self.handle_show_prompt)

        self.viewmodel.docEvents.connect(self._update_doc_status_list)
        self.viewmodel.docOpened.connect(self._doc_opened)

    def setup_menu(self):
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("border-bottom: 1px solid #30834C")

        # ------------------------------------------
        # App Menu
        app_menu = menu_bar.addMenu("App")
        app_menu.menuAction().setIconVisibleInMenu(False)

        # App Menu: Add Menu
        add_sub_menu = QMenu("Add", self)
        add_sub_menu.setEnabled(False)
        add_sub_menu.menuAction().setIconVisibleInMenu(False)

        # App Menu: Add Menu: New template
        new_template_act = QAction("New Template", self)
        # new_template_act.triggered.connect(self.show_template_window)
        new_template_act.setEnabled(False)
        add_sub_menu.addAction(new_template_act)

        # App Menu: Settings
        settings_act = QAction("Settings", self)
        settings_act.setEnabled(False)
        # settings_act.triggered.connect(self.show_settings_window)

        # App Menu: exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        app_menu.addMenu(add_sub_menu)
        app_menu.addAction(settings_act)
        app_menu.addAction(exit_action)

        # ------------------------------------------
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        change_template_dir_action = QAction("Show Template folder", self)
        change_template_dir_action.triggered.connect(self.show_template_dir)
        help_menu.addAction(change_template_dir_action)

    def show_template_dir(self):
        QMessageBox.information(
            self,
            "Reminder",
            """
        1. Maintain the original filenames of the templates; do not rename them.
        2. Do not delete the template files.
        3. You may modify the templates, but {{placeholders}} must remain intact.
        """,
        )
        app_data_path = os.path.join(os.environ.get("APPDATA"), "OrDraft", "Templates")
        try:
            url = QUrl.fromLocalFile(app_data_path)
        except Exception as e:
            print(e)
            os.makedirs(app_data_path, exist_ok=True)
        finally:
            QDesktopServices.openUrl(url)

    def update_template(self, text):
        pass

    def show_dir(self):
        try:
            # Ensure the path is absolute
            full_path = os.path.abspath(self.path_edit_save.text())
            # Convert the file path to a QUrl
            url = QUrl.fromLocalFile(full_path)
            # Open the directory using QDesktopServices
            QDesktopServices.openUrl(url)
        except Exception:
            print(traceback.format_exc())

    def handle_show_prompt(self, state: Qt.CheckState):
        # _ = self.prompt.show() if state == Qt.CheckState.Checked else self.prompt.hide()
        _ = (
            self.prompt.setEnabled(True)
            if state == Qt.CheckState.Checked
            else self.prompt.setEnabled(False)
        )

        if state == Qt.CheckState.Checked:
            self.prompt.setText(DEFAULT_GUIDELINES)
        else:
            self.prompt.setText("")

    def browse_directory(self, type):
        try:
            if type == 0:
                download_dir = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DownloadLocation
                )
                file_path, _ = QFileDialog.getOpenFileName(
                    None, "Select a File", download_dir, "*.pdf"
                )
            else:
                directory = QFileDialog.getExistingDirectory(self, "Select Directory")

            if type == 0:
                self.path_edit_file.setText(file_path)
            elif type == 1:
                if not (directory is None or len(directory) == 0):
                    self.path_edit_save.setText(directory)
        except Exception:
            print(traceback.format_exc())

    def save_data(self):
        path = self.path_edit_save.text()
        if not path:
            QMessageBox.critical(self, "Error", "Please select a save location!")
            return

        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Could not create directory: {str(e)}"
                )
                return

        self.process()

    @pyqtSlot()
    def process(self):
        self.setEnabled(False)
        try:
            data = GenerateDocData(
                url=self.url_edit.text(),
                # port=self.port_edit.text(),
                pdf_path=self.path_edit_file.text(),
                save_path=self.path_edit_save.text(),
                is_reply_included=self.include_reply_checkbox.isChecked(),
                selected_template=TemplateType(self.combo.currentText()),
                is_custom_prompt=self.custom_prompt.isChecked(),
                custom_prompt=self.prompt.toPlainText(),
                model=self.assisant.currentText()
            )
            success, e = self.viewmodel.main_handler(data)
            if not success:
                raise RuntimeError(f"Error occured: {e}")
        except Exception as e:
            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.setEnabled(True)

    @pyqtSlot(UpdateDocData, str)
    def _update_doc_status_list(self, doc_status: UpdateDocData, id: str):
        widget: CustomListItem = self.viewmodel.get_widget(id)
        try:
            doc_status.validate()
            if widget is not None:
                status, name = self.viewmodel._format_doc_status_name(
                    id=id,
                    status=doc_status.status,
                )
                widget.set_status_color("Normal")
                if doc_status.status == "Done":
                    widget.button.setEnabled(True)

                widget.status.setText(status)
                widget.name.setText(name)

                if doc_status.error:
                    QMessageBox.critical(self, "Error", str(doc_status.error))
                    widget.set_status_color("Error")
                    raise RuntimeError(f"{doc_status.error}")
            else:
                self._add_doc_status_list(doc_status=doc_status, id=id)
        except Exception:
            widget.status.setText("[Error]:")
            widget.set_status_color("Error")
            widget.button.setEnabled(False)
            err = doc_status.error if doc_status.error is not None else traceback.format_exc()
            QMessageBox.critical(self, "Error", str(err))

    def _add_doc_status_list(self, doc_status: UpdateDocData, id: str):
        try:
            doc_status.validate()
            item = QListWidgetItem()

            status, name = self.viewmodel._format_doc_status_name(
                id=id,
                status=doc_status.status,
            )

            custom_widget = CustomListItem(status=status, name=name, id=id)
            custom_widget.set_status_color("Waiting")
            custom_widget.button.setEnabled(False)
            custom_widget.button.setIcon(QIcon("icons:open-file.svg"))
            custom_widget.button.clicked.connect(
                lambda checked, id=id: self.viewmodel.open_document(id)
            )
            item.setSizeHint(custom_widget.sizeHint())
            self.list_widget.insertItem(0, item)
            self.list_widget.setItemWidget(item, custom_widget)

            self.viewmodel.doc_ui_map[custom_widget.id] = (item, custom_widget)
        except Exception:
            print(traceback.format_exc())

    @pyqtSlot(str, Any)
    def _doc_opened(self, id, err):
        try:
            widget: CustomListItem = self.viewmodel.get_widget(id)
            if isinstance(err, Exception):
                widget.set_status_color("Error")
                widget.status.setText("[File Missing]:")
                widget.button.setEnabled(False)
                QMessageBox.critical(self, "Error", str(err))
        except Exception as e:
            print(f"{e}: {traceback.format_exc()}")

    # ----built-in-----
    def closeEvent(self, a0):
        try:
            self.settings_vm.save_window_geometry(self.size(), self.pos())
            self.settings_vm.save_settings()
            a0.accept()
        except Exception:
            print(traceback.format_exc())
        finally:
            return super().closeEvent(a0)


def register_search_path(relative_path=None):
    relative_path = (
        str(pathlib.Path(__file__).parent.resolve())
        if relative_path is None
        else relative_path
    )
    QDir.addSearchPath("resource", os.path.join(relative_path, "resource"))
    QDir.addSearchPath("icons", os.path.join(relative_path, "resource", "icons"))


def main():
    app = QApplication(sys.argv)
    register_search_path()

    window = MainWindow(MainViewModel(Data()))

    window.setWindowFlags(window.windowFlags())
    window.show()
    window.raise_()
    window.activateWindow()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
