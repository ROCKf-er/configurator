from PyQt5.QtWidgets import QApplication, QTableView, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Создаем модель данных
        self.model = QStandardItemModel(self)

        # Создаем таблицу и устанавливаем модель данных
        self.tableView = QTableView(self)
        self.tableView.setModel(self.model)

        # Заполняем таблицу тестовыми данными
        self.model.setItem(0, 0, QStandardItem("Ячейка 1"))
        self.model.setItem(0, 1, QStandardItem("Ячейка 2"))

        # Подключаем сигнал dataChanged к соответствующему слоту
        self.model.dataChanged.connect(self.on_data_changed)

        # Создаем макет и добавляем таблицу
        layout = QVBoxLayout(self)
        layout.addWidget(self.tableView)

        self.setLayout(layout)

        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Отслеживание изменения содержимого ячейки')
        self.show()

    def on_data_changed(self, topLeft, bottomRight):
        # Получаем измененное значение ячейки
        changed_item = self.model.itemFromIndex(topLeft)
        new_value = changed_item.text()

        # Получаем координаты измененной ячейки
        row = topLeft.row()
        column = topLeft.column()

        print(f"Изменено содержимое ячейки ({row}, {column}): {new_value}")


if __name__ == '__main__':
    app = QApplication([])
    window = MyWindow()
    app.exec_()