import math
import os
import re
import subprocess
import sys
import time
import glob
import serial.tools.list_ports
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QTableWidgetItem, QStyledItemDelegate, QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout, QPushButton, QFrame, QLineEdit, QFileDialog
from PyQt5 import QtCore
from PyQt5.QtGui import QBrush, QColor, QPainter, QPixmap, QValidator, QRegExpValidator, QPalette, QFont
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from pymavlink import mavutil
from serial import SerialException
from xml.dom import minidom
#import netifaces


VALUES_COUNT = 20

ID_COLUMN_NUMBER = 1
VALUES_COLUMN_NUMBER = 2
DEFAULT_COLUMN_NUMBER = 3
RANGE_COLUMN_NUMBER = 4
DESCRIPTION_COLUMN_NUMBER = 5

COMMAND_REQUEST_LIST = "REQUEST_LIST"
COMMAND_PARAM_SET = "PARAM_SET"
SYSTEM_ID = 1
TARGET_COMPONENT_ID = 191
SELF_COMPONENT_ID = 25 # master.mav.MAV_COMP_ID_USER1
MAVLINK_MESSAGE_ID_PARAM_VALUE = 22
MAVLINK_MESSAGE_ID_STATUSTEXT = 253
STATUS_TEXT_SAVED = "SAVED TO EEPROM"
bitmask_dict = {}
edited_cell = None
edited_cell_row_number = -1
edited_cell_is_valid = True
edited_cell_saved_value = ""
xml_file = None

SETTINGS_FILE_NAME = "settings.txt"
SAVE_FILE_NAME = "saved_parameters.xml"

param_types = {
    "MAV_PARAM_TYPE_UINT8":     1,
    "MAV_PARAM_TYPE_INT8":      2,
    "MAV_PARAM_TYPE_UINT16":    3,
    "MAV_PARAM_TYPE_INT16":     4,
    "MAV_PARAM_TYPE_UINT32":    5,
    "MAV_PARAM_TYPE_INT32":     6,
    "MAV_PARAM_TYPE_UINT64":    7,
    "MAV_PARAM_TYPE_INT64":     8,
    "MAV_PARAM_TYPE_REAL32":    9,
    "MAV_PARAM_TYPE_REAL64":    10
}


class MyMavMesage():
    def __init__(self, param_id, param_value, param_type, param_count, param_index):
        self.param_id = param_id
        self.param_value = param_value
        self.param_type = param_type
        self.param_count = param_count
        self.param_index = param_index


class BitsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        bits_path = "src/bits.ui"
        if getattr(sys, 'frozen', False):
            # in case of run as one exe
            bits_path = os.path.join(sys._MEIPASS, ('' + bits_path))
        uic.loadUi(bits_path, self)

        frame_widget = self.findChild(QFrame, 'frameWidget')
        if frame_widget:
            frame_widget.setLineWidth(2)

        self.setGeometry(0, 0, 400, 300)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

    def on_button_click(self):
        print("Button clicked!")


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        form_path = "src/form_07.ui"
        if getattr(sys, 'frozen', False):
            # in case of run as one exe
            form_path = os.path.join(sys._MEIPASS, ('' + form_path))
        uic.loadUi(form_path, self)

        self.getPushButton.clicked.connect(self.getPushButton_clicked)
        self.setPushButton.clicked.connect(self.setPushButton_clicked)
        self.setDefaultPushButton.clicked.connect(self.setDefaultPushButton_clicked)

        self.is_changed_numbers_set = set()

        self.bits_widget = BitsWidget(self)
        self.bits_widget.move(100, 200)
        self.bits_widget.hide()

        self.bits_show_button = QPushButton(self)
        self.bits_show_button.setText("Edit Bits")
        self.bits_show_button.setStyleSheet("background-color: rgb(0, 150, 0);")
        self.bits_show_button.clicked.connect(self.bits_show_button_clicked)
        self.bits_show_button.move(200, 300)
        self.bits_show_button.hide()

        self.tableWidget.setStyleSheet("""
            QTableWidget::item {padding-left: 10px; padding-right: 10px; border: 1px}
            """)

        # self.tableWidget.setStyleSheet("""
        #             QTableWidget::item {margin: 20px; border: 1px}
        #             """)
        self.tableWidget.horizontalHeader().setStyleSheet("""
            QHeaderView::section {padding: 10px; border: 1px}
            """)

        self.resizeToContent()

        # self.setItemColor(2, 3, QColor(250, 0, 0))
        # item = self.tableWidget.item(2, 3)
        # item.setForeground(QColor(50, 180, 100))

        self.tableWidget.cellClicked.connect(self.getClickedCell)
        # self.tableWidget.verticalScrollBar().valueChanged.connect(self.adjustSelectedMarks)

        self.tableWidget.horizontalHeader().sectionClicked.connect(self.horizontal_header_ckicked)

        delegate = ItemDelegate()
        self.tableWidget.setItemDelegate(delegate)
        self.tableWidget.itemChanged.connect(self.on_item_changed)

        # self.model = QStandardItemModel(self)
        # self.tableWidget.setModel(self.model)

        self.installEventFilter(self)

        # self.getValues()

        self.types_dict = {}
        self.sender_command = None
        self.master_in = None
        self.master_out = None
        self.device = ""
        self.baudrate = 115200
        self.is_connection_done = False
        self.last_connection_time_sec = 0
        self.interface_info = None
        self.current_interface_number = -1

        self.port_lineEdit.focusInEvent = self.focusInLineEdit
        regex = QtCore.QRegExp("[0-9]*")
        validator = QRegExpValidator(regex)
        self.port_lineEdit.setValidator(validator)
        self.port_lineEdit.setText("19856")

        self.update_device_list()
        self.refreshButton.clicked.connect(self.refreshButton_clicked)
        # self.port_comboBox.view().installEventFilter(self)
        # self.port_comboBox.view().entered.connect(self.on_port_comboBox_activated)
        # self.port_comboBox.activated.connect(self.on_combobox_activated)
        #self.port_comboBox.activated.connect(self.on_port_comboBox_activated)
        self.start_tasks()

        self.label_saved_state = False
        self.set_label_saved_state(False)

        self.remember_device = ""
        self.remember_baudrate = ""
        self.restore_from_settings()

        self.save_pushButton.clicked.connect(self.saveButton_clicked)
        self.load_pushButton.clicked.connect(self.loadButton_clicked)
        self.setWindowTitle("Configurator")

        self.tableWidget.setStyleSheet("QTableWidget { font-size: 12pt; }") 
        self.tableWidget.horizontalHeader().setStyleSheet("QHeaderView::section { font-size: 12pt; }") 
        self.tableWidget.verticalHeader().setStyleSheet("QHeaderView::section { font-size: 12pt; }")

    def focusInLineEdit(self, event):
        #self.port_lineEdit.setText("")
        event.accept()
    def update_GUI_by_UDP(self):
        if self.device == "UDP":
            self.baud_comboBox.hide()
            self.port_lineEdit.show()
        else:
            self.baud_comboBox.show()
            self.port_lineEdit.hide()

    def saveButton_clicked(self):
        doc = minidom.Document()

        params = doc.createElement("Params")
        doc.appendChild(params)

        arduPlane = doc.createElement("ArduPlane")
        params.appendChild(arduPlane)

        rowCount = self.tableWidget.rowCount()
        for r in range(rowCount):
            id_str = str(self.tableWidget.item(r, ID_COLUMN_NUMBER).text())
            id = doc.createElement(id_str)
            arduPlane.appendChild(id)
            displayName = doc.createElement("DisplayName")
            id.appendChild(displayName)
            is_described = self.is_in_parameters_xml(id_str)
            description = doc.createElement("Description")
            id.appendChild(description)
            if is_described:
                description_str = str(self.tableWidget.item(r, DESCRIPTION_COLUMN_NUMBER).text())
            else:
                description_str = ""
            description_text = doc.createCDATASection(description_str)
            description.appendChild(description_text)
            range_ = doc.createElement("Range")
            id.appendChild(range_)
            if is_described:
                range_str = str(self.tableWidget.item(r, RANGE_COLUMN_NUMBER).text())
            else:
                range_str = "-1000000.00 1000000.00"
            range_text = doc.createTextNode(range_str)
            range_.appendChild(range_text)
            user = doc.createElement("User")
            id.appendChild(user)
            user_text = doc.createTextNode("Standard")
            user.appendChild(user_text)
            default = doc.createElement("Default")
            id.appendChild(default)
            if is_described:
                default_str = str(self.tableWidget.item(r, DEFAULT_COLUMN_NUMBER).text())
            else:
                default_str = "0.00"
            default_text = doc.createTextNode(default_str)
            default.appendChild(default_text)
            value = doc.createElement("Value")
            id.appendChild(value)
            value_str = str(self.tableWidget.item(r, VALUES_COLUMN_NUMBER).text())
            value_text = doc.createTextNode(value_str)
            value.appendChild(value_text)

            # Step
            step = doc.createElement("Step")
            id.appendChild(step)
            if is_described:
                step_str = self.get_from_parameters_xml(id_str, "Step")
            else:
                step_str = "0.01"
            step_text = doc.createTextNode(step_str)
            step.appendChild(step_text)
            # Index
            index = doc.createElement("Index")
            id.appendChild(index)
            index_str = str(r)
            index_text = doc.createTextNode(index_str)
            index.appendChild(index_text)
            # Type
            type = doc.createElement("Type")
            id.appendChild(type)
            type_int = self.types_dict[id_str]
            type_str = self.get_type_neme(type_int)
            type_text = doc.createTextNode(type_str)
            type.appendChild(type_text)

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,
                                                            "Save File", "", "XML Files(*.xml);;All Files(*)",
                                                            options=options)
        if fileName:
            if not str(fileName).endswith('.xml'):
                fileName = str(fileName) + '.xml'
            xml_str = doc.toprettyxml(indent="    ")
            with open(fileName, "w", encoding="utf-8") as file:
                file.write(xml_str)

            print(f"XML file saved successfully as {fileName}")

    def get_type_neme(self, type_int):
        for key, val in param_types.items():
            if val == type_int:
                return key

        return "MAV_PARAM_TYPE_REAL32"

    def is_in_parameters_xml(self, id_str):
        elements = xml_file.getElementsByTagName(id_str)

        if len(elements) > 0:
            return True
        else:
            return  False

    def get_from_parameters_xml(self, id_str, field_str):
        elements = xml_file.getElementsByTagName(id_str)

        if len(elements) > 0:
            parameter_xml = elements[0]
            fields = parameter_xml.getElementsByTagName(field_str)
            if len(fields) > 0:
                val_str = fields[0].firstChild.data
                return val_str

        return ""

    def loadButton_clicked(self):
        self.removeAllRows()
        self.is_changed_numbers_set = set()
        changed_set = set()
        self.tableWidgetUpdate()

        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self,
                                                      "Load File", "", "XML Files(*.xml);;All Files(*)",
                                                      options=options)
            if fileName:
                saved_xml_file = minidom.parse(fileName)
                arduPlane_list =  saved_xml_file.getElementsByTagName("ArduPlane")
                if len(arduPlane_list) > 0:
                    arduPlane = arduPlane_list[0]
                    # id_list = arduPlane.getElementsByTagName("*")
                    index = 0
                    # for id in id_list:
                    for id in arduPlane.childNodes:
                        if id.nodeType == minidom.Node.ELEMENT_NODE:
                            param_id = id.tagName
                            param_value = float(id.getElementsByTagName("Value")[0].firstChild.data)
                            param_type = param_types[id.getElementsByTagName("Type")[0].firstChild.data]
                            param_count = 100500 #len(id_list)
                            param_index = index
                            #self.is_changed_numbers_set.add(int(index))
                            changed_set.add(int(index))
                            index += 1

                            m = MyMavMesage(param_id, param_value, param_type, param_count, param_index)
                            self.get_data_from_mavlink_message(m)

                    self.is_changed_numbers_set.update(changed_set)
                    self.tableWidgetUpdate()
                    print(f"XML file loaded successfully from {SAVE_FILE_NAME}")
        except Exception as e:
            print(f"Loading exeption: {e}")

    def remember_settings(self, device, baudrate):
        self.remember_device = device
        self.remember_baudrate = baudrate

    def save_settings(self):
        device = self.remember_device
        baudrate = self.remember_baudrate

        if len(str(device)) > 0 and len(str(baudrate)) > 0:
            settings_file = open(SETTINGS_FILE_NAME, "w")
            settings_file.write(str(device) + "\n")
            settings_file.write(str(baudrate) + "\n")

            if str(device) == "UDP":
                settings_file.write(str(self.master_in_str) + "\n")
                settings_file.write(str(self.master_out_str) + "\n")
                settings_file.write(str(self.port_lineEdit.text()) + "\n")

            settings_file.close()

            self.remember_device, self.remember_baudrate = "", ""


    def load_settings(self):
        device, baudrate, udpin, udpout, port = "", "", "", "", ""
        try:
            settings_file = open(SETTINGS_FILE_NAME, "r")
            device = settings_file.readline().strip()
            baudrate = settings_file.readline().strip()
            if device == "UDP":
                udpin = settings_file.readline().strip()
                udpout = settings_file.readline().strip()
                port = settings_file.readline().strip()
            settings_file.close()
        except OSError:
            print("Could not open settings file: " + str(SETTINGS_FILE_NAME))
        return (device, baudrate, udpin, udpout, port)

    def restore_from_settings(self):
        device, baudrate, udpin, udpout, port = self.load_settings()
        device = str(device)
        baudrate = str(baudrate)

        # self.port_comboBox.setCurrentIndex(0)
        list_len = self.port_comboBox.count()
        if list_len > 0:
            for i in range(list_len):
                stripped_device_name = self.strip_port(self.port_comboBox.itemText(i))
                if stripped_device_name.startswith(device):
                    self.port_comboBox.setCurrentIndex(i)


        list_len = self.baud_comboBox.count()
        if list_len > 0:
            for i in range(list_len):
                if str(self.baud_comboBox.itemText(i)).startswith(baudrate):
                    self.baud_comboBox.setCurrentIndex(i)

        if port != "":
            self.port_lineEdit.setText(port)

    def strip_port(self, port_name):
        port_name = str(port_name)
        open_br_position = port_name.find("(")
        close_br_position = port_name.find(")")
        if open_br_position > 0:
            port_name = port_name[open_br_position + 1: close_br_position]
        return port_name

    def refreshButton_clicked(self):
        self.update_device_list()

    # def on_port_comboBox_activated(self, index):
    #     self.update_device_list()

    def reset_label_saved_state(self, state):
        if state is None:
            return
        self.label_saved_state = state
        self.set_label_saved_state(state)

    def set_label_saved_state(self, state):
        if self.label_saved_state is None:
            # wait for reset
            return
        self.label_saved_state = state
        if state is None:
            self.statusLabel.setText("Waiting...")
            self.statusLabel.setStyleSheet("color: red;")
            return
        if state is True:
            self.statusLabel.setText("Saved     ")
            self.statusLabel.setStyleSheet("color: green;")
            return
        if state is False:
            self.statusLabel.setText("Changed   ")
            self.statusLabel.setStyleSheet("color: grey;")
        return

    def update_device_list(self):
        print("update_device_list")
        self.port_comboBox.clear()
        placeholder_text = "Select the Device"
        self.port_comboBox.addItem(placeholder_text)
        self.port_comboBox.setCurrentIndex(0)

        device_list = self.get_device_list()
        for device in device_list:
            self.port_comboBox.addItem(device)

        self.port_comboBox.addItem("UDP")

    def get_device_list(self):
        platform_str = str(sys.platform)
        pors = []
        if platform_str.startswith("linux"):
            ports = glob.glob('/dev/tty[A-Za-z]*')
            comports = serial.tools.list_ports.comports()
            # print(comports)
            ports = []
            for port in comports:
                ports.append(port.description + " (" + port.device + ")")
        elif platform_str.startswith("win"):
            # import serial.tools.list_ports;
            comports = serial.tools.list_ports.comports()
            # print(comports)
            # ports = ['COM%s' % (i + 1) for i in range(256)]
            ports = []
            for port in comports:
                ports.append(port.description)
        return ports

    def start_tasks(self):
        self.connect_timer = QtCore.QTimer(self)
        self.connect_timer.timeout.connect(self.connect_routine)
        self.connect_timer.start(500)

        self.sender_timer = QtCore.QTimer(self)
        self.sender_timer.timeout.connect(self.sender_routine)
        self.sender_timer.start(10)

        self.receaver_timer = QtCore.QTimer(self)
        self.receaver_timer.timeout.connect(self.receaver_routine)
        self.receaver_timer.start(10)

    def horizontal_header_ckicked(self):
        self.bits_show_button.hide()
        self.bits_widget.hide()
        self.postvalidateEdited()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.bits_show_button.hide()
            self.bits_widget.hide()
            self.postvalidateEdited()
        if obj == self.port_comboBox.view():
            if event.type() == event.Show:
                # print("ComboBox opened")
                pass
                # self.update_device_list()
        return super().eventFilter(obj, event)

    def resizeToContent(self):
        header = self.tableWidget.horizontalHeader()
        # self.tableWidget.resizeColumnsToContents()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.tableWidget.verticalHeader().setVisible(False)

    def removeAllRows(self):
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)

    # def getValues(self):
    #     global bitmask_dict
    #
    #     self.removeAllRows()
    #
    #     for row_n in range(20):
    #         row_position = self.tableWidget.rowCount()
    #         self.tableWidget.insertRow(row_position)
    #         #row_n = 0
    #         self.tableWidget.setItem(row_n, 0, QTableWidgetItem(str(row_n)))
    #         self.tableWidget.setItem(row_n, 1, QTableWidgetItem(f"Value_{row_n}"))
    #         self.tableWidget.setItem(row_n, 2, QTableWidgetItem(str(row_n)))
    #         self.tableWidget.setItem(row_n, 3, QTableWidgetItem(f"1{row_n}"))
    #         if row_n % 2 == 0:
    #             self.tableWidget.setItem(row_n, 4, QTableWidgetItem("-100 100"))
    #         else:
    #             self.tableWidget.setItem(row_n, 4, QTableWidgetItem("-100.00 100.00"))
    #         self.tableWidget.setItem(row_n, 5, QTableWidgetItem("Description kdfisoo duiasioshf ujsdfhjsh  sidfsd  sdiijfidsj sijfisi."))
    #
    #     self.tableWidget.itemChanged.connect(self.on_item_changed)
    #
    #     rows_count = self.tableWidget.rowCount()
    #     for row in range(0, rows_count):
    #         item = self.tableWidget.item(row, 0)
    #         if item is None:
    #             break
    #         item.setFlags(QtCore.Qt.ItemIsEnabled)
    #         item = self.tableWidget.item(row, 1)
    #         item.setFlags(QtCore.Qt.ItemIsEnabled)
    #         # item = self.tableWidget.item(row, 2)
    #         item.setFlags(QtCore.Qt.ItemIsEnabled)
    #         item = self.tableWidget.item(row, 3)
    #         item.setFlags(QtCore.Qt.ItemIsEnabled)
    #         item = self.tableWidget.item(row, 4)
    #         item.setFlags(QtCore.Qt.ItemIsEnabled)
    #         item = self.tableWidget.item(row, 5)
    #         item.setFlags(QtCore.Qt.ItemIsEnabled)
    #
    #     self.is_changed_numbers_set = set()
    #     bitmask_dict[6] = "0:weeer, 1:sdsds, 2:ddd sdff, 3:dfdf, 4:dgff dfd, 5:dfd ddsd sfs"
    #     bitmask_dict[7] = "0:weeer, 1:sdsds, 2:ddd sdff, 3:dfdf, 4:dgff dfd, 5:dfd ddsd sfs, 6:ksis"
    #     bitmask_dict[8] = "0:weeer, 1:sdsds, 2:ddd sdff, 3:dfdf, 4:dgff dfd, 5:dfd ddsd sfs, 6:ksis, 7:ddii sdidj is"
    #
    #     self.resizeToContent()
    #     self.set_sizes()

    def on_data_changed(self, topLeft, bottomRight):
        # Получаем измененное значение ячейки
        changed_item = self.model.itemFromIndex(topLeft)
        new_value = changed_item.text()

        row = topLeft.row()
        column = topLeft.column()

        print(f"Changed ({row}, {column}): {new_value}")

    def on_item_changed(self, item):
        self.postvalidateEdited()

        row = item.row()
        column = item.column()
        new_value = item.text()

        print(f"Changed ({row}, {column}): {new_value}")

        self.is_changed_numbers_set.add(row)
        self.set_label_saved_state(False)

    def resizeEvent(self, event):
        #print("resize")
        # self.adjustSelectedMarks()
        self.set_sizes()

        self.bits_show_button.hide()
        self.bits_widget.hide()
        self.postvalidateEdited()

    def scrolled(self, value):
        print(f"scrolled to {value}")

    def postvalidateEdited(self):
        global edited_cell
        global edited_cell_is_valid
        global edited_cell_saved_value

        print("postvalidateEdited")
        if not edited_cell_is_valid:
            if edited_cell is not None:
                edited_cell.setText(str(edited_cell_saved_value))
                print(f"post set to saved = {edited_cell_saved_value}")
                edited_cell = None

    def getClickedCell(self, row, column):
        global edited_cell
        global edited_cell_row_number

        print('clicked!', row, column)

        # if edited_cell is None:
        #     edited_cell = self.tableWidget.item(row, column)
        #     print(f"set edited_cell to {edited_cell}")

        self.bits_show_button.hide()
        self.bits_widget.hide()
        self.postvalidateEdited()

        if row in bitmask_dict.keys() and column == VALUES_COLUMN_NUMBER:
            item = self.tableWidget.item(row, column)
            edited_cell = item
            edited_cell_row_number = row
            cell_rect = self.tableWidget.visualItemRect(item)
            header_height = self.tableWidget.horizontalHeader().height()
            button_height = self.bits_show_button.height()
            print(f"tableWidget.x() = {self.tableWidget.x()}")
            print(f"tableWidget.y() = {self.tableWidget.y()}")
            print(f"cell_rect = {cell_rect}")
            bits_show_button_x = self.tableWidget.x() + cell_rect.x() + cell_rect.width() + 10
            bits_show_button_y = self.tableWidget.y() + header_height + cell_rect.y() + cell_rect.height() // 2 - button_height // 2
            self.bits_show_button.move(bits_show_button_x, bits_show_button_y)
            self.bits_show_button.show()

    def getPushButton_clicked(self):
        print('getPushButton_clicked')
        self.sender_command = COMMAND_REQUEST_LIST

    def setPushButton_clicked(self):
        print('setPushButton_clicked')
        self.sender_command = COMMAND_PARAM_SET
        self.set_label_saved_state(None)

    def setDefaultPushButton_clicked(self):
        print('setDefaultPushButton_clicked')
        self.bits_show_button.hide()
        self.bits_widget.hide()

        rowCount = self.tableWidget.rowCount()
        for r in range(rowCount):
            default_str = str(self.tableWidget.item(r, DEFAULT_COLUMN_NUMBER).text())
            old_value_str = self.tableWidget.item(r, VALUES_COLUMN_NUMBER).text()
            self.tableWidget.item(r, VALUES_COLUMN_NUMBER).setText(default_str)
            if float(old_value_str) != float(default_str):
                self.is_changed_numbers_set.add(r)
            else:
                if r in self.is_changed_numbers_set:
                    self.is_changed_numbers_set.remove(r)
            self.tableWidget.update()

    def bits_show_button_clicked(self):
        self.bits_show_button.hide()

        header_height = self.tableWidget.horizontalHeader().height()
        bits_widget_x = self.tableWidget.x() + self.tableWidget.width() // 2 - self.bits_widget.width() // 2
        bits_widget_y = self.tableWidget.y() + self.tableWidget.height() // 2 - self.bits_widget.height() // 2 + header_height // 2
        self.bits_widget.move(bits_widget_x, bits_widget_y)

        edited_value = int(edited_cell.text())
        self.bits_widget.bits_value_label.setText(str(edited_value))
        val = edited_value
        bit_0 = val % 2
        val = val // 2
        bit_1 = val % 2
        val = val // 2
        bit_2 = val % 2
        val = val // 2
        bit_3 = val % 2
        val = val // 2
        bit_4 = val % 2
        val = val // 2
        bit_5 = val % 2
        val = val // 2
        bit_6 = val % 2
        val = val // 2
        bit_7 = val % 2

        self.bits_widget.bit_checkBox_0.setChecked(bit_0 > 0)
        self.bits_widget.bit_checkBox_1.setChecked(bit_1 > 0)
        self.bits_widget.bit_checkBox_2.setChecked(bit_2 > 0)
        self.bits_widget.bit_checkBox_3.setChecked(bit_3 > 0)
        self.bits_widget.bit_checkBox_4.setChecked(bit_4 > 0)
        self.bits_widget.bit_checkBox_5.setChecked(bit_5 > 0)
        self.bits_widget.bit_checkBox_6.setChecked(bit_6 > 0)
        self.bits_widget.bit_checkBox_7.setChecked(bit_7 > 0)

        bitmask_str = bitmask_dict[edited_cell_row_number]
        bitmask_str_list = bitmask_str.split(', ')

        num = 0
        checkbox = self.bits_widget.bit_checkBox_0
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 1
        checkbox = self.bits_widget.bit_checkBox_1
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 2
        checkbox = self.bits_widget.bit_checkBox_2
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 3
        checkbox = self.bits_widget.bit_checkBox_3
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 4
        checkbox = self.bits_widget.bit_checkBox_4
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 5
        checkbox = self.bits_widget.bit_checkBox_5
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 6
        checkbox = self.bits_widget.bit_checkBox_6
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        num = 7
        checkbox = self.bits_widget.bit_checkBox_7
        checkbox.stateChanged.connect(
            lambda state, checkbox=checkbox, num=num: self.bit_checkBox_clicked(state, checkbox, num))
        if len(bitmask_str_list) > num:
            checkbox.setCheckable(True)
            checkbox.setStyleSheet("color: black;")
            checkbox.setText(bitmask_str_list[num])
        else:
            checkbox.setCheckable(False)
            checkbox.setStyleSheet("color: grey;")
            checkbox.setText('__(not used)__')

        self.bits_widget.show()

    def bit_checkBox_clicked(self, state, checkbox, bit_number):
        global edited_cell

        #print(f"bit_number = {bit_number}, state = {state}")

        chb = self.bits_widget.bit_checkBox_0
        val_0 = 2 ** 0 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_1
        val_1 = 2 ** 1 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_2
        val_2 = 2 ** 2 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_3
        val_3 = 2 ** 3 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_4
        val_4 = 2 ** 4 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_5
        val_5 = 2 ** 5 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_6
        val_6 = 2 ** 6 if chb.isChecked() else 0

        chb = self.bits_widget.bit_checkBox_7
        val_7 = 2 ** 7 if chb.isChecked() else 0

        new_val = val_0 + val_1 + val_2 + val_3 + val_4 + val_5 + val_6 + val_7
        edited_cell.setText(str(new_val))
        self.bits_widget.bits_value_label.setText(str(new_val))

    def set_sizes(self):
        self.tableWidget.resizeRowsToContents()

    def setItemColor(self, row, col, color):
        item = self.tableWidget.item(row, col)
        item.setData(QtCore.Qt.BackgroundRole, color)

    # def adjustSelectedMarks(self):
    #     print("adjust")
    #     vheader = self.tableWidget.verticalHeader()
    #     print(vheader)

    def strip_port(self, port_name):
        port_name = str(port_name)
        open_br_position = port_name.find("(")
        close_br_position = port_name.find(")")
        if open_br_position > 0:
            port_name = port_name[open_br_position + 1: close_br_position]
        return port_name

    def connect_routine(self):
        selected_device_str = self.port_comboBox.currentText()
        selected_device = self.strip_port(selected_device_str)
        selected_baudrate = self.baud_comboBox.currentText()

        self.update_GUI_by_UDP()

        is_trying_UDP = False
        if (self.device == "UDP" and not self.is_connection_done):
            is_trying_UDP = True

        if (self.device != selected_device or
                self.baudrate != selected_baudrate or
                #self.master_in is None or
                is_trying_UDP):
            if selected_device == "UDP":
                self.is_connection_done = False
                self.interface_info = get_interface_info()
                #self.current_interface_number = -1

            connection_timeout_sec = 0.5
            now_time_sec = time.time()
            if is_trying_UDP:
                if now_time_sec > self.last_connection_time_sec + connection_timeout_sec:
                    try:
                        self.removeAllRows()

                        self.last_connection_time_sec = now_time_sec
                        self.current_interface_number = self.current_interface_number + 1
                        if self.current_interface_number >= len(self.interface_info):
                            self.current_interface_number = 0
                        # interface_values = self.interface_info.values()
                        # current_interface_value = list(interface_values)[self.current_interface_number]
                        # udpin = current_interface_value["ip"]
                        # udpout = current_interface_value["gateway"]
                        if (self.interface_info is None or
                            self.current_interface_number < 0 or
                            self.current_interface_number >= len(self.interface_info)):
                            current_interface = None
                        else:
                            current_interface = self.interface_info[self.current_interface_number]
                        udpin = "_None_"
                        if "IP" in current_interface.keys():
                            udpin = current_interface["IP"]
                        udpout = "_None_"
                        if "Gateway" in current_interface.keys():
                            udpout = current_interface["Gateway"]
                        port = int(self.port_lineEdit.text())
                        # new_master_in = mavutil.mavlink_connection("udpin:192.168.144.20:19856")
                        # new_master_out = mavutil.mavlink_connection("udpout:192.168.144.12:19856")
                        self.master_in_str = "udpin:" + udpin + ":" + str(port) #":19856"
                        self.master_out_str = "udpout:" + udpout + ":" + str(port) #":19856"
                        new_master_in = mavutil.mavlink_connection(self.master_in_str)
                        new_master_out = mavutil.mavlink_connection(self.master_out_str)
                    except SerialException:
                        print(f"! Can not connect to: {self.master_in_str}")
                    except Exception as e:
                        print(f"During connection to: {self.master_in_str}")
                        print(f"Connection exeption: {type(e).__name__}")
                        print(f"Exeption args: {e.args}")
                    else:
                        #self.removeAllRows()
                        # await asyncio.sleep(CONNECT_PERIOD_S)
                        self.master_in = new_master_in
                        self.master_out = new_master_out
                        print(f"Connected to in: {self.master_in_str}")
                        print(f"Connected to out: {self.master_out_str}")
                        # self.device = selected_device
                        # self.baudrate = selected_baudrate
                        self.remember_settings(selected_device, selected_baudrate)
                        # is_connected = True

                        self.getPushButton_clicked()

            else: # if is_trying_UDP:

                if self.master_in is not None:
                    self.master_in.close()
                    self.master_in = None

                if self.master_out is not None:
                    self.master_out.close()
                    self.master_out = None

                try:
                    self.removeAllRows()

                    # selected_device = str(app.combo_device.get())  # in case of change device meanwhile
                    # selected_device = strip_port(selected_device)
                    # selected_baudrate = int(app.combo_baud.get())  # in case of change baud meanwhile
                    new_master_in = mavutil.mavlink_connection(selected_device, selected_baudrate)
                except SerialException:
                    print(f"! Can not connect to: {selected_device} at {selected_baudrate}")
                except Exception as e:
                    print(f"During connection to: {selected_device} at {selected_baudrate}")
                    print(f"Connection exeption: {type(e).__name__}")
                    print(f"Exeption args: {e.args}")
                else:
                    # self.removeAllRows()
                    # await asyncio.sleep(CONNECT_PERIOD_S)
                    self.master_in = new_master_in
                    self.master_out = self.master_in
                    print(f"Connected to in/out: {selected_device} at {selected_baudrate}")
                    # self.device = selected_device
                    # self.baudrate = selected_baudrate
                    self.remember_settings(selected_device, selected_baudrate)
                    # is_connected = True

                    self.getPushButton_clicked()

        self.device = selected_device
        self.baudrate = selected_baudrate

    def sender_routine(self):
        target_system = SYSTEM_ID
        target_component = TARGET_COMPONENT_ID

        if self.master_out is None:
            return

        self.master_out.mav.srcComponent = SELF_COMPONENT_ID

        if self.sender_command is not None:
            if str(self.sender_command).startswith(COMMAND_REQUEST_LIST):
                self.sender_command = None
                self.removeAllRows()

                self.master_out.mav.param_request_list_send(target_system, target_component)
                print(f"_________________<< param_request_list_send(target_system={target_system}, target_component={target_component})")

            if str(self.sender_command).startswith(COMMAND_PARAM_SET):
                self.sender_command = None
                for changed_number in self.is_changed_numbers_set:
                    changed_item = ex.tableWidget.item(changed_number, VALUES_COLUMN_NUMBER)
                    param_value = float(changed_item.text())
                    param_id_item = ex.tableWidget.item(changed_number, ID_COLUMN_NUMBER)
                    param_id = param_id_item.text()
                    param_id_bytes = str.encode(param_id)
                    # For undescribed parameters (if hes not describe in the file "parameters.xml"):
                    # set defaul param tipe -  MAV_PARAM_TYPE_REAL32 = 9
                    param_type_int = 9
                    if param_id in self.types_dict.keys():
                        param_type_int = self.types_dict[param_id]

                    self.master_out.mav.srcComponent = SELF_COMPONENT_ID
                    self.master_out.mav.param_set_send(target_system, target_component, param_id_bytes, param_value,
                                              param_type_int)
                    print(
                        f"_________________<< param_set_send(target_system={target_system}, target_component={target_component}, param_id={param_id}, param_value={param_value}, param_type_int={param_type_int})")
                    time.sleep(0.1)

                self.is_changed_numbers_set = set()
                self.tableWidgetUpdate()
                #self.tableWidget.repaint()

    def tableWidgetUpdate(self):
        self.tableWidget.setFocus()
        return
        # item = self.tableWidget.item(1, VALUES_COLUMN_NUMBER)
        # item_text = item.text()
        # item.setText("")
        # self.tableWidget.update()
        # item.setText(item_text)
        # self.tableWidget.update()

    def receaver_routine(self):
        if self.master_in is None:
            return

        try:
            m = self.master_in.recv_msg()
            #while self.master.port.inWaiting() > 0:
            if m is not None:
                # recv_msg will try parsing the serial port buffer
                # and return a new message if available
                #m = self.master.recv_msg()
                #m = self.master.

                #if m is None: break  # No new message

                m_src_id = m.get_srcComponent()
                # print(f">> id = {m.id} from {m_src_id}")
                # print(str(m))
                if m_src_id == TARGET_COMPONENT_ID:
                    print(f">> id = {m.id} from {m_src_id}")
                    # print(str(m))
                    if m.id == MAVLINK_MESSAGE_ID_PARAM_VALUE:
                        print("MAVLINK_MESSAGE_ID_PARAM_VALUE")
                        self.is_connection_done = True
                        self.get_data_from_mavlink_message(m)
                        self.save_settings()  # save connection settings after data receive
                    if m.id == MAVLINK_MESSAGE_ID_STATUSTEXT or m.id == 0:
                        #print("MAVLINK_MESSAGE_ID_STATUSTEXT")
                        self.handle_statustext(m)
        except Exception as e:
            print("Exception in receaver:")
            print(e)

    def get_data_from_mavlink_message(self, m):
        global bitmask_dict

        param_id = m.param_id
        param_value = m.param_value
        param_type = m.param_type
        param_count = m.param_count
        param_index = m.param_index

        self.types_dict[param_id] = param_type

        if len(param_id) == 0:
            return

        # MAV_PARAM_TYPE_REAL32 = 9
        # MAV_PARAM_TYPE_REAL64 = 10
        reals = (9, 10)
        if m.param_type not in reals:
            param_value = math.trunc(param_value)

        index_str = str(param_index)
        id_str = str(param_id)
        value_str = str(param_value)
        elements = xml_file.getElementsByTagName(id_str)

        if len(elements) > 0:
            parameter_xml = elements[0]
            default_str = parameter_xml.getElementsByTagName('Default')[0].firstChild.data
            range_str = parameter_xml.getElementsByTagName('Range')[0].firstChild.data
            description_str = parameter_xml.getElementsByTagName('Description')[0].firstChild.data
        else:
            if m.param_type in reals:
                default_str = "0.00"
                range_str = "-1000000.00 1000000.00"
                description_str = ""
            else:
                default_str = "0"
                range_str = "-1000000 1000000"
                description_str = ""

        min_str = str(range_str).split(" ")[0]
        dot_position = min_str.find(".")
        if dot_position > 0:
            decimal_nums_count = len(min_str) - dot_position - 1
            param_value_rounded = round(param_value, decimal_nums_count)
            value_str = str(param_value_rounded)
            while (len(value_str) - value_str.find(".")) < (len(min_str) - dot_position):
                value_str += "0"

        # row = (index_str, id_str, value_str, default_str, range_str, description_str)

        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)
        # row_n = 0
        self.tableWidget.setItem(row_position, 0, QTableWidgetItem(str(row_position)))
        self.tableWidget.setItem(row_position, 1, QTableWidgetItem(id_str))
        self.tableWidget.setItem(row_position, 2, QTableWidgetItem(value_str))
        self.tableWidget.setItem(row_position, 3, QTableWidgetItem(default_str))
        self.tableWidget.setItem(row_position, 4, QTableWidgetItem(range_str))
        self.tableWidget.setItem(row_position, 5, QTableWidgetItem(description_str))

        item = self.tableWidget.item(row_position, 0)
        if item is None:
            return
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item = self.tableWidget.item(row_position, 1)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        # item = self.tableWidget.item(row_position, 2)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item = self.tableWidget.item(row_position, 3)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item = self.tableWidget.item(row_position, 4)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item = self.tableWidget.item(row_position, 5)
        item.setFlags(QtCore.Qt.ItemIsEnabled)

        if row_position in self.is_changed_numbers_set:
            self.is_changed_numbers_set.remove(row_position)
        # bitmask_dict[row_position] = "0:weeer, 1:sdsds, 2:ddd sdff, 3:dfdf, 4:dgff dfd, 5:dfd ddsd sfs"
        elements = xml_file.getElementsByTagName(id_str)
        if len(elements) > 0:
            param_xml = elements[0]
            bitmask_xml = param_xml.getElementsByTagName("Bitmask")
            if len(bitmask_xml) > 0:
                self.is_bit_value = True
                bitmask_raw = bitmask_xml[0].firstChild.data
                bitmask_dict[row_position] = bitmask_raw
            else:
                if row_position in bitmask_dict.keys():
                    bitmask_dict.pop(row_position)

        self.set_label_saved_state(True)
        self.resizeToContent()
        self.set_sizes()

    def handle_statustext(self, m):
        fieldnames = m.get_fieldnames()
        if 'severity' in fieldnames and 'text' in fieldnames:
            text = m.text
            print(f"STATUSTEXT: {text}")
            if str(text).startswith(STATUS_TEXT_SAVED):
                self.reset_label_saved_state(True)


class ItemDelegate(QStyledItemDelegate):
    global edited_cell_is_valid
    global edited_cell_saved_value

    cellEditingStarted = QtCore.pyqtSignal(int, int)
    #saved_value = ''
    edited_cell_saved_value = ''
    range = ''
    #is_valid = True
    edited_cell_is_valid = True

    def createEditor(self, parent, option, index):
        global edited_cell
        global edited_cell_saved_value

        row = index.row()
        column = index.column()

        range_item = ex.tableWidget.item(row, RANGE_COLUMN_NUMBER)
        range_str = range_item.text()
        #print(range_str)
        self.range = range_str

        # result = super(ItemDelegate, self).createEditor(parent, option, index)
        # validator = QRegExpValidator(QtCore.QRegExp(r'[0-9]+'))
        # result.setValidator(validator)
        # if result:
        #     self.cellEditingStarted.emit(index.row(), index.column())
        # return result

        edited_cell = ex.tableWidget.item(row, column)
        #self.saved_value = ex.tableWidget.item(row, column).text()
        edited_cell_saved_value = edited_cell.text()
        print(f"createEditor for cell ({row}, {column})")

        editor = QLineEdit(parent)
        editor.textChanged.connect(self.validate_and_update_color)
        editor.editingFinished.connect(self.validate_and_save)
        return editor

    def validate_and_save(self):
        global edited_cell_is_valid
        global edited_cell_saved_value

        editor = self.sender()
        if editor:
            #if not self.is_valid:
            if not edited_cell_is_valid:
                #editor.setText(self.saved_value)
                editor.setText(edited_cell_saved_value)

    def validate_and_update_color(self, text):
        global edited_cell_is_valid

        editor = self.sender()
        if editor:
            try:
                #self.is_valid = False
                edited_cell_is_valid = False

                float_value = float(text)

                range_list = self.range.split(' ')
                range_min = float(range_list[0])
                range_max = float(range_list[1])

                if range_min <= float_value <= range_max:
                    #self.is_valid = True
                    edited_cell_is_valid = True

                dot_position = range_list[0].find('.')
                if dot_position < 0:
                    int_value = int(text)
                    if range_min <= int_value and int_value <= range_max:
                        #self.is_valid = True
                        edited_cell_is_valid = True

            except ValueError:
                #self.is_valid = False
                edited_cell_is_valid = False

            #if self.is_valid:
            if edited_cell_is_valid:
                editor.setStyleSheet("color: black;")
            else:
                editor.setStyleSheet("color: red;")

    def paint(self, painter, option, index):
        row = index.row()
        column = index.column()
        # padding
        # option.rect.adjust(10, 0, 0, 0)
        if column == VALUES_COLUMN_NUMBER:
            if row in ex.is_changed_numbers_set:
                painter.fillRect(option.rect, QColor(50, 180, 100))
            else:
                if row % 2 == 0:
                    painter.fillRect(option.rect, QColor(240, 240, 220))
                else:
                    painter.fillRect(option.rect, QColor(220, 220, 200))
        super().paint(painter, option, index)


def get_interface_info():
    # interface_info = {}
    # routes = netifaces.gateways()
    # for interface in netifaces.interfaces():
    #     try:
    #         addresses = netifaces.ifaddresses(interface)
    #         ip = addresses[netifaces.AF_INET][0]['addr']
    #         gateway = None
    #         for route in routes.get(netifaces.AF_INET, []):
    #             if route[1] == interface:
    #                 gateway = route[0]
    #                 break
    #         interface_info[interface] = {'ip': ip, 'gateway': gateway}
    #     except (KeyError, IndexError):
    #         pass
    # return interface_info

    interfaces = []

    platform_str = str(sys.platform)
    if platform_str.startswith("linux"):
        ip_route_output = subprocess.check_output(['ip', 'route', 'show'], universal_newlines=True)

        for line in ip_route_output.split('\n'):
            match = re.match(r'^default via (\S+) dev (\S+)', line)
            if match:
                gateway = match.group(1)
                interface = match.group(2)
                interfaces.append({'Interface': interface, 'Gateway': gateway})

        for interface_info in interfaces:
            interface = interface_info['Interface']
            try:
                ip_addr_output = subprocess.check_output(['ip', 'addr', 'show', interface], universal_newlines=True)
                for line in ip_addr_output.split('\n'):
                    if 'inet ' in line:
                        parts = line.strip().split()
                        ip = parts[1].split('/')[0]  # Извлекаем IP-адрес без маски
                        interface_info['IP'] = ip
                        break  # Переходим к следующему интерфейсу после того, как найден IP-адрес
            except subprocess.CalledProcessError:
                pass

        return interfaces

    elif platform_str.startswith("win"):
        ipconfig_output = subprocess.check_output(['ipconfig'], shell=True, universal_newlines=True)

        lines = ipconfig_output.split('\n')

        # interfaces = []
        current_interface = {}

        for line in lines:
            if 'adapter' in line.lower():
                # if current_interface:
                #     interfaces.append(current_interface)
                current_interface = {'Interface': line.split(':')[0].strip()}
            elif 'IPv4 Address' in line:
                current_interface['IP'] = line.split(':')[-1].strip()
            elif 'Default Gateway' in line:
                current_interface['Gateway'] = line.split(':')[-1].strip()

        if current_interface:
            if 'IP' in current_interface.keys() and 'Gateway' in current_interface.keys():
                interfaces.append(current_interface)

    # Example of output:
    # [{'Interface': 'Ethernet adapter Ethernet'},
    # {'Interface': 'Ethernet adapter Ethernet 2'},
    # {'Interface': 'Wireless LAN adapter Џ?¤Є«озҐ\xad\xadп зҐаҐ§ «®Є\xa0«м\xadг ¬ҐаҐ¦г* 11'},
    # {'Interface': 'Wireless LAN adapter Џ?¤Є«озҐ\xad\xadп зҐаҐ§ «®Є\xa0«м\xadг ¬ҐаҐ¦г* 12'},
    # {'Interface': 'Wireless LAN adapter Wi-Fi', 'IP': '192.168.144.20', 'Gateway': '192.168.144.12'},
    # {'Interface': 'Wireless LAN adapter Wi-Fi 2', 'IP': '192.168.88.80', 'Gateway': '192.168.88.1'}]

    return interfaces


if __name__ == '__main__':
    # parse an xml file by name
    if getattr(sys, 'frozen', False):
        # in case of run as one exe
        xml_file = minidom.parse(file=os.path.join(sys._MEIPASS, 'src/parameters.xml'))
    else:
        # xml_file = minidom.parse('../parameters.xml')
        xml_file = minidom.parse('../parameters.xml')

    app = QApplication(sys.argv)
    ex = App()
    ex.setStyleSheet("QWidget { font-size: 12pt; }") 

    ex.show()
    ex.set_sizes()
    sys.exit(app.exec())