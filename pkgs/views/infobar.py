# coding:utf-8
import os
import sys
from typing import Union

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    InfoBarIcon,
    InfoBar,
    PushButton,
    setTheme,
    Theme,
    FluentIcon,
    InfoBarPosition,
    InfoBarManager,
    FluentIconBase,
)

if __name__ == "__main__" or "pkgs" not in sys.modules:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pkgs.icons import MyFluentIcon


@InfoBarManager.register("Custom")
class CustomInfoBarManager(InfoBarManager):
    """Custom info bar manager"""

    def _pos(self, infoBar: InfoBar, parentSize=None):
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        x = (parentSize.width() - infoBar.width()) // 2
        y = (parentSize.height() - infoBar.height()) // 2

        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y += bar.height() + self.spacing

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() - 16)


class InfoBars(QWidget):

    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)

        self.hBoxLayout = QHBoxLayout(self)
        self.button1 = PushButton("Information", self)
        self.button2 = PushButton("Success", self)
        self.button3 = PushButton("Warning", self)
        self.button4 = PushButton("Error", self)
        self.button5 = PushButton("Custom", self)
        self.button6 = PushButton("Desktop", self)

        self.button1.clicked.connect(self.createInfoInfoBar)
        self.button2.clicked.connect(self.createSuccessInfoBar)
        self.button3.clicked.connect(self.createWarningInfoBar)
        self.button4.clicked.connect(self.createErrorInfoBar)
        self.button5.clicked.connect(self.createCustomInfoBar)
        self.button6.clicked.connect(self.createDeskTopBottomRightInfoBar)

        self.hBoxLayout.addWidget(self.button1)
        self.hBoxLayout.addWidget(self.button2)
        self.hBoxLayout.addWidget(self.button3)
        self.hBoxLayout.addWidget(self.button4)
        self.hBoxLayout.addWidget(self.button5)
        self.hBoxLayout.addWidget(self.button6)
        self.hBoxLayout.setContentsMargins(30, 0, 30, 0)

        self.resize(700, 700)

    def createInfoInfoBar(self, title: str, content: str, duration: int = -1):
        """Create Information bar

        Args:
            title (str): 
            content (str): 
            duration (int, optional): use milliseconds. Defaults to -1, -1 = disable auto close
        """        
        w = InfoBar(
            icon=InfoBarIcon.INFORMATION,
            title=title,
            content=content,
            orient=Qt.Orientation.Vertical,  # vertical layout
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self,
        )
        w.addWidget(PushButton("Action"))
        w.show()

    def createSuccessInfoBar(self, title: str, content: str, duration: int = -1):
        """Create Success bar

        Args:
            title (str): 
            content (str): 
            duration (int, optional): use milliseconds. Defaults to -1, -1 = disable auto close
        """    
        # convenient class mothod
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            # position='Custom',   # NOTE: use custom info bar manager
            duration=duration,
            parent=self,
        )

    def createWarningInfoBar(self, title: str, content: str, duration: int = -1):
        """Creates Warning bar

        Args:
            title (str): 
            content (str): 
            duration (int, optional): use milliseconds. Defaults to -1, -1 = disable auto close
        """    
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=False,  # disable close button
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self,
        )

    def createErrorInfoBar(self, title: str, content: str, duration: int = -1):
        """Create error bar

        Args:
            title (str): 
            content (str): 
            duration (int, optional): use milliseconds. Defaults to -1, -1 = disable auto close
        """    
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self,
        )

    def createCustomInfoBar(
        self,
        title: str,
        content: str,
        icon: Union[FluentIcon, FluentIconBase, MyFluentIcon] = None,
        duration: int = -1,
    ):
        """Create info bar with custom icon

        Args:
            title (str): 
            content (str): 
            duration (int, optional): use milliseconds. Defaults to -1, -1 = disable auto close
        """    
        if isinstance(icon, None):
            raise TypeError("icon is type of None")
        w = InfoBar.new(
            icon=icon,
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=self,
        )
        w.setCustomBackgroundColor("white", "#202020")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = InfoBars()
    w.show()
    app.exec()
