from dataclasses import dataclass, field, fields, asdict
from typing import Any

from PyQt6.QtCore import QSettings, QSize, QPoint

@dataclass
@dataclass
class WindowGeom:
    size: QSize = field(default_factory=lambda: QSize(600, 500))
    pos: QPoint = field(default_factory=lambda: QPoint(100, 100))

@dataclass
class Settings:
    windowGeometry: WindowGeom = field(default_factory=WindowGeom)
    api_url: str = "https://sheep-promoted-manatee.ngrok-free.app"

class SettingsModel:
    """Handles application settings using QSettings."""

    def __init__(self):
        self._settings = QSettings("OrDraft", "OrDraft")

    @property
    def settings(self) -> Settings:
        """Loads QSettings into the Settings dataclass dynamically."""
        _settings = self._load_settings(Settings)
        return _settings

    def _load_settings(self, dataclass_type):
        """Recursively loads settings into the given dataclass."""
        settings_data = {}
        
        for field_info in fields(dataclass_type):
            key = field_info.name
            qsettings_value = self._settings.value(key, None)

            if qsettings_value is None:
                if field_info.default is not field_info.default_factory:
                    settings_data[key] = field_info.default
                elif field_info.default_factory is not None:
                    settings_data[key] = field_info.default_factory()
                else:
                    raise ValueError(f"Missing required setting: {key}")

            else:
                # Handle nested dataclasses
                if isinstance(field_info.type, type) and issubclass(field_info.type, WindowGeom):
                    settings_data[key] = self._deserialize_window_geom(qsettings_value)
                else:
                    settings_data[key] = qsettings_value
        
        return dataclass_type(**settings_data)

    def _deserialize_window_geom(self, value: Any) -> WindowGeom:
        """Convert stored QSettings value to WindowGeom dataclass."""
        if isinstance(value, dict):
            size = value.get("size", QSize(800, 600))
            pos = value.get("pos", QPoint(100, 100))
        else:
            size, pos = QSize(800, 600), QPoint(100, 100)  # Default fallback

        return WindowGeom(size=size, pos=pos)

    def save_settings(self, settings: Settings):
        """Save a Settings dataclass instance into QSettings dynamically."""
        settings_dict = asdict(settings)
        for key, value in settings_dict.items():
            if isinstance(value, WindowGeom):
                self._settings.setValue(key, {"size": value.size, "pos": value.pos})
            else:
                self._settings.setValue(key, value)


    def get_value(self, key, default_value=None):
        """Retrieve a setting value."""
        return self._settings.value(key, default_value)

    def set_value(self, key, value):
        """Save a setting value."""
        self._settings.setValue(key, value)

    def get_window_geometry(self):
        """Retrieve saved window geometry (size & position)."""
        return self._settings.value("windowGeometry", None)

    def set_window_geometry(self, geometry):
        """Save window geometry (size & position)."""
        self._settings.setValue("windowGeometry", geometry)

    def set_api_url(self, url="https://sheep-promoted-manatee.ngrok-free.app"):
        self.set_value("api_url", url)
    
    def get_api_url(self):
        return self._settings.value("api_url", "")
        
