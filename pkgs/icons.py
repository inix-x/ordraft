from enum import Enum

from qfluentwidgets import getIconColor, Theme, FluentIconBase


class MyFluentIcon(FluentIconBase, Enum):
    """ Custom icons """

    THEMEMODE = "theme"
    URL = "link"

    def path(self, theme=Theme.AUTO):
        return f'icons:{self.value}_{getIconColor(theme)}.svg'
