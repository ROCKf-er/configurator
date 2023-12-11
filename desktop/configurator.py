import asyncio
import math
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tkinter.messagebox import showinfo
from argparse import ArgumentParser
from serial import SerialException
import serial.tools.list_ports
from pymavlink import mavutil
import time
from xml.dom import minidom
import os
import sys
import glob


IS_LOGS = True
IS_LOGS_FOR_DEBUG = True
IS_TEST_DATA_GENERATION = False

WIDTH = 1500
HEIGHT = 1500
# FONT_SIZE = 30
# FONT_SMALL_SIZE = 20
# FONT = "Areal 30"

xml_file = None

HEARTBEAT_TIMEOUT_S = 1

master = None
SYSTEM_ID = 1
TARGET_COMPONENT_ID = 191
SELF_COMPONENT_ID = 25 # master.mav.MAV_COMP_ID_USER1
CONNECT_PERIOD_S = 0.5
WAIT_BEFORE_FIRST_SEND_S = 3
MINIMAL_ASYNC_PAUSE_S = 0.01
SEND_ASYNC_PAUSE_S = 0.05
CHECK_GET_PAUSE_S = 0.5
MAVLINK_MESSAGE_ID_PARAM_VALUE = 22
MAVLINK_MESSAGE_ID_STATUSTEXT = 253

STATUS_TEXT_SAVED = "SAVED TO EEPROM"

# 0 based column numbers
ID_COLUMN_NUMBER = 1
VALUES_COLUMN_NUMBER = 2
DEFAULT_COLUMN_NUMBER = 3
RANGE_COLUMN_NUMBER = 4
DESCRIPTION_COLUMN_NUMBER = 5

HINT_TEX = "Double-click the Description cell to view the full text.   Double-click the Value cell to edit the value."

sender_command = None
COMMAND_REQUEST_LIST = "REQUEST_LIST"
COMMAND_PARAM_SET = "PARAM_SET"
param_to_set_list = []
# param_to_set_list = [
#     {
#         "param_id": "VALUE_ID",
#         "param_value": 0.0,
#     },
# ]
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
get_button_pressed_time_s = None
GET_BUTTON_PRESSED_TIMEOUT_S = 3


def strip_port(port_name):
    port_name = str(port_name)
    open_br_position = port_name.find("(")
    close_br_position = port_name.find(")")
    if open_br_position > 0:
        port_name = port_name[open_br_position + 1 : close_br_position]
    return port_name


async def connect():
    global master

    # parser = ArgumentParser(description=__doc__)
    #
    # parser.add_argument("--baudrate", type=int,
    #                     help="master port baud rate", default=115200)
    # parser.add_argument("--device", required=True, help="serial device")
    # args = parser.parse_args()
    #
    # ### MAV related code starts here ###
    #
    # is_connected = False
    # # create a mavlink serial instance
    # while not is_connected:
    #     try:
    #         master = mavutil.mavlink_connection(args.device, baud=args.baudrate)
    #     except SerialException:
    #         print(f"! Can not connect to: {args.device} at {args.baudrate}" )
    #     else:
    #         print(f"Connected to: {master.port} at {master.baud}")
    #         is_connected = True
    #     await asyncio.sleep(CONNECT_PERIOD_S)

    device = ""
    baudrate = 115200

    while True:
        selected_device = str(app.combo_device.get())
        selected_device = strip_port(selected_device)
        selected_baudrate = int(app.combo_baud.get())
        if device != selected_device or baudrate != selected_baudrate:
            if master is not None:
                master.close()
                master = None
            app.delete_all_data()

            is_connected = False
            # create a mavlink serial instance
            while not is_connected:
                try:
                    selected_device = str(app.combo_device.get()) # in case of change device meanwhile
                    selected_device = strip_port(selected_device)
                    selected_baudrate = int(app.combo_baud.get()) # in case of change baud meanwhile
                    new_master = mavutil.mavlink_connection(selected_device, selected_baudrate)
                except SerialException:
                    print(f"! Can not connect to: {selected_device} at {selected_baudrate}" )
                except Exception as e:
                    print(f"Connection exeption: {e}")
                else:
                    await asyncio.sleep(CONNECT_PERIOD_S)
                    master = new_master
                    print(f"Connected to: {master.port} at {master.baud}")
                    device = selected_device
                    baudrate = selected_baudrate
                    is_connected = True

                    app.button_get_press()
                await asyncio.sleep(CONNECT_PERIOD_S)

        await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)


async def receaver():
    global master

    while True:
        # Check for incoming data on the serial port and count
        # how many messages of each type have been received
        if not master is None:
            while master.port.inWaiting() > 0:
                # recv_msg will try parsing the serial port buffer
                # and return a new message if available
                m = master.recv_msg()

                if m is None: break  # No new message

                m_src_id = m.get_srcComponent()
                # print(f">> id = {m.id} from {m_src_id}")
                # print(str(m))
                if m_src_id == TARGET_COMPONENT_ID:
                    print(f">> id = {m.id} from {m_src_id}")
                    print(str(m))
                    if m.id == MAVLINK_MESSAGE_ID_PARAM_VALUE:
                        app.get_data_from_mavlink_message(m)
                    if m.id == MAVLINK_MESSAGE_ID_STATUSTEXT or m.id == 0:
                        app.handle_statustext(m)

                await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)

        await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)


async def sender():
    global master
    global sender_command
    global param_to_set_list
    global param_types

    #await asyncio.sleep(WAIT_BEFORE_FIRST_SEND_S)
    while master is None:
        await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)

    target_system = SYSTEM_ID
    target_component = TARGET_COMPONENT_ID
    master.mav.srcComponent = SELF_COMPONENT_ID

    while True:
        if sender_command is not None:
            if str(sender_command).startswith(COMMAND_REQUEST_LIST):
                sender_command = None
                app.delete_all_data()

                target_system = SYSTEM_ID
                target_component = TARGET_COMPONENT_ID
                master.mav.srcComponent = SELF_COMPONENT_ID
                master.mav.param_request_list_send(target_system, target_component)
                print(f"_________________<< param_request_list_send(target_system={target_system}, target_component={target_component})")

            if str(sender_command).startswith(COMMAND_PARAM_SET):
                sender_command = None

                for param_to_set in param_to_set_list:
                    param_id = param_to_set["param_id"]
                    param_id_bytes = str.encode(param_id)
                    param_value = float(param_to_set["param_value"])
                    parameter_xml = xml_file.getElementsByTagName(param_id)[0]
                    param_type = parameter_xml.getElementsByTagName('Type')[0].firstChild.data
                    param_type_int = param_types[param_type]
                    master.mav.srcComponent = SELF_COMPONENT_ID
                    master.mav.param_set_send(target_system, target_component, param_id_bytes, param_value, param_type_int)
                    print(f"_________________<< param_set_send(target_system={target_system}, target_component={target_component}, param_id={param_id}, param_value={param_value}, param_type={param_type})")
                    await asyncio.sleep(SEND_ASYNC_PAUSE_S)

                await asyncio.sleep(CHECK_GET_PAUSE_S)
                app.button_get_press()

        await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)


async def heartbeat():
    while True:
        if not master is None:
            custom_mode = 15  # /*<  A bitfield for use for autopilot-specific flags*/
            type = 1  # /*<  Vehicle or component type. For a flight controller component the vehicle type (quadrotor, helicopter, etc.). For other components the component type (e.g. camera, gimbal, etc.). This should be used in preference to component id for identifying the component type.*/
            autopilot = 3  # /*<  Autopilot type / class. Use MAV_AUTOPILOT_INVALID for components that are not flight controllers.*/
            base_mode = 217  # /*<  System mode bitmap.*/
            system_status = 4  # /*<  System status flag.*/
            mavlink_version = 2
            master.mav.heartbeat_send(type, autopilot, base_mode, custom_mode, system_status)
            print(f"_________________<< heartbeat_send(type={type}, autopilot={autopilot}, base_mode={base_mode}, custom_mode={custom_mode}, system_status={system_status})")

        await asyncio.sleep(HEARTBEAT_TIMEOUT_S)


async def main():
    if IS_LOGS_FOR_DEBUG:
        print("Run main")

    connect_task = asyncio.create_task(connect())
    receiver_task = asyncio.create_task(receaver())
    sender_task = asyncio.create_task(sender())
    heartbeat_task = asyncio.create_task(heartbeat())
    results = await asyncio.gather(connect_task, receiver_task, sender_task, heartbeat_task)


class App(tk.Tk):
    def __init__(self, loop, interval=1 / 120):
        global WIDTH, HEIGHT

        if IS_LOGS_FOR_DEBUG:
            print("App init")

        super().__init__()
        self.loop = loop
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.tasks = []
        #self.tasks.append(loop.create_task(self.gpsreader(1 / 2)))
        self.tasks.append(loop.create_task(self.rotator(1 / 60, 2)))
        self.tasks.append(loop.create_task(self.updater(interval)))
        self.tasks.append(loop.create_task(main()))
        self.is_new_line_odd = True
        self.TAG_NAME_ODD = 'odd'
        self.TAG_NAME_EVEN = 'even'
        self.TAG_NAME_ODD_CHANGED = 'odd_changed'
        self.TAG_NAME_EVEN_CHANGED = 'even_changed'
        self.VALID_CANVAS_BORDER = 3

        self.label_saved_state = False

        if IS_TEST_DATA_GENERATION:
            self.tasks.append(loop.create_task(self.generate_test_tree_data()))

        super().title("Configurator")
        #super().attributes('-zoomed', True)
        super().state('zoomed')

        #self.root = tk.Tk()

    async def rotator(self, interval, d_per_tick):
        if IS_LOGS_FOR_DEBUG:
            print("Run rotator")

        await self.init_gui()

        while await asyncio.sleep(interval, True):
            pass

        await asyncio.sleep(1)

    def get_device_list(self):
        platform_str = str(sys.platform)
        pors = []
        if platform_str.startswith("linux"):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif platform_str.startswith("win"):
            # import serial.tools.list_ports;
            comports = serial.tools.list_ports.comports()
            #print(comports)
            #ports = ['COM%s' % (i + 1) for i in range(256)]
            ports = []
            for port in comports:
                ports.append(port.description)
        return ports

    async def init_gui(self):
        self.style = ttk.Style()

        self.my_font_size = 10
        self.my_font_small_size = 10
        self.myFont = tkfont.Font(size=self.my_font_size)
        self.myFontSmall = tkfont.Font(size=self.my_font_small_size)

        top_frame = ttk.Frame(borderwidth=0, relief=tk.SOLID, padding=[8, 10])

        #combo_values = ["Python", "C", "C++", "Java"]
        combo_device_values = self.get_device_list()
        self.style.configure('W.TCombobox', arrowsize=40)
        top_frame.option_add("*TCombobox*Listbox*Font", self.myFont)

        self.combo_device = ttk.Combobox(top_frame, values=combo_device_values, style="W.TCombobox", font=self.myFont, state='readonly', width=25)
        self.combo_device.Font = self.myFont
        combo_device_default_text = "Select the Port..."
        self.combo_device.set(combo_device_default_text)
        self.combo_device.pack(side=tk.LEFT, padx=10)

        combo_baud_values = ('110', '300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '38400', '57600', '115200', '128000', '256000')
        self.style.configure('W.TCombobox', arrowsize=40)
        top_frame.option_add("*TCombobox*Listbox*Font", self.myFont)

        self.combo_baud = ttk.Combobox(top_frame, values=combo_baud_values, style="W.TCombobox", font=self.myFont, state='readonly')
        self.combo_baud.Font = self.myFont
        combo_baud_default_text = "115200"
        self.combo_baud.set(combo_baud_default_text)
        self.combo_baud.pack(side=tk.LEFT, padx=10)

        button_get = tk.Button(top_frame, text="GET", command=self.button_get_press, font=self.myFont, width=13, bg='#D0D090')
        button_get.pack(side=tk.LEFT, padx=10)

        button_set = tk.Button(top_frame, text="SET", command=self.button_set_press, font=self.myFont, width=13, bg='#90D090')
        button_set.pack(side=tk.LEFT, padx=10)

        button_default = tk.Button(top_frame, text="SET DEFAULT", command=self.button_default_press, font=self.myFont, width=13, bg='#D09090')
        button_default.pack(side=tk.LEFT, padx=10)

        #tk.Label(top_frame, text="EEPROM status:", font=self.myFont).pack(side=tk.LEFT, padx=10)

        self.var_saved_text = tk.StringVar()
        self.label_saved = tk.Label(top_frame, textvariable=self.var_saved_text, font=self.myFont)
        self.label_saved.pack(side=tk.LEFT, padx=10)
        self.set_label_saved_state(False)

        top_frame.pack(padx=10, pady=10, ipadx=10, ipady=10)

        hint_frame = ttk.Frame(borderwidth=0, relief=tk.SOLID, padding=[8, 0, 10, 10])
        hint_label = ttk.Label(hint_frame, text=HINT_TEX, font=self.myFontSmall)
        hint_label.pack(anchor=tk.NW)
        hint_frame.pack(anchor=tk.NW, fill=tk.BOTH)

        columns = ('index', 'id', 'value', 'default', 'range', 'description')

        self.tree_frame = ttk.Frame(borderwidth=1, relief=tk.SOLID, padding=[8, 10])

        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings', height=40)

        # CreateToolTip(self.tree_frame, text='Hello World\n'
        #                            'This is how tip looks like.'
        #                            'Best part is, it\'s not a menu.\n'
        #                            'Purely tipbox.')

        self.tree.tag_configure(self.TAG_NAME_ODD, background='#f2f2f2')
        self.tree.tag_configure(self.TAG_NAME_EVEN, background='#d0d0d0')
        self.tree.tag_configure(self.TAG_NAME_ODD_CHANGED, background='#a0e0a0')
        self.tree.tag_configure(self.TAG_NAME_EVEN_CHANGED, background='#80c080')
        # tree.pack(expand=True, fill=BOTH)
        self.tree.pack()

        self.style.configure("Treeview.Heading", font=(None, self.my_font_size))
        self.style.configure("Treeview", font=(None, self.my_font_size))
        rowheight = math.floor(3.0 * self.my_font_size)
        self.style.configure('Treeview', rowheight=rowheight)

        self.tree.heading(columns[0], text="Index")
        self.tree.column(columns[0], minwidth=0, width=40, stretch=tk.NO)
        self.tree.heading(columns[1], text="ID")
        self.tree.column(columns[1], minwidth=0, width=150, stretch=tk.NO)
        self.tree.heading(columns[2], text="Value")
        self.tree.column(columns[2], minwidth=0, width=60, stretch=tk.NO)
        self.tree.heading(columns[3], text="Default")
        self.tree.column(columns[3], minwidth=0, width=60, stretch=tk.NO)
        self.tree.heading(columns[4], text="Range")
        self.tree.column(columns[4], minwidth=0, width=120, stretch=tk.NO)
        self.tree.heading(columns[5], text="Description")
        self.tree.column(columns[5], minwidth=0, width=200)

        #self.generate_tree_data()

        self.tree.bind('<Double-1>', self.item_selected)

        self.tree.grid(row=0, column=0, sticky='nsew')

        # add a scrollbar
        scrollbar = tk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview, width=30)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        scrollbar.grid_columnconfigure(1, weight=1)
        scrollbar.grid_rowconfigure(0, weight=1)

        self.tree_frame.pack(anchor=tk.NW, fill=tk.BOTH)
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)

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
            self.var_saved_text.set("Waiting...")
            self.label_saved.config(fg="orange")
            return
        if state is True:
            self.var_saved_text.set("Saved     ")
            self.label_saved.config(fg="green")
            return
        if state is False:
            self.var_saved_text.set("Changed   ")
            self.label_saved.config(fg="grey")
            return

    async def generate_test_tree_data(self):
        await asyncio.sleep(5)

        contacts = []
        for n in range(1, 50):
            #textbox = tk.Text()
            index_str = f'{n}'
            id_str = f'VALUE_{n}'
            value_str = f'{n}{n}{n}'
            default_str = f'{n}{n}{n}'
            range_str = f'{n}..{n+1}'
            description_str = str(n) + " sdfeduioh  ehiusef \n  ehuihas eaa iheiuaseuh \
            e a89r983h  euihrf89we89ehrf  euwfheuf98ef8 \nasbndasdu88  udu8  hudhfdksfsdsdufsdhjb sdddfasf"
            contacts.append((index_str, id_str, value_str, default_str, range_str, description_str))

        # add data to the treeview
        for contact in contacts:
            tag = 'even'
            if self.is_new_line_odd:
                tag = 'odd'

            self.tree.insert('', tk.END, values=contact, tags=(tag,), row_height=300)
            self.is_odd_line = not self.is_odd_line

    def delete_all_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.set_label_saved_state(False)

    def get_data_from_mavlink_message(self, m):
        param_id = m.param_id
        param_value = m.param_value
        param_type = m.param_type
        param_count = m.param_count
        param_index = m.param_index

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
        parameter_xml = xml_file.getElementsByTagName(id_str)[0]
        default_str = parameter_xml.getElementsByTagName('Default')[0].firstChild.data
        range_str = parameter_xml.getElementsByTagName('Range')[0].firstChild.data
        description_str = parameter_xml.getElementsByTagName('Description')[0].firstChild.data

        min_str = str(range_str).split(" ")[0]
        dot_position = min_str.find(".")
        if dot_position > 0:
           decimal_nums_count = len(min_str) - dot_position - 1
           param_value_rounded = round(param_value, decimal_nums_count)
           value_str = str(param_value_rounded)

        row = (index_str, id_str, value_str, default_str, range_str, description_str)

        tag = 'even'
        if self.is_new_line_odd:
            tag = 'odd'

        self.tree.insert('', tk.END, values=row, tags=(tag,))
        self.is_new_line_odd = not self.is_new_line_odd

        self.tree.column("#0", stretch=False)

        self.set_label_saved_state(True)

    def handle_statustext(self, m):
        fieldnames = m.get_fieldnames()
        if 'severity' in fieldnames and 'text' in fieldnames:
            text = m.text
            print(f"STATUSTEXT: {text}")
            if str(text).startswith(STATUS_TEXT_SAVED):
                self.reset_label_saved_state(True)

    def item_selected(self, event):
        region_clicked = self.tree.identify_region(event.x, event.y)
        # print(region_clicked)
        if region_clicked not in ("cell"):
            return
        column = self.tree.identify_column(event.x)
        # Work for column #3 only
        self.column_index = int(column[1:]) - 1

        # if column != '#3':
        #     return
        self.selected_iid = self.tree.focus()
        # print(self.selected_iid)

        column_box = self.tree.bbox(self.selected_iid, column)
        # print(column_box)

        for selected_item in self.tree.selection():
            item = self.tree.item(selected_item)
            selected_values = item['values']
            selected_text = selected_values[self.column_index]
            # print(selected_text)
            # Show Info only
            record = item['values'][DESCRIPTION_COLUMN_NUMBER]
            # show a message
            # showinfo(title='Information', message=','.join(record))
            # showinfo(title='Information', message=record)

        if self.column_index == DESCRIPTION_COLUMN_NUMBER:
            # show a message
            message_title = selected_values[ID_COLUMN_NUMBER]
            showinfo(title=message_title, message=record)
        elif self.column_index == VALUES_COLUMN_NUMBER:
            valid_canvas_width = column_box[2]+2*self.VALID_CANVAS_BORDER
            valid_canvas_height = column_box[3]+2*self.VALID_CANVAS_BORDER
            self.entry_valid_canvas = tk.Canvas(width=valid_canvas_width, height=valid_canvas_height)

            self.entry_edit = ttk.Entry( width=column_box[2], font=self.myFont)
            tree_root_x = self.tree.winfo_x()
            tree_root_y = self.tree.winfo_y()
            tree_frame_x = self.tree_frame.winfo_x()
            tree_frame_y = self.tree_frame.winfo_y()

            self.entry_valid_rectangle = self.entry_valid_canvas.create_rectangle(0, 0, 1000, 1000,   fill='grey')
            valid_canvas_x = column_box[0] + tree_root_x + tree_frame_x - self.VALID_CANVAS_BORDER
            valid_canvas_y = column_box[1] + tree_root_y + tree_frame_y - self.VALID_CANVAS_BORDER
            self.entry_valid_canvas.place(x=valid_canvas_x, y=valid_canvas_y)
            self.entry_edit.place(x=column_box[0] + tree_root_x + tree_frame_x,
                             y=column_box[1] + tree_root_y + tree_frame_y,
                             w=column_box[2],
                             h=column_box[3])
            self.entry_edit.editing_column_index = self.column_index
            self.entry_edit.editing_item_iid = self.selected_iid
            self.entry_edit.insert(0, selected_text)
            self.entry_edit.select_range(0, tk.END)
            # self.entry_edit.configure(background="white", foreground="orange")
            self.entry_edit.bind("<FocusOut>", self.on_focus_out)
            self.entry_edit.bind("<KeyRelease>", self.on_key_released)
            self.entry_edit.focus()

    def on_focus_out(self, event):
        event.widget.destroy()
        self.entry_valid_canvas.destroy()

    def on_key_released(self, event):
        widget = event.widget
        new_text = widget.get()
        print(f"new_text = {new_text}")

        item = self.tree.item(self.selected_iid)
        current_values = item['values']  # , text=new_text)
        #print(current_values)

        current_tags = self.tree.item(self.selected_iid, "tags")
        # print(f"current_tags = {current_tags}")
        if current_tags[0].startswith(self.TAG_NAME_ODD):
            current_tags = (self.TAG_NAME_ODD_CHANGED,)
        else:
            current_tags = (self.TAG_NAME_EVEN_CHANGED,)

        is_valid = False
        try:
            new_val = float(new_text)
        except ValueError:
            pass
        else:
            min_max = current_values[RANGE_COLUMN_NUMBER]
            min_max_list = str(min_max).split(" ")
            min_float = float(min_max_list[0])
            max_float = float(min_max_list[1])

            is_dot_position_correct = False
            min_str = str(min_max).split(" ")[0]
            dot_position = min_str.find(".")
            if dot_position > 0:
                decimal_nums_count = len(min_str) - dot_position - 1
                new_text_dot_position = new_text.find(".")
                if new_text_dot_position > -1:
                    new_text_decimal_nums_count = len(new_text) - new_text_dot_position - 1
                    if new_text_decimal_nums_count <= decimal_nums_count:
                        is_dot_position_correct = True
            else:
                is_dot_position_correct = True

            if min_float <= new_val <= max_float and is_dot_position_correct:
                is_valid = True

        if str(new_text).endswith("."):
            is_valid = False

        if is_valid:
            self.entry_valid_canvas.itemconfig(self.entry_valid_rectangle, fill='grey')
        else:
            self.entry_valid_canvas.itemconfig(self.entry_valid_rectangle, fill='red')

        keysym = event.keysym
        #print(f"keysym = {keysym}")

        if keysym.startswith("Return") or keysym.startswith("KP_Enter"):
            if is_valid:
                current_values[self.column_index] = new_text
                self.tree.item(self.selected_iid, values=current_values, tags=current_tags)
                widget.destroy()
                self.entry_valid_canvas.destroy()

                self.set_label_saved_state(False)

    def button_get_press(self):
        global  sender_command
        global get_button_pressed_time_s

        print("GET Button pressed")
        now_s = time.time()
        if get_button_pressed_time_s is not None:
            if now_s - get_button_pressed_time_s < GET_BUTTON_PRESSED_TIMEOUT_S:
                print("GET Button: timeout has not ended yet")
                return

        sender_command = COMMAND_REQUEST_LIST
        get_button_pressed_time_s = now_s

    def button_set_press(self):
        global sender_command
        global param_to_set_list

        print("SET Button pressed")

        param_to_set_list = []

        list_of_entries = self.tree.get_children()

        for each in list_of_entries:
            #print(self.tree.item(each)['values'])
            tags = self.tree.item(each, "tags")
            if self.TAG_NAME_ODD_CHANGED in tags or self.TAG_NAME_EVEN_CHANGED in tags:
                param_id = self.tree.item(each)['values'][ID_COLUMN_NUMBER]
                param_value = self.tree.item(each)['values'][VALUES_COLUMN_NUMBER]
                new_param_and_value = {
                    "param_id": param_id,
                    "param_value": param_value
                }
                param_to_set_list.append(new_param_and_value)
                if self.TAG_NAME_ODD_CHANGED in tags:
                    new_tag = self.TAG_NAME_ODD
                else:
                    new_tag = self.TAG_NAME_EVEN
                self.tree.item(each, tags=(new_tag, ))

        if len(param_to_set_list) > 0:
            sender_command = COMMAND_PARAM_SET
            self.set_label_saved_state(None)


    def button_default_press(self):
        print("SET_DEFAULT Button pressed")

        list_of_entries = self.tree.get_children()

        for each in list_of_entries:
            # print(self.tree.item(each)['values'])
            tags = self.tree.item(each, "tags")

            row_values = self.tree.item(each)['values']
            param_default = self.tree.item(each)['values'][DEFAULT_COLUMN_NUMBER]
            row_values[VALUES_COLUMN_NUMBER] = param_default

            if self.TAG_NAME_ODD in tags or self.TAG_NAME_ODD_CHANGED in tags:
                new_tag = self.TAG_NAME_ODD_CHANGED
            else:
                new_tag = self.TAG_NAME_EVEN_CHANGED

            self.tree.item(each, values=row_values, tags=(new_tag,))

        self.button_set_press()


    async def updater(self, interval):
        while True:
            if IS_LOGS_FOR_DEBUG:
                # print("Run update")
                pass

            self.update()
            await asyncio.sleep(interval)


    def close(self):
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()


def close(self):
    for task in self.tasks:
        task.cancel()
    self.loop.stop()
    self.destroy()


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


#if __name__ == "__main__":

loop = asyncio.get_event_loop()

if IS_LOGS_FOR_DEBUG:
    print("Run App...")

# parse an xml file by name
if getattr(sys, 'frozen', False):
    # in case of run as one exe
    xml_file = minidom.parse(file=os.path.join(sys._MEIPASS, 'files/parameters.xml'))
else:
    xml_file = minidom.parse('../parameters.xml')

app = App(loop)
loop.run_forever()
loop.close()