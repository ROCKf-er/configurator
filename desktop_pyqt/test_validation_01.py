from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Создаем QTableWidget
        self.tableWidget = QTableWidget(self)

        # Задаем количество строк и столбцов
        self.tableWidget.setRowCount(2)
        self.tableWidget.setColumnCount(2)

        # Заполняем таблицу тестовыми данными
        self.tableWidget.setItem(0, 0, QTableWidgetItem("1"))
        self.tableWidget.setItem(0, 1, QTableWidgetItem("2"))
        self.tableWidget.setItem(1, 0, QTableWidgetItem("3"))
        self.tableWidget.setItem(1, 1, QTableWidgetItem("4"))

        # Подключаем событие itemChanged к соответствующему слоту
        self.tableWidget.itemChanged.connect(self.validate_cell)

        # Создаем макет и добавляем таблицу
        layout = QVBoxLayout(self)
        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Добавление собственной функции валидации для QTableWidget')
        self.show()

    def validate_cell(self, item):
        # Получаем текущее значение ячейки
        current_value = item.text()

        # Проверяем, соответствует ли значение условию (например, является ли целым числом)
        try:
            int_value = int(current_value)
        except ValueError:
            # Если не соответствует, сбрасываем значение на предыдущее
            item.setText(item.data(Qt.EditRole))


if __name__ == '__main__':
    app = QApplication([])
    window = MyWindow()
    app.exec_()