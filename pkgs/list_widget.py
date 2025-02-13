import sys  

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
)
from PyQt6.QtCore import QSize, Qt

class AutoResizeLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: green;")
        self.adjustSize() 
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def setText(self, text):  
        super().setText(text)  
        self.adjustSize()

class CustomListItem(QWidget):  
    def __init__(self, status, name, parent=None, id=None):  
        super().__init__(parent)  
        
        self._uuid = id

        layout = QHBoxLayout(self)
        
        self.status = AutoResizeLabel(status)  
        self.status.setStyleSheet("color: #63FF9A;")


        self.name = QLabel(name)
        
        self.button = QPushButton()  
        self.button.setIconSize(QSize(16, 16))
        self.button.setFixedSize(QSize(24,24))

        layout.addWidget(self.status)  
        layout.addWidget(self.name, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)  
        layout.addWidget(self.button)  
        
        layout.setContentsMargins(8, 4, 8, 4)  
        self.setLayout(layout)  

    @property
    def id(self):
        return self._uuid
    
    def set_status_color(self, state:str = "Normal"):
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
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        main_layout.addWidget(self.list_widget)  
        
        for i in range(5):  
            item = QListWidgetItem()  
            custom_widget = CustomListItem(f"Item {i+1}")  
            
            custom_widget.button.clicked.connect(lambda checked, index=i: self.on_button_clicked(index))  
            
            item.setSizeHint(custom_widget.sizeHint())  
            
            self.list_widget.addItem(item)  
            
            self.list_widget.setItemWidget(item, custom_widget)  

    def on_button_clicked(self, index):  
        print(f"Button in item {index+1} clicked!")  


def main():  
    app = QApplication(sys.argv)  
    window = MainWindow()  
    window.show()  
    sys.exit(app.exec())  


if __name__ == "__main__":  
    main()  
