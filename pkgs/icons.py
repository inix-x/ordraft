from enum import Enum

from qfluentwidgets import getIconColor, Theme, FluentIconBase, theme


class MyFluentIcon(FluentIconBase, Enum):
    """ Custom icons """

    THEMEMODE = "theme"
    URL = "link"
    NEW_FILE = "new_file"
    ACTIVE = "active"
    WAITING = "waiting"
    ERROR = "error"
    CANCELLED = "cancelled"
    SUCCESS = "success"
    STOPPED = "stopped"

    def path(self, current_theme=Theme.AUTO, no_dark_theme: bool = False):
        _theme = theme()
        if no_dark_theme is False:
            return f'icons:{self.value}_{getIconColor(_theme)}.svg'
        else:
            return f'icons:{self.value}.svg'
