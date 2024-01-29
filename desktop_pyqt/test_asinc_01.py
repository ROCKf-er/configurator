import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QEventLoop, QTimer

async def my_async_task():
    print("Start async task")
    await asyncio.sleep(2)  # Симулируем асинхронную задачу, занимающую время
    print("Async task completed")

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.button = QPushButton("Запустить асинхронную задачу")
        self.button.clicked.connect(self.start_async_task)
        self.layout.addWidget(self.button)

        self.central_widget.setLayout(self.layout)

    def start_async_task(self):
        # Создаем асинхронный цикл событий
        loop = asyncio.new_event_loop()

        # Запускаем асинхронную задачу в цикле событий
        asyncio.set_event_loop(loop)
        loop.run_until_complete(my_async_task())
        asyncio.set_event_loop(None)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())