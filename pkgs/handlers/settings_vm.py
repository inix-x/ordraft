import os
import sys

from PyQt6.QtCore import QSize, QPoint

if __name__ == "__main__" or "pkgs" not in sys.modules:
    test = sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    )

from pkgs.models import SettingsModel, Settings

class SettingsViewModel:
    """Manages interactions between the settings and UI components."""

    def __init__(self, model: SettingsModel):
        self.model = model
        self._settings: Settings = self.model.settings

    @property
    def settings(self) -> Settings:
        return self._settings

    def load_api_url(self):
        self.model.get_api_url()
    
    def set_preferred_api_url(self, url):
        self.model.set_api_url(url)

    def load_window_geometry(self, default_size=QSize(800, 600), default_pos=QPoint(100, 100)):
        """Load window size and position."""
        geometry = self.model.get_window_geometry()
        if geometry:
            return geometry
        return {"size": default_size, "pos": default_pos}

    def save_window_geometry(self, size: QSize, pos: QPoint):
        """Save window size and position."""
        self._settings.windowGeometry.pos = pos
        self._settings.windowGeometry.size = size

    def get_setting(self, key, default_value=None):
        """Fetch a user setting."""
        return self.model.get_value(key, default_value)

    def set_setting(self, key, value):
        """Update a user setting."""
        self.model.set_value(key, value)

    def save_settings(self):
        self.model.save_settings(settings=self._settings)