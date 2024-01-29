from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QEvent

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        label = QLabel("Кликните вне виджетов")
        layout.addWidget(label)

        button = QPushButton("Нажми меня")
        layout.addWidget(button)

        self.setLayout(layout)

        # Устанавливаем фильтр событий для окна
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            # Событие MouseButtonPress срабатывает, когда происходит клик мышью
            # Проверяем, что клик был вне границ виджетов в окне
            for widget in self.findChildren(QWidget):
                if widget.geometry().contains(event.pos()):
                    # Клик был внутри какого-то виджета, прекращаем обработку события
                    return super().eventFilter(obj, event)

            print("Клик вне виджетов")
        return super().eventFilter(obj, event)

if __name__ == '__main__':
    app = QApplication([])

    window = MyWindow()
    window.show()

    app.exec_()
