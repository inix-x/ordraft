# coding:utf-8
import sys
import traceback

from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (FluentIcon, TransparentDropDownPushButton, RoundMenu, CommandBar, Action,
                            setTheme, Theme, setFont, CommandBarView, Flyout, FlyoutAnimationType,
                            ImageLabel, ToolButton, PushButton, CardWidget)
from qframelesswindow import FramelessWindow, StandardTitleBar


class CommandBarCard(CardWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundColor(self._normalBackgroundColor())
        
        self.setClickEnabled(False)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(4, 4, 4, 4)

        self.commandbar = CommandBar(self)
        self.commandbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        # self.commandBar.setMenuDropDown(False)
        # self.commandBar.setButtonTight(True)
        # setFont(self.commandbar, 14)

        self.hBoxLayout.addWidget(self.commandbar, 0)

        # self.dropDownButton = self.createDropDownButton()

        # change button style

        # self.addButton(FluentIcon.ADD, 'Add', QKeySequence("ctrl+n"), lambda: print("new"))

        # self.commandbar.addSeparator()

        # self.commandbar.addAction(Action(FluentIcon.EDIT, 'Edit', triggered=self.onEdit, checkable=True))
        # # self.commandbar.addWidget(self.dropDownButton)
        # self.addButton(QIcon(FluentIcon.COPY.path()), 'Copy', QKeySequence("ctrl+c"), lambda: print("test"))
        # # copy_action.triggered.connect(lambda: print("copy"))
        # # self.commandbar.addAction(copy_action)
        # save_action = self.addAction(QIcon(FluentIcon.SHARE.path()), 'Share', QKeySequence("ctrl+s"))
        # save_action.triggered.connect(lambda: print("share"))
        # self.commandbar.addAction(save_action)


    def addButton(
        self,
        icon: QIcon,
        text: str,
        shortcut: QKeySequence | QKeySequence.StandardKey | str | int | None,
        triggered = None
    ) -> Action:
        try:
            action = Action(icon, text, shortcut=shortcut, triggered=triggered)
            self.commandbar.addAction(action)
        except Exception as e:
            print(traceback.format_exc())
            return e

    # def onEdit(self, isChecked):
    #     print('Enter edit mode' if isChecked else 'Exit edit mode')

    # def onEditProto(self, isChecked):
    #     if isChecked is True:
    #         self.button_menu.setText("Edit")
    #     else:
    #         self.button_menu.setText("Menu")

    def createDropDownButton(self, actions: list[Action]) -> tuple[TransparentDropDownPushButton, RoundMenu] | Exception:
        try:
            button_menu = TransparentDropDownPushButton('Menu', self, FluentIcon.MENU)
            button_menu.setFixedHeight(34)
            setFont(button_menu, 12)

            menu = RoundMenu(parent=self)
            menu.addActions(actions)
            # menu.addAction(Action(FluentIcon.EDIT, 'Edit', triggered=onEditProto, checkable=True))
            button_menu.setMenu(menu)
            return button_menu, menu
        except Exception as e:
            print(traceback.format_exc())
            return e

    def _hoverBackgroundColor(self):
        return super()._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        return super()._normalBackgroundColor()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w1 = CommandBarCard()
    w1.show()
    app.exec()
