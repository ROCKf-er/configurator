import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QTimer, QEventLoop

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

        self.label = QLabel("Статус: Готово")
        self.layout.addWidget(self.label)

        self.central_widget.setLayout(self.layout)

        # Создаем таймер для периодического обновления
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_task_status)
        self.timer.start(100)  # Обновление каждые 100 мс

        # # Создаем цикл событий asyncio
        # self.asyncio_loop = QEventLoop(self)
        # asyncio.set_event_loop(self.asyncio_loop)
        loop = asyncio.new_event_loop()
        self.asyncio_loop = loop


    def start_async_task(self):

        asyncio.set_event_loop(self.asyncio_loop)
        asyncio.ensure_future(my_async_task(), loop=self.asyncio_loop)
        asyncio.set_event_loop(None)

    def update_task_status(self):
        # Обновляем статус асинхронной задачи
        if asyncio.all_tasks(loop=self.asyncio_loop):
            self.label.setText("Статус: Выполняется")
        else:
            self.label.setText("Статус: Готово")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())