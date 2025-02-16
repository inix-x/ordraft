# fmt: off
import os
import sys
import traceback
import pathlib
import re
from enum import Enum
from functools import partial
from typing import Union


from PyQt6.QtCore import (
    Qt, QObject, QDir, Qt, QUrl,
    QPropertyAnimation, pyqtSignal, QStandardPaths, QSize,
)
from PyQt6.QtWidgets import (
    QFrame, QApplication, QVBoxLayout,
    QHBoxLayout, QWidget, QSplitter,
    QListWidget, QSplitterHandle, QGraphicsOpacityEffect,
    QSizePolicy, QFileDialog, QLabel,
)
from PyQt6.QtGui import QIcon, QColor, QPainter, QPainterPath, QDesktopServices

from qfluentwidgets import (
    NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, QConfig,
    SwitchSettingCard, qconfig, StyleSheetBase, Theme, setTheme,
    setThemeColor, AvatarWidget, SingleDirectionScrollArea, PushButton, ElevatedCardWidget,
    ImageLabel, CaptionLabel, CardWidget, SettingCard, ScrollArea,
    themeColor, isDarkTheme, ListWidget, IconWidget,
    BodyLabel, TransparentToolButton, PlainTextEdit, ComboBox,
    CheckBox, MessageBox, MessageBoxBase, LineEdit,
    PushSettingCard,
)
from qfluentwidgets.common import (
    ConfigItem, BoolValidator, ColorValidator,
    FluentStyleSheet, FluentIconBase,
)
from qfluentwidgets.components.settings.setting_card import SettingIconWidget
from qfluentwidgets import FluentIcon as FIF


from pkgs.icons import MyFluentIcon as CFIF


from pkgs import MainViewModel, Data

from pkgs import (
    URL, DEFAULT_GUIDELINES, TemplateType, MainViewModel,
    GenerateDocData, Data, UpdateDocData, CustomListItem,
    Utils, Models,
)

from pkgs import SettingsViewModel, SettingsModel
# fmt: on


class StyleSheet(StyleSheetBase, Enum):
    """Style sheet"""

    WINDOW = "window"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"qss/{theme.value.lower()}/{self.value}.qss"


class Config(QConfig):
    darkTheme = ConfigItem("MainWindow", "darkTheme", True, BoolValidator())
    transparent_bg = ConfigItem(
        "MainWindow", "TransparentSubInterface", False, BoolValidator()
    )


class Container(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.hBoxlayout = QHBoxLayout(self)
        self.hBoxlayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setObjectName(text.replace(" ", "-"))


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.vBoxlayout = QVBoxLayout(self)
        self.vBoxlayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        setFont(self.label, 24)
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter
        )
        self.vBoxlayout.addWidget(
            self.label, stretch=0, alignment=Qt.AlignmentFlag.AlignTop
        )

        self.setObjectName(text.replace(" ", "-"))


class CustomPushSettingCard(PushSettingCard):

    def __init__(
        self,
        text,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        data=None,
        content=None,
        parent=None,
    ):
        """
        Parameters
        ----------
        text: str
            button text
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(
            text=text, icon=icon, title=title, content=content, parent=parent
        )
        self._data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data: str):
        if self._data != data and isinstance(data, str):
            self._data = data

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class PushButtonData(PushButton):

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setIcon(icon)
        self.setText(text)
        self._data = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data: str):
        self._data = data


class AppCard(CardWidget):

    def __init__(self, icon: QIcon, title, content, parent=None):
        super().__init__(parent)
        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.openButton = PushButton("Open", self)
        self.moreButton = TransparentToolButton(FIF.MORE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(73)
        self.iconWidget.setFixedSize(48, 48)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.openButton.setFixedWidth(120)

        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.addWidget(self.iconWidget)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.openButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addWidget(self.moreButton, 0, Qt.AlignmentFlag.AlignRight)

        self.moreButton.setFixedSize(32, 32)


class InfoMessageBox(MessageBoxBase):
    """Custom message box"""

    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(title)
        self.content = BodyLabel(content)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content)

        self.widget.setMinimumWidth(350)

        self.cancelButton.hide()
        self.buttonLayout.insertStretch(1)

        self.hide()

    def set_title(self, text):
        self.titleLabel.setText(text)

    def set_content(self, text):
        self.content.setText(text)


class LineEditMessageBox(MessageBoxBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Open URL", self)
        self.urlLineEdit = LineEdit(self)

        self.urlLineEdit.setPlaceholderText(
            "Enter the URL of a file, stream, or playlist"
        )
        self.urlLineEdit.setClearButtonEnabled(True)

        self.warningLabel = CaptionLabel("Invalid URL")
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        # add widget to view layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.urlLineEdit)
        self.viewLayout.addWidget(self.warningLabel)
        self.warningLabel.hide()

        self.widget.setMinimumWidth(350)
        self.hide()

    def validate(self):
        """Override to validate form data"""
        isValid = QUrl(self.urlLineEdit.text()).isValid()
        self.warningLabel.setHidden(isValid)
        return isValid

    def validate_url(self):
        """Override to validate form data"""
        url_text = self.urlLineEdit.text().strip()

        url_pattern = re.compile(
            r"^(https?|ftp):\/\/"
            r"("
            r"((\d{1,3}\.){3}\d{1,3})"
            r"|"
            r"([a-zA-Z0-9-]+(\.[a-zA-Z]{2,})+)"
            r")"
            r"(:\d{1,5})?"
        )

        is_valid = bool(url_pattern.match(url_text))

        self.warningLabel.setHidden(is_valid)
        return is_valid


class AIStreamCard(CardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Stream Output")

        self.setClickEnabled(False)

        self._hover = False

        self.outputWidget = PlainTextEdit(self)
        self.outputWidget.setReadOnly(True)
        self.outputWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout(self)
        layout.addWidget(self.outputWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _hoverBackgroundColor(self):
        if self._hover:
            return CardWidget()._hoverBackgroundColor()
        else:
            return CardWidget()._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        if self._hover:
            return CardWidget()._pressedBackgroundColor()
        else:
            return CardWidget()._normalBackgroundColor()

    def append_stream(self, text: str):
        """
        Append new text to the streaming output.
        This method can be called repeatedly to update the card.
        """
        self.outputWidget.append(text)


class Window(FluentWindow):
    """Main Interface"""

    def __init__(self):
        super().__init__()
        self.cfg = Config()

        # Interface
        self.dismissal_interface = Widget("Dismissal", self)
        self.settings_interface = Widget("Settings", self)

        self.view_model = MainViewModel(Data())

        self.view_model.docEvents.connect(self.generate_events)

        self.initNavigation()
        self.initWindow()
        self.settings_setup_ui()
        self.dismissal_setup_ui()
        self._load_config()
        self._components()

        size = QSize(800, 600)
        self.setMinimumSize(size)
        self.setBaseSize(size)
        self.resize(size)

    def _load_config(self):
        try:
            file_path = "config.json"
            if not os.path.exists(file_path):
                with open(file_path, "w") as file:
                    file.write("")

            qconfig.load("config.json", self.cfg)
            self._load_theme()
        except Exception:
            print(traceback.format_exc())

    def _load_theme(self):
        try:
            dark_mode = self.cfg.darkTheme.value
        except AttributeError:
            dark_mode = self.cfg.darkTheme

        setTheme(Theme.DARK if dark_mode else Theme.LIGHT)

        (
            """QLabel { color: #FF7043; }"""
            if dark_mode
            else """QLabel { color: #D32F2F; }"""
        )
        setThemeColor(QColor("#3CB969"))
        self.cfg.save()

    def initNavigation(self):
        self.addSubInterface(self.dismissal_interface, FIF.DOCUMENT, "Draft Dismissal")
        self.addSubInterface(
            self.settings_interface,
            FIF.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon("icons:app.icon.svg"))
        self.setWindowTitle("OrDraft")

    def settings_setup_ui(self):
        """asd"""
        # UI
        # UI: APP
        app_settings = SubtitleLabel("App", self)
        setFont(app_settings, 18)
        self.api_url = CustomPushSettingCard(
            text="Change",
            icon=CFIF.URL,
            title="API",
            content="DO NOT CHANGE. Unless the API url supports OpenAI-like endpoints",
            data=URL,
            parent=self,
        )

        # UI: Aesthetics
        aesthetics = SubtitleLabel("Aesthetics", self)
        setFont(aesthetics, 18)
        dark_theme = SwitchSettingCard(
            icon=CFIF.THEMEMODE,
            title="Dark Mode",
            content="Enable dark mode theme",
            configItem=self.cfg.darkTheme,
        )
        transparent = SwitchSettingCard(
            icon=FIF.TRANSPARENT,
            title="Enable Transparent View",
            content="Set the background of the views to transparent",
            configItem=self.cfg.transparent_bg,
        )

        # Initial Values
        dark_theme.switchButton.setChecked(self.cfg.darkTheme.value)
        transparent.switchButton.setChecked(self.cfg.transparent_bg.value)

        # Connections: App
        self.api_url.button.clicked.connect(self._show_change_api_url)

        # Connections: Aeshethics
        dark_theme.switchButton.checkedChanged.connect(
            lambda checked: self._change_visual(dark_theme=checked)
        )
        transparent.switchButton.checkedChanged.connect(
            lambda checked: self._change_visual(transparent=checked)
        )
        # layout: App settings
        self.settings_interface.vBoxlayout.addWidget(
            app_settings, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            self.api_url, alignment=Qt.AlignmentFlag.AlignTop
        )
        # layout: Aesthetics
        self.settings_interface.vBoxlayout.addWidget(
            aesthetics, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            dark_theme, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            transparent, alignment=Qt.AlignmentFlag.AlignTop
        )

    def _change_visual(self, *args, **kwargs):
        dark_theme = kwargs.get("dark_theme", None)
        transparent = kwargs.get("transparent", None)

        if dark_theme is not None:
            setTheme(Theme.DARK if dark_theme else Theme.LIGHT)
            self.cfg.darkTheme = dark_theme

            style = (
                """QLabel { color: #FF7043; }"""
                if dark_theme
                else """QLabel { color: #D32F2F; }"""
            )
            self.api_url.contentLabel.setStyleSheet(style)

        if transparent is not None:
            self.toggleStackedBackground(transparent)
            self._updateStackedBackground()
            self.cfg.transparent_bg = transparent

        self.cfg.save()

    def _show_change_api_url(self):
        self.line_edit_message_box.titleLabel.setText("Change API URL")
        self.line_edit_message_box.urlLineEdit.setPlaceholderText("New API URL")
        test = self.line_edit_message_box.exec()

        if test == 1:
            self._handle_change_api_url()

    def _handle_change_api_url(self):
        if self.line_edit_message_box.validate_url():
            self.api_url.data = self.line_edit_message_box.urlLineEdit.text()
            self.line_edit_message_box.close()
            self.line_edit_message_box.warningLabel.hide()
        else:
            self.line_edit_message_box.urlLineEdit.setText("")
            self.line_edit_message_box.warningLabel.show()
            self._show_change_api_url()

    def toggleStackedBackground(self, state: bool):
        """Toggle the background transparency of the stacked widget"""
        current_widget = self.stackedWidget.currentWidget()
        if not current_widget:
            return

        self.stackedWidget.setProperty("isTransparent", state)
        self._updateStackedBackground()

    def _updateStackedBackground(self):
        self.stackedWidget.setStyle(QApplication.style())

    def _components(self):
        self.message_box = InfoMessageBox("Popup", "", self)

        self.line_edit_message_box = LineEditMessageBox(self)

    def dismissal_setup_ui(self):
        self.streamCard = AIStreamCard()
        self.streamCard.setFixedWidth(725)
        self.streamCard.setMinimumWidth(725)
        self.streamCard.setFixedHeight(350)

        self.streamCard.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )

        controls = Container("File Controls", self)
        template_control = Container("Template Controls", self)
        controls.setFixedWidth(725)
        controls.setContentsMargins(0, 5, 0, 0)
        template_control.setFixedWidth(725)
        template_control.setContentsMargins(0, 20, 0, 0)

        self.file_button = PushButtonData(FIF.ADD_TO, "Add new file")
        self.file_button.setFixedWidth(400)

        self.save_location_btn = PushButtonData(FIF.FOLDER_ADD, "Save location")
        self.open_save_location_btn = PushButton(FIF.FOLDER, "Open Generated Documents")

        self.generate_btn = PushButtonData(QIcon("icons:bot.icon.svg"), "Generate")
        self.generate_btn.setFixedWidth(120)

        # Template
        self.template_combobox = ComboBox()
        self.template_combobox.setFixedWidth(175)
        self.template_combobox.addItems([template.value for template in TemplateType])
        self.template_combobox.setPlaceholderText("Choose template")
        self.template_combobox.setCurrentIndex(-1)

        self.include_reply = CheckBox("Include Reply")

        # Connections
        self.file_button.clicked.connect(partial(self._browse, 0))
        self.save_location_btn.clicked.connect(partial(self._browse, 1))
        self.open_save_location_btn.clicked.connect(self._open_save_location)
        self.generate_btn.clicked.connect(self.generate)

        # File Control layout
        controls.hBoxlayout.addWidget(
            self.save_location_btn, Qt.AlignmentFlag.AlignLeft
        )
        controls.hBoxlayout.addWidget(
            self.open_save_location_btn, Qt.AlignmentFlag.AlignLeft
        )
        controls.hBoxlayout.addWidget(self.generate_btn, Qt.AlignmentFlag.AlignLeft)

        # Template Control Layout
        template_control.hBoxlayout.addWidget(
            self.file_button, Qt.AlignmentFlag.AlignLeft
        )
        template_control.hBoxlayout.addWidget(
            self.template_combobox, Qt.AlignmentFlag.AlignLeft
        )
        template_control.hBoxlayout.addWidget(
            self.include_reply, Qt.AlignmentFlag.AlignLeft
        )

        # Dismissal Layout
        self.dismissal_interface.vBoxlayout.addWidget(
            self.streamCard,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        self.dismissal_interface.vBoxlayout.addWidget(
            template_control,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        self.dismissal_interface.vBoxlayout.addWidget(
            controls,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        # controls.hBoxlayout.addWidget()

    def _browse(self, type: int):
        try:
            if type == 0:
                download_dir = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DownloadLocation
                )
                file_path, _ = QFileDialog.getOpenFileName(
                    None, "Select a File", download_dir, "*.pdf"
                )

                filename = os.path.splitext(os.path.basename(file_path))[0]
                if not len(filename) == 0:
                    self.file_button.data = file_path
                    text = self.view_model._truncate_string(filename, 40)
                    self.file_button.setText(text)
                else:
                    self.file_button.setText("Add file")

            else:
                directory = QFileDialog.getExistingDirectory(self, "Select Directory")
                if not (directory is None or len(directory) == 0):
                    self.save_location_btn.data = directory
                    text = self.view_model._truncate_string(directory, 24)
                    self.save_location_btn.setText(text)

        except Exception:
            print(traceback.format_exc())

    def _open_save_location(self):
        try:
            absolute_path = os.path.relpath(self.save_location_btn.data)

            if absolute_path is None:
                raise ValueError("Add Save Location first")

            if not os.path.isdir(absolute_path):
                raise FileNotFoundError(
                    f"The directory '{absolute_path}' is not valid."
                )

            url = QUrl.fromLocalFile(absolute_path)

            if not QDesktopServices.openUrl(url):
                raise RuntimeError(f"Failed to open the folder: {absolute_path}")

        except Exception as e:
            self.show_message_box("Error", str(e))
            # print(traceback.format_exc())

    def show_message_box(self, title, content):
        self.message_box.set_title(title)
        self.message_box.set_content(content)

        if self.message_box.exec():
            pass

    def generate(self):
        self.generate_btn.setEnabled(False)
        self.streamCard.outputWidget.setPlainText("")
        try:
            data = GenerateDocData(
                url=self.api_url.data,
                pdf_path=self.file_button.data,
                save_path=self.save_location_btn.text(),
                is_reply_included=self.include_reply.isChecked(),
                selected_template=TemplateType(self.template_combobox.currentText()),
                is_custom_prompt=False,
                custom_prompt="",
            )
            self.view_model.main_handler(data)
        except Exception as e:
            print(traceback.format_exc())
            self.show_message_box("Error", f"{e}")

    def generate_events(self, doc: UpdateDocData, id: str):
        if doc.status == "Done":
            self.generate_btn.setEnabled(True)
            
        if doc.error:
            self.generate_btn.setEnabled(True)
            self.show_message_box("Error", str(doc.error))
    

def register_search_path(relative_path=None):
    relative_path = (
        str(pathlib.Path(__file__).parent.resolve())
        if relative_path is None
        else relative_path
    )
    QDir.addSearchPath("resource", os.path.join(relative_path, "resource"))
    QDir.addSearchPath("icons", os.path.join(relative_path, "resource", "icons"))


if __name__ == "__main__":
    register_search_path()

    app = QApplication(sys.argv)
    window = Window()
    # title_bar = FluentTitleBar(window)
    # title_bar.setTitle("OrDraft")
    # title_bar.setIcon("icons:app.icon.svg")
    # window.setTitleBar(titleBar=title_bar)
    window.show()
    sys.exit(app.exec())
