from enum import Enum

from qfluentwidgets import getIconColor, Theme, FluentIconBase


class MyFluentIcon(FluentIconBase, Enum):
    """ Custom icons """

    THEMEMODE = "theme"
    URL = "link"
    NEW_FILE = "new_file"

    def path(self, theme=Theme.AUTO):
        return f'icons:{self.value}_{getIconColor(theme)}.svg'
