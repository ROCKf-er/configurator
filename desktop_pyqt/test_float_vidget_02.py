import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi


class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(0, 0, 400, 300)
        self.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Создаем кнопку на виджете
        self.button = QPushButton('Click me!', self)
        self.button.clicked.connect(self.on_button_click)

        # Размещаем кнопку по центру виджета
        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.setAlignment(Qt.AlignCenter)

    def on_button_click(self):
        print("Button clicked!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Загружаем интерфейс из файла .ui
        loadUi('form_02.ui', self)

        # Создаем новый виджет, который будет отображаться поверх всех прочих виджетов
        overlay_widget = OverlayWidget(self)
        overlay_widget.show()

        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Overlay Example')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
