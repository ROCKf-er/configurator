import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton
from PyQt5.QtGui import QColor
from PyQt5.uic import loadUi
from PyQt5 import QtCore


class TopMostWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 200, 100)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background-color: rgba(255, 0, 0, 128);")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Загружаем интерфейс из файла .ui
        loadUi('form_02.ui', self)

        # Создаем новый виджет, который будет отображаться поверх всех прочих виджетов
        topmost_widget = TopMostWidget(self)
        topmost_widget.show()

        # Добавляем кнопку на основной виджет
        button = QPushButton('Click me!', self)
        button.clicked.connect(self.on_button_click)

        self.setGeometry(100, 100, 400, 300)
        self.setWindowTitle('Overlay Example')

        button.move(50, 30)

    def on_button_click(self):
        print("Button clicked!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
