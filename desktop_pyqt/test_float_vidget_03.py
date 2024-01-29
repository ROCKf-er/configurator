import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Создаем виджеты, которые будут включены в основной виджет
        self.text_edit = QLineEdit(self)
        self.button = QPushButton('Click me', self)

        # Создаем вертикальный макет и добавляем в него виджеты
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)

        # Настроим виджет
        self.setGeometry(100, 100, 300, 200)
        self.setWindowTitle('Custom Widget Example')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())
