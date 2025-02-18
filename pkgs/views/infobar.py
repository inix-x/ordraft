# coding:utf-8
import os
import sys
from typing import Union, Any

from PyQt6.QtCore import QPoint, Qt, pyqtSlot
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

    def __init__(self, parent = None):
        super().__init__()

    @pyqtSlot(str, str, int)
    def createInfoInfoBar(self, w: QWidget, title: str, content: str, duration: int = -1):
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
            # position='Custom',
            duration=duration,
            parent=w,
        )
        w.show()
        return w

    @pyqtSlot(str, str, int)
    def createSuccessInfoBar(self, w: QWidget, title: str, content: str, duration: int = -1):
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
            parent=w,
        )
        w.show()
        return w

    @pyqtSlot(str, str, int)
    def createWarningInfoBar(self, w: QWidget, title: str, content: str, duration: int = -1):
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
            parent=w,
        )
        w.show()
        return w

    @pyqtSlot(str, str, int)
    def createErrorInfoBar(self, w: QWidget, title: str, content: str, duration: int = -1):
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
            parent=w,
        )
        w.show()
        return w

    @pyqtSlot(str, str, Any, int)
    def createCustomInfoBar(
        self,
        w: QWidget,
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
        bar = InfoBar.new(
            icon=icon,
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=duration,
            parent=w,
        )
        bar.setCustomBackgroundColor("white", "#202020")
        bar.show()
        return bar


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = InfoBars()
    w.show()
    app.exec()
