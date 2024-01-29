from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLineEdit, QStyledItemDelegate
from PyQt5.QtCore import Qt

class ValidationDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.textChanged.connect(self.validate_cell)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)

    def validate_cell(self, text):
        # Ваша логика валидации, например, проверка наличия числового значения
        try:
            int_value = int(text)
            # Здесь вы можете выполнить необходимые действия при успешной валидации
            print("Введено Корректное значение")
        except ValueError:
            # Если не соответствует, можно обработать это как угодно, например, вывести предупреждение
            print("Введено некорректное значение")

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

        # Устанавливаем кастомный делегат для ячеек
        delegate = ValidationDelegate(self)
        self.tableWidget.setItemDelegate(delegate)

        # Создаем макет и добавляем таблицу
        layout = QVBoxLayout(self)
        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Добавление собственной функции валидации для QTableWidget')
        self.show()

if __name__ == '__main__':
    app = QApplication([])
    window = MyWindow()
    app.exec_()