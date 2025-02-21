import os
import sys
from typing import Optional
import os
import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QApplication,
    QSizePolicy,
    QSizePolicy,
)
from PyQt6.QtCore import (
    QSize,
    Qt,
    QPropertyAnimation,
    QRectF,
    pyqtProperty,
    QEasingCurve,
    QSequentialAnimationGroup,
    QAbstractAnimation
)
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

from pkgs.icons import MyFluentIcon as CFIF


class PulsatingSvgLabel(QLabel):
    def __init__(self, svg_file: str = None, loop: bool = True, parent=None):
        super().__init__(parent)
        self.renderer = None 
        self._scaleFactor = 1.0  

        # Determine loop count: infinite (-1) if loop is True; otherwise, 0 (no loop)
        self._loop = -1 if loop is True else 0       
        self.animationGroup = QSequentialAnimationGroup(self)
        self.start_animation()

        self.stop_anim = None 
        self.resume_anim = None

        # Optionally set the SVG icon if provided.
        if svg_file:
            self.setIcon(svg_file)

    def start_animation(self):
        # Animation for scaling up from 0.75 to 1.
        animation_up = QPropertyAnimation(self, b"scaleFactor")
        animation_up.setStartValue(0.60)
        animation_up.setEndValue(1)
        animation_up.setDuration(1000)
        animation_up.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Animation for scaling down from 1 to 0.75.
        animation_down = QPropertyAnimation(self, b"scaleFactor")
        animation_down.setStartValue(1)
        animation_down.setEndValue(0.60)
        animation_down.setDuration(1000)
        animation_down.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Add the animations in sequence.
        self.animationGroup.addAnimation(animation_down)
        self.animationGroup.addAnimation(animation_up)
        self.animationGroup.setLoopCount(self._loop)
        self.animationGroup.start()

    def setIcon(self, path, loop=False):
        self._loop = -1 if loop is True else 0       
        self.renderer = QSvgRenderer(path, self)

    def paintEvent(self, event):
        if self.renderer is not None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
           
            # Calculate a centered, scaled rectangle.
            w = self.width() * self._scaleFactor
            h = self.height() * self._scaleFactor
            x = (self.width() - w) / 2
            y = (self.height() - h) / 2
            target_rect = QRectF(x, y, w, h)
            self.renderer.render(painter, target_rect)

    def getScaleFactor(self) -> float:
        return self._scaleFactor

    def setScaleFactor(self, value: float):
        self._scaleFactor = value
        self.update()

    scaleFactor = pyqtProperty(float, fget=getScaleFactor, fset=setScaleFactor)

    def stop_animation(self, new_svg_file: str = None):
        """
        Stops the pulsating animation with a smooth transition back to a scale factor of 1.0.
        If new_svg_file is provided, the icon is updated once the transition completes.
        """
        if self.animationGroup.state() == QAbstractAnimation.State.Running:
            self.animationGroup.stop()

        self.stop_anim = QPropertyAnimation(self, b"scaleFactor")
        self.stop_anim.setStartValue(self._scaleFactor)
        self.stop_anim.setEndValue(1.0)
        self.stop_anim.setDuration(500)
        self.stop_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Connect the finished signal to update the icon if a new file path is provided.
        if new_svg_file:
            self.stop_anim.finished.connect(lambda: self.setIcon(new_svg_file))
        
        self.stop_anim.start()

    def resume_animation(self):
        """
        Smoothly resumes the pulsating animation by first transitioning to the starting scale (0.60)
        and then restarting the pulsating animation group.
        """
        # If the pulsation group is already running, do nothing.
        if self.animationGroup.state() == QAbstractAnimation.State.Running:
            return

        # Create an animation to transition from the current scale to 0.75.
        self.resume_anim = QPropertyAnimation(self, b"scaleFactor")
        self.resume_anim.setStartValue(self._scaleFactor)
        self.resume_anim.setEndValue(0.60)
        self.resume_anim.setDuration(1000)
        self.resume_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        # Once this transition finishes, rebuild and start the pulsating animation.
        self.resume_anim.finished.connect(self.restart_pulsation)
        self.resume_anim.start()

    def restart_pulsation(self):
        """
        Rebuilds the pulsating animation group and starts it.
        """
        self.animationGroup = QSequentialAnimationGroup(self)

        animation_up = QPropertyAnimation(self, b"scaleFactor")
        animation_up.setStartValue(0.60)
        animation_up.setEndValue(1)
        animation_up.setDuration(1000)
        animation_up.setEasingCurve(QEasingCurve.Type.InOutQuad)

        animation_down = QPropertyAnimation(self, b"scaleFactor")
        animation_down.setStartValue(1)
        animation_down.setEndValue(0.60)
        animation_down.setDuration(1000)
        animation_down.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.animationGroup.addAnimation(animation_up)
        self.animationGroup.addAnimation(animation_down)
        self.animationGroup.setLoopCount(self._loop)
        self.animationGroup.start()


class QueueItem(QWidget):

    def __init__(
        self,
        text: str,
        icon: Optional[CFIF] = None,
        loop: bool = False,
        id: Optional[object] = None,
        parent: Optional[QWidget] = None,
        dark_theme: bool = True
    ):
        """
        Custom list widget item that can display a static icon, and text.

        Args:
            text (str): The text to display.
            icon_path (Optional[str]): File path for the static icon. Defaults to None.
            loop (bool):
            id (any):
            parent (Optional[QWidget]): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._id = id
        self._loop = loop
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.icon_label = PulsatingSvgLabel(loop=loop, parent=self)
        self.icon_label.setFixedSize(20, 20)
        
        self.text_label = QLabel(f" {text}", self)
        self.movie = None
        self.icon: CFIF = icon
        self.init_ui(self.icon)
        self.change_theme(dark_theme)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    def init_ui(self, icon: Optional[CFIF]):
        """
        Initialize the user interface by setting up the layout and adding widgets.

        Args:
            icon (Optional[str]): Path to the static icon image.
        """
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self._layout = QHBoxLayout()
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignHCenter)
        self._layout.setContentsMargins(3, 12, 3, 12)

        if icon:
            self.set_icon(icon)

        self._layout.addWidget(self.icon_label, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignHCenter)
        self._layout.addWidget(self.text_label, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignHCenter)
        
        self.setLayout(self._layout)

    def set_icon(self, icon: CFIF, loop: bool = None):
        """
        Set or update the static icon displayed in the item.

        Args:
            icon (str): Path to the static icon image.
        """

        if icon is not None:
            self._loop = loop if loop is not None else self._loop
            self.icon = icon if icon is not None else self.icon
            self.icon_label.setIcon(self.icon.path(), self._loop)

    def hide_text(self):
        self.text_label.hide()

    def show_text(self):
        self.text_label.show()

    def change_theme(self, is_dark_theme: bool):
        if is_dark_theme is True:
            self.text_label.setStyleSheet("""QLabel { color: white }""")
        else:
            self.text_label.setStyleSheet(""" QLabel { color: black }""")

        self.icon_label.setIcon(self.icon.path(), self._loop)


class AutoResizeLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: green;")
        self.adjustSize()
        self.adjustSize()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setText(self, text):
        super().setText(text)

    def setText(self, text):
        super().setText(text)
        self.adjustSize()



class CustomListItem(QWidget):
    def __init__(self, status, name, parent=None, id=None):
        super().__init__(parent)



class CustomListItem(QWidget):
    def __init__(self, status, name, parent=None, id=None):
        super().__init__(parent)

        self._uuid = id

        layout = QHBoxLayout(self)

        self.status = AutoResizeLabel(status)

        self.status = AutoResizeLabel(status)
        self.status.setStyleSheet("color: #63FF9A;")

        self.name = QLabel(name)

        self.button = QPushButton()

        self.button = QPushButton()
        self.button.setIconSize(QSize(16, 16))
        self.button.setFixedSize(QSize(24, 24))
        self.button.setFixedSize(QSize(24, 24))

        layout.addWidget(self.status)
        layout.addWidget(self.name, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.button)

        layout.setContentsMargins(8, 4, 8, 4)
        self.setLayout(layout)
        layout.addWidget(self.status)
        layout.addWidget(self.name, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.button)

        layout.setContentsMargins(8, 4, 8, 4)
        self.setLayout(layout)

    @property
    def id(self):
        return self._uuid

    def set_status_color(self, state: str = "Normal"):
        if state == "Error":
            self.status.setStyleSheet("color: #CC144A;")
        elif state == "Normal":
            self.status.setStyleSheet("color: #63FF9A;")
        elif state == "Waiting":
            self.status.setStyleSheet("color: #FF9A63;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("List Widget with Custom Items")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.list_widget = QListWidget()
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("List Widget with Custom Items")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        main_layout.addWidget(self.list_widget)

        for i in range(5):
            item = QListWidgetItem()
            custom_widget = CustomListItem(f"Item {i+1}")

            custom_widget.button.clicked.connect(
                lambda checked, index=i: self.on_button_clicked(index)
            )

            item.setSizeHint(custom_widget.sizeHint())

            self.list_widget.addItem(item)

            self.list_widget.setItemWidget(item, custom_widget)
        main_layout.addWidget(self.list_widget)

        for i in range(5):
            item = QListWidgetItem()
            custom_widget = CustomListItem(f"Item {i+1}")

            custom_widget.button.clicked.connect(
                lambda checked, index=i: self.on_button_clicked(index)
            )

            item.setSizeHint(custom_widget.sizeHint())

            self.list_widget.addItem(item)

            self.list_widget.setItemWidget(item, custom_widget)

    def on_button_clicked(self, index):
        print(f"Button in item {index+1} clicked!")
    def on_button_clicked(self, index):
        print(f"Button in item {index+1} clicked!")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
