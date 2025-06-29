from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, 
)

def create_layout(orientation: str = "vertical", parent=None):
    """
    Factory function to create a QVBoxLayout or QHBoxLayout.

    Parameters:
        orientation (str): Either "vertical" or "horizontal" (case-insensitive).
        parent: The parent widget for the layout.
    
    Returns:
        A QVBoxLayout or QHBoxLayout instance.
    """
    if orientation.lower() == "vertical":
        layout = QVBoxLayout(parent)
    elif orientation.lower() == "horizontal":
        layout = QHBoxLayout(parent)
    else:
        raise ValueError("Orientation must be 'vertical' or 'horizontal'")
    
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    return layout