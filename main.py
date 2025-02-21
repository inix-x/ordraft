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
    Qt, QDir, QUrl, QStandardPaths, QSize, pyqtSlot, pyqtSignal
)
from PyQt6.QtWidgets import (
    QFrame, QApplication, QVBoxLayout, QHBoxLayout, 
    QSizePolicy, QFileDialog, QSpacerItem, QSplitter,
    QWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon, QColor, QPainter, QDesktopServices

from qfluentwidgets import (
    NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, QConfig,
    SwitchSettingCard, qconfig, StyleSheetBase, Theme, setTheme,
    setThemeColor, PushButton,CaptionLabel, CardWidget,
    isDarkTheme, IconWidget, BodyLabel, TransparentToolButton, 
    PlainTextEdit, ComboBox, ListWidget, ListItemDelegate,
    CheckBox, MessageBoxBase, LineEdit,
    PushSettingCard,
)
from qfluentwidgets.common import (
    ConfigItem, BoolValidator, FluentIconBase
)
from qfluentwidgets import FluentIcon as FIF


from pkgs.icons import MyFluentIcon as CFIF


from pkgs import (
    URL, TemplateType, MainViewModel, CustomListItem,
    GenerateDocData, Data, UpdateDocData, InfoBars, create_layout,
    QueueItem
)

from pkgs import StateLLM
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
    save_location = ConfigItem(
        "App", "SaveLocation", ""
    )


class Container(QFrame):

    def __init__(self, text: str, orientation: str = "vertical", parent=None):
        super().__init__(parent=parent)
        self._layout = create_layout(orientation, self)
        self.setLayout(self._layout)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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


class SplitContainerWidget(QFrame):

    leftWidgetAtMinimum = pyqtSignal(bool)

    def __init__(
        self,
        object_name: str,
        text: str = None,
        left_w: ListWidget = None,
        right_w: Union[QWidget, Widget, Container] = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        if left_w is None and not isinstance(left_w, ListWidget):
            raise ValueError("left_w expects a ListWidget")
        if right_w is None:
            raise ValueError("right_w expects a widget")

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)

        self.left_w: ListWidget = left_w
        self.left_w.setUniformItemSizes(True)
        self.left_w.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_w.setMinimumWidth(53)
        self.left_w.setMaximumWidth(175)

        self.right_w: Union[QWidget, Widget, Container] = right_w

        self.splitter.addWidget(self.left_w)
        self.splitter.addWidget(self.right_w)

        self.splitter.setSizes([150, 450])

        layout = QVBoxLayout(self)

        if text is not None:
            self.label = SubtitleLabel(text, self)
            self.label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter
            )
            setFont(self.label, 24)
            layout.addWidget(self.label, 0, Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.splitter, 2)

        self.setObjectName(object_name.replace(" ", "-"))

        self.splitter.splitterMoved.connect(self.check_left_widget_width)

    def check_left_widget_width(self, pos: int, index: int):
        if self.left_w.width() <= self.left_w.minimumWidth() + 32: 
            self.leftWidgetAtMinimum.emit(True)
        else:
            self.leftWidgetAtMinimum.emit(False)

    def setSplitterTheme(self, dark_theme: bool):

        if dark_theme:
            handle_color = "#333333"
        else:
            handle_color = "#CCCCCC"

        splitter_style = f"""
            QSplitter {{
                background-color: none;
            }}
            QSplitter::handle {{
                background-color: {handle_color};
            }}
        """
        self.splitter.setStyleSheet(splitter_style)


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

        self.chatbox = PlainTextEdit(self)
        self.chatbox.setReadOnly(True)
        self.chatbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QVBoxLayout(self)
        layout.addWidget(self.chatbox)
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
        self.chatbox.append(text)


class Window(FluentWindow):
    """Main Interface"""

    def __init__(self):
        super().__init__()
        self.cfg = Config()

        # Interface
        self.dismissal_interface = Widget("Draft", self)
        self.settings_interface = Widget("Settings", self)
        self.prototype_interface = SplitContainerWidget(
            object_name="Draft View",
            left_w=ListWidget(self),
            right_w=Widget("Draft Assistant", self),  # text in widget serve also as
            parent=self,
        )

        self.selflist_prototype_interface = ListWidget(self)

        # Dependencies
        self.view_model = MainViewModel(Data())

        # Dependencies Connections
        self.view_model.docEvents.connect(self.generate_events)
        self.view_model.chatbox_update.connect(self.update_chatbox)
        self.view_model.llm_stream_finished.connect(self._finished)
        self.view_model.stream_stopped_sucess.connect(self._stream_stopped_success)
        self.view_model.errorOccured.connect(self._handle_error)

        self.initNavigation()
        self.initWindow()
        self.settings_setup_ui()
        self.dismissal_setup_ui()
        self.draft_setup_ui()
        self._load_config()
        self._components()

        size = QSize(1150, 600) # 800, 600
        self.setMinimumSize(size)
        self.setBaseSize(size)
        self.resize(size)

        self.connections()

    def _load_config(self):
        try:
            file_path = "config.json"
            # config_path = os.path.join(os.environ.get("APPDATA"), "OrDraft", file_path)
            if not os.path.exists(file_path):
                with open(file_path, "w") as file:
                    file.write("")

            qconfig.load(file_path, self.cfg)
            self._load_theme()
            self._load_app_settings()
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

    def _load_app_settings(self):
        save_loc = self.cfg.save_location.value

        if not len(save_loc) == 0:
            self._save_location(save_loc)

    def initNavigation(self):
        self.addSubInterface(self.dismissal_interface, FIF.DOCUMENT, "Draft Dismissal")
        self.addSubInterface(self.prototype_interface, FIF.LABEL, "Draft Assistant")
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
        # UI
        # UI: APP
        app_settings = SubtitleLabel("App", self)
        setFont(app_settings, 18)

        self.template_dir = CustomPushSettingCard(
            text="Show",
            icon=FIF.FOLDER,
            title="Template Location",
            content="You may edit here the existing templates.",
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
        self.api_url = CustomPushSettingCard(
            text="Change",
            icon=CFIF.URL,
            title="API",
            content="DO NOT CHANGE. Unless the API url supports OpenAI-like endpoints",
            data=URL,
            parent=self,
        )

        # UI: Development
        development = SubtitleLabel("Development", self)
        setFont(development, 18)

        # Initial Values
        dark_theme.switchButton.setChecked(self.cfg.darkTheme.value)
        transparent.switchButton.setChecked(self.cfg.transparent_bg.value)

        # Connections: App
        self.api_url.button.clicked.connect(self._show_change_api_url)
        self.template_dir.button.clicked.connect(self.show_template_dir)

        # Connections: Aeshethics
        dark_theme.switchButton.checkedChanged.connect(
            lambda checked: self._change_visual(dark_theme=checked)
        )
        transparent.switchButton.checkedChanged.connect(
            lambda checked: self._change_visual(transparent=checked)
        )

        # layout: App settings
        spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )

        self.settings_interface.vBoxlayout.addWidget(
            app_settings, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            self.template_dir, alignment=Qt.AlignmentFlag.AlignTop
        )

        # layout: Aesthetics
        self.settings_interface.vBoxlayout.addItem(spacer)
        self.settings_interface.vBoxlayout.addWidget(
            aesthetics, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            dark_theme, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            transparent, alignment=Qt.AlignmentFlag.AlignTop
        )

        # layout: Development
        self.settings_interface.vBoxlayout.addItem(spacer)
        self.settings_interface.vBoxlayout.addWidget(
            development, alignment=Qt.AlignmentFlag.AlignTop
        )
        self.settings_interface.vBoxlayout.addWidget(
            self.api_url, alignment=Qt.AlignmentFlag.AlignTop
        )

    def _change_visual(self, *args, **kwargs):
        dark_theme = kwargs.get("dark_theme", None)
        transparent = kwargs.get("transparent", None)

        if dark_theme is not None:
            setTheme(Theme.DARK if dark_theme else Theme.LIGHT)

            self.prototype_interface.setSplitterTheme(dark_theme)
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

        self._update_queue_list_item_theme(dark_theme)
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

        self.info_bars = InfoBars(self)

        self.push_button = PushButton("Start")

    def dismissal_setup_ui(self):
        self.stream_card = AIStreamCard()
        self.stream_card.setFixedWidth(725)
        self.stream_card.setMinimumWidth(725)
        self.stream_card.setFixedHeight(350)

        self.stream_card.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )

        controls = Container("File Controls", "horizontal", self)
        template_control = Container("Template Controls", "horizontal", self)
        controls.setFixedWidth(725)
        controls.setContentsMargins(0, 5, 0, 0)
        template_control.setFixedWidth(725)
        template_control.setContentsMargins(0, 20, 0, 0)

        self.file_button = PushButtonData(FIF.ADD_TO, "Add new file")
        self.file_button.setFixedWidth(275)

        self.save_location_btn = PushButtonData(FIF.FOLDER_ADD, "Save location")
        self.save_location_btn.setFixedWidth(150)

        self.open_save_location_btn = PushButton(FIF.FOLDER, "Open Generated Documents")
        self.open_save_location_btn.setFixedWidth(225)

        self.scan_stop_btn = PushButtonData(QIcon("icons:bot.icon.svg"), "Scan PDF")
        self.scan_stop_btn.setFixedWidth(125)

        self.generate_doc_btn = PushButton(CFIF.NEW_FILE, "Generate")
        self.generate_doc_btn.setFixedWidth(125)
        self.generate_doc_btn.setEnabled(False)

        # Template
        self.template_combobox = ComboBox()
        self.template_combobox.setFixedWidth(150)
        self.template_combobox.addItems([template.value for template in TemplateType])
        self.template_combobox.setPlaceholderText("Choose template")
        self.template_combobox.setCurrentIndex(-1)

        self.include_reply = CheckBox("Include Reply")

        spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Connections
        self.file_button.clicked.connect(partial(self._browse, 0))
        self.save_location_btn.clicked.connect(partial(self._browse, 1))
        self.open_save_location_btn.clicked.connect(self._open_save_location)
        self.template_combobox.currentTextChanged.connect(
            self._update_template_combobox
        )
        self.scan_stop_btn.clicked.connect(self.generate)
        self.generate_doc_btn.clicked.connect(
            self.view_model._handle_document_generation
        )

        # File Control layout
        controls._layout.addWidget(self.save_location_btn, Qt.AlignmentFlag.AlignLeft)
        controls._layout.addWidget(
            self.open_save_location_btn, Qt.AlignmentFlag.AlignLeft
        )
        controls._layout.addItem(spacer)
        controls._layout.addWidget(self.generate_doc_btn, Qt.AlignmentFlag.AlignRight)

        # Template Control Layout
        template_control._layout.addWidget(self.file_button, Qt.AlignmentFlag.AlignLeft)
        template_control._layout.addWidget(
            self.template_combobox, Qt.AlignmentFlag.AlignLeft
        )
        template_control._layout.addWidget(
            self.include_reply, Qt.AlignmentFlag.AlignLeft
        )
        template_control._layout.addWidget(
            self.scan_stop_btn, Qt.AlignmentFlag.AlignLeft
        )

        # Dismissal Layout
        self.dismissal_interface.vBoxlayout.addWidget(
            self.stream_card,
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

    def draft_setup_ui(self):
        self.stream_view = AIStreamCard()
        self.stream_view.setFixedWidth(725)
        self.stream_view.setMinimumWidth(725)
        self.stream_view.setFixedHeight(350)

        self.stream_view.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )

        controls = Container("File Controls", "horizontal", self)
        template_control = Container("Template Controls", "horizontal", self)
        controls.setFixedWidth(725)
        controls.setContentsMargins(0, 5, 0, 0)
        template_control.setFixedWidth(725)
        template_control.setContentsMargins(0, 20, 0, 0)

        self.file_button_pr = PushButtonData(FIF.ADD_TO, "Add new file")
        self.file_button_pr.setFixedWidth(275)

        self.save_location_btn_pr = PushButtonData(FIF.FOLDER_ADD, "Save location")
        self.save_location_btn_pr.setFixedWidth(150)

        self.open_save_location_btn_pr = PushButton(
            FIF.FOLDER, "Open Generated Documents"
        )
        self.open_save_location_btn_pr.setFixedWidth(225)

        self.scan_stop_btn_pr = PushButtonData(QIcon("icons:bot.icon.svg"), "Scan PDF")
        self.scan_stop_btn_pr.setFixedWidth(125)

        self.generate_doc_btn_pr = PushButton(CFIF.NEW_FILE, "Generate")
        self.generate_doc_btn_pr.setFixedWidth(125)
        self.generate_doc_btn_pr.setEnabled(False)

        # Template
        self.template_combobox_pr = ComboBox()
        self.template_combobox_pr.setFixedWidth(150)
        self.template_combobox_pr.addItems(
            [template.value for template in TemplateType]
        )
        self.template_combobox_pr.setPlaceholderText("Choose template")
        self.template_combobox_pr.setCurrentIndex(-1)

        self.include_reply_pr = CheckBox("Include Reply")

        spacer = QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Connections
        self.file_button_pr.clicked.connect(
            lambda id=1, icon=CFIF.ACTIVE, loop=True: self.set_queue_item_icon(
                id, icon, loop
            )
        )
        self.save_location_btn_pr.clicked.connect(lambda id=1, icon=CFIF.STOPPED, loop=False: self.set_queue_item_icon(
                id, icon, loop
        ))
        # self.file_button_pr.clicked.connect(partial(self._browse, 0))
        # self.save_location_btn_pr.clicked.connect(partial(self._browse, 1))
        # self.open_save_location_btn_pr.clicked.connect(self._open_save_location)
        # self.template_combobox_pr.currentTextChanged.connect(self._update_template_combobox)
        # self.scan_stop_btn_pr.clicked.connect(self.generate)
        # self.generate_doc_btn_pr.clicked.connect(self.view_model._handle_document_generation)

        # File Control layout
        controls._layout.addWidget(
            self.save_location_btn_pr, Qt.AlignmentFlag.AlignLeft
        )
        controls._layout.addWidget(
            self.open_save_location_btn_pr, Qt.AlignmentFlag.AlignLeft
        )
        controls._layout.addItem(spacer)
        controls._layout.addWidget(
            self.generate_doc_btn_pr, Qt.AlignmentFlag.AlignRight
        )

        # Template Control Layout
        template_control._layout.addWidget(
            self.file_button_pr, Qt.AlignmentFlag.AlignLeft
        )
        template_control._layout.addWidget(
            self.template_combobox_pr, Qt.AlignmentFlag.AlignLeft
        )
        template_control._layout.addWidget(
            self.include_reply_pr, Qt.AlignmentFlag.AlignLeft
        )
        template_control._layout.addWidget(
            self.scan_stop_btn_pr, Qt.AlignmentFlag.AlignLeft
        )

        # Dismissal Layout
        self.prototype_interface.right_w.vBoxlayout.addWidget(
            self.stream_view,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        self.prototype_interface.right_w.vBoxlayout.addWidget(
            template_control,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        self.prototype_interface.right_w.vBoxlayout.addWidget(
            controls,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )

    def connections(self):
        self.scan_stop_btn_pr.clicked.connect(self._prototype)
        self.prototype_interface.leftWidgetAtMinimum.connect(
            self._set_queue_list_text_visibility
        )

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
                    text = self.view_model._truncate_string(filename, 30)
                    self.file_button.setText(text)
                    if self.view_model.is_new_session(file_path) is True:
                        self.view_model._document = None
                        self.generate_doc_btn.setEnabled(False)
                else:
                    self.file_button.setText("Add file")

            else:
                directory = QFileDialog.getExistingDirectory(self, "Select Directory")
                if not (directory is None or len(directory) == 0):
                    self._save_location(directory=directory)

        except Exception:
            print(traceback.format_exc())

    def _save_location(self, directory):
        if not os.path.exists(directory) and len(directory) == 0:
            raise IOError("Directory not found")

        self.save_location_btn.data = directory
        _directory = os.path.basename(directory)
        text = self.view_model._truncate_string(_directory, 14)

        if len(text) == 0:
            text = "Save Location"

        self.save_location_btn.setText(text)
        
        if self.cfg.save_location != directory:
            self.cfg.save_location.value = directory
            
        self.cfg.save()

    @pyqtSlot(str)
    def _update_template_combobox(self, text):
        template_enum = TemplateType(text)
        if template_enum in [
            TemplateType.RESO_AIR,
            TemplateType.RESO_HW,
            TemplateType.RESO_WATER,
            TemplateType.RESO_PD,
        ]:
            self.include_reply.setChecked(False)
            self.include_reply.setEnabled(False)
        else:
            self.include_reply.setEnabled(True)

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

    def show_template_dir(self):
        self.show_message_box(
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

    def generate(self):
        if self.scan_stop_btn.data == "scanning":
            self.view_model.handle_stream_stop(True)
            self.scan_stop_btn.setEnabled(False)
            return

        self.generate_doc_btn.setEnabled(False)
        self.stream_card.chatbox.setPlainText("")
        try:
            data = GenerateDocData(
                url=self.api_url.data,
                pdf_path=self.file_button.data,
                save_path=self.save_location_btn.data,
                is_reply_included=self.include_reply.isChecked(),
                selected_template=TemplateType(self.template_combobox.currentText()),
                is_custom_prompt=False,
                custom_prompt="",
            )
            success, e = self.view_model.main_handler(data)

            if success is True:
                self.stream_card.chatbox.setPlainText("Preparing... ")
                self.scan_stop_btn.data = "scanning"
                self.scan_stop_btn.setText("Stop")

        except Exception as e:
            print(traceback.format_exc())
            self.show_message_box("Error", f"{e}")

    def generate_events(self, doc: UpdateDocData, id: str):
        if doc.status == "Done":
            self.generate_doc_btn.setEnabled(True)
            pass

        if doc.error:
            self.generate_doc_btn.setEnabled(True)
            self.show_message_box("Error", str(doc.error))

    def update_chatbox(self, text: str):
        self.stream_card.chatbox.moveCursor(
            self.stream_card.chatbox.textCursor().MoveOperation.End
        )
        self.stream_card.chatbox.insertPlainText(text)

    @pyqtSlot(bool)
    def _finished(self, state):
        if state is True:
            self.scan_stop_btn.setText("Scan PDF")
            self.scan_stop_btn.data = "not-scanning"
            self.generate_doc_btn.setEnabled(True)

    @pyqtSlot(bool)
    def _stream_stopped_success(self, state):
        if state is not True:
            self.show_message_box("Error", "RESTART THE APP")
            return

        self.scan_stop_btn.data = "not-scanning"
        self.scan_stop_btn.setText("Scan PDF")
        self.scan_stop_btn.setEnabled(True)

    @pyqtSlot(str)
    def _handle_error(self, err):
        self.show_message_box("Error", err)
        self.stream_card.chatbox.setPlainText("")
        self.scan_stop_btn.setText("Scan PDF")

    @pyqtSlot(object)
    def _cloud_llm_error(self, err):
        self.stream_card.chatbox.moveCursor(
            self.stream_card.chatbox.textCursor().MoveOperation.End
        )
        self.stream_card.chatbox.insertPlainText(
            "\nOppsss...Something went wrong on my end."
        )
        self.generate_doc_btn.setEnabled(True)

    def add_item(self, text, data = None):
        queue_item = QueueItem(
            text=text, 
            icon=CFIF.ACTIVE, 
            loop=False,
            id=data,
            dark_theme=self.cfg.darkTheme.value
        )
        list_item = QListWidgetItem(self.prototype_interface.left_w)
        list_item.setSizeHint(queue_item.sizeHint())
        self.prototype_interface.left_w.addItem(list_item)
        self.prototype_interface.left_w.setItemWidget(list_item, queue_item)

    def set_queue_item_icon(self, id, icon, loop: bool = False):
        queue_item = self.get_queue_item(id)
        queue_item.set_icon(icon=icon, loop=loop)

        if loop is True:
            queue_item.icon_label.resume_animation()
        else:
            queue_item.set_icon(CFIF.STOPPED)
            queue_item.icon_label.stop_animation(CFIF.STOPPED.path())

    def get_queue_item(self, id) -> QueueItem:
        list_items = self._get_queue_list_items()
        for list_item in list_items:
            list_item: QListWidgetItem = list_item
            queue_item: QueueItem = self.prototype_interface.left_w.itemWidget(list_item)
            if queue_item.data == id:
                return queue_item

    def _get_queue_list_items(self) -> list[QListWidgetItem]:
        items = [
            self.prototype_interface.left_w.item(i)
            for i in range(self.prototype_interface.left_w.count())
        ]
        return items

    def _update_queue_list_item_icons(self):
        items = self._get_queue_list_items()

        for item in items:
            item: QListWidgetItem = item
            queue_item: QueueItem = self.prototype_interface.left_w.itemWidget(item)
            queue_item.set_icon(CFIF.ACTIVE)
    
    def _update_queue_list_item_theme(self, dark_theme):
        items = self._get_queue_list_items()

        for item in items:
            item: QListWidgetItem = item
            queue_item: QueueItem = self.prototype_interface.left_w.itemWidget(item)
            queue_item.change_theme(dark_theme)

    @pyqtSlot(bool)
    def _set_queue_list_text_visibility(self, hide: bool):
        list_items = self._get_queue_list_items()

        for list_item in list_items:
            list_item: QListWidgetItem = list_item
            queue_item: QueueItem = self.prototype_interface.left_w.itemWidget(list_item)
            if hide is True:
                queue_item.hide_text()
            else:
                queue_item.show_text()

    def _prototype(self):
        try:
            for i in range(5):
                self.add_item(f"item {i}", i)
        except Exception:
            print(traceback.format_exc())

    def closeEvent(self, e):
        self.view_model.stop_agents()
        return super().closeEvent(e)


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
