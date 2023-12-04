import asyncio
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from tkinter.messagebox import showinfo
from argparse import ArgumentParser
from serial import SerialException
from pymavlink import mavutil
import time
from xml.dom import minidom
import os
import sys


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
CONNECT_PERIOD_S = 2
WAIT_BEFORE_FIRST_SEND_S = 3
MINIMAL_ASYNC_PAUSE_S = 0.01
MAVLINK_MESSAGE_ID_PARAM_VALUE = 22

# 0 based column numbers
ID_COLUMN_NUMBER = 1
VALUES_COLUMN_NUMBER = 2
DESCRIPTION_COLUMN_NUMBER = 5

HINT_TEX = "Double-click the Description cell to view the full text.   Double-click the Value cell to edit the value."


async def connect():
    global master

    parser = ArgumentParser(description=__doc__)

    parser.add_argument("--baudrate", type=int,
                        help="master port baud rate", default=115200)
    parser.add_argument("--device", required=True, help="serial device")
    args = parser.parse_args()

    ### MAV related code starts here ###

    is_connected = False
    # create a mavlink serial instance
    while not is_connected:
        try:
            master = mavutil.mavlink_connection(args.device, baud=args.baudrate)
        except SerialException:
            print(f"! Can not connect to: {args.device} at {args.baudrate}" )
        else:
            print(f"Connected to: {master.port} at {master.baud}")
            is_connected = True
        await asyncio.sleep(CONNECT_PERIOD_S)


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
                if m_src_id == TARGET_COMPONENT_ID:
                    print(f">> id = {m.id} from {m_src_id}")
                    print(str(m))
                    if m.id == MAVLINK_MESSAGE_ID_PARAM_VALUE:
                        app.get_data_from_mavlink_message(m)

        await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)


async def sender():
    global master

    await asyncio.sleep(WAIT_BEFORE_FIRST_SEND_S)
    while master is None:
        await asyncio.sleep(MINIMAL_ASYNC_PAUSE_S)

    target_system = SYSTEM_ID
    target_component = TARGET_COMPONENT_ID
    master.mav.srcComponent = SELF_COMPONENT_ID
    master.mav.param_request_list_send(target_system, target_component)
    print(f"_________________<< param_request_list_send(target_system={target_system}, target_component={target_component})")

    while True:
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

        if IS_TEST_DATA_GENERATION:
            self.tasks.append(loop.create_task(self.generate_test_tree_data()))

        super().title("Configurator")
        super().attributes('-zoomed', True)

        #self.root = tk.Tk()

    async def rotator(self, interval, d_per_tick):
        if IS_LOGS_FOR_DEBUG:
            print("Run rotator")

        await self.init_gui()

        while await asyncio.sleep(interval, True):
            pass

        await asyncio.sleep(1)

    async def init_gui(self):
        self.style = ttk.Style()

        self.myFont = tkfont.Font(size=20)
        self.myFontSmall = tkfont.Font(size=15)

        top_frame = ttk.Frame(borderwidth=0, relief=tk.SOLID, padding=[8, 10])

        button_get = tk.Button(top_frame, text="GET", command=self.button_get_press, font=self.myFont, width=13, bg='#D0D090')
        button_get.pack(side=tk.LEFT, padx=10)

        button_set = tk.Button(top_frame, text="SET", command=self.button_set_press, font=self.myFont, width=13, bg='#90D090')
        button_set.pack(side=tk.LEFT, padx=10)

        button_default = tk.Button(top_frame, text="SET DEFAULT", command=self.button_default_press, font=self.myFont, width=13, bg='#D09090')
        button_default.pack(side=tk.LEFT, padx=10)

        top_frame.pack(padx=10, pady=10, ipadx=10, ipady=10)

        hint_frame = ttk.Frame(borderwidth=0, relief=tk.SOLID, padding=[8, 0, 10, 10])
        hint_label = ttk.Label(hint_frame, text=HINT_TEX, font=self.myFontSmall)
        hint_label.pack(anchor=tk.NW)
        hint_frame.pack(anchor=tk.NW, fill=tk.BOTH)

        columns = ('index', 'id', 'value', 'default', 'range', 'description')

        self.tree_frame = ttk.Frame(borderwidth=1, relief=tk.SOLID, padding=[8, 10])

        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings', height=40)

        CreateToolTip(self.tree_frame, text='Hello World\n'
                                   'This is how tip looks like.'
                                   'Best part is, it\'s not a menu.\n'
                                   'Purely tipbox.')

        self.tree.tag_configure('odd', background='#f2f2f2')
        self.tree.tag_configure('even', background='#d0d0d0')
        self.tree.tag_configure('changed', background='#e0a0a0')
        # tree.pack(expand=True, fill=BOTH)
        self.tree.pack()

        self.style.configure("Treeview.Heading", font=(None, 25))
        self.style.configure("Treeview", font=(None, 25))
        self.style.configure('Treeview', rowheight=50)

        self.tree.heading(columns[0], text="Index")
        self.tree.column(columns[0], minwidth=0, width=150, stretch=tk.NO)
        self.tree.heading(columns[1], text="ID")
        self.tree.column(columns[1], minwidth=0, width=300, stretch=tk.NO)
        self.tree.heading(columns[2], text="Value")
        self.tree.column(columns[2], minwidth=0, width=300, stretch=tk.NO)
        self.tree.heading(columns[3], text="Default")
        self.tree.column(columns[3], minwidth=0, width=150, stretch=tk.NO)
        self.tree.heading(columns[4], text="Range")
        self.tree.column(columns[4], minwidth=0, width=300, stretch=tk.NO)
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

    def get_data_from_mavlink_message(self, m):
        param_id = m.param_id
        param_value = m.param_value
        param_type = m.param_type
        param_count = m.param_count
        param_index = m.param_index

        index_str = str(param_index)
        id_str = str(param_id)
        value_str = str(param_value)
        parameter_xml = xml_file.getElementsByTagName(id_str)[0]
        default_str = parameter_xml.getElementsByTagName('Default')[0].firstChild.data
        range_str = parameter_xml.getElementsByTagName('Range')[0].firstChild.data
        description_str = parameter_xml.getElementsByTagName('Description')[0].firstChild.data

        row = (index_str, id_str, value_str, default_str, range_str, description_str)

        tag = 'even'
        if self.is_new_line_odd:
            tag = 'odd'

        self.tree.insert('', tk.END, values=row, tags=(tag,))
        self.is_new_line_odd = not self.is_new_line_odd

        self.tree.column("#0", stretch=False)

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
            entry_edit = ttk.Entry( width=column_box[2], font=self.myFont)
            tree_root_x = self.tree.winfo_x()
            tree_root_y = self.tree.winfo_y()
            tree_frame_x = self.tree_frame.winfo_x()
            tree_frame_y = self.tree_frame.winfo_y()
            entry_edit.place(x=column_box[0] + tree_root_x + tree_frame_x,
                             y=column_box[1] + tree_root_y + tree_frame_y,
                             w=column_box[2],
                             h=column_box[3])
            entry_edit.editing_column_index = self.column_index
            entry_edit.editing_item_iid = self.selected_iid
            entry_edit.insert(0, selected_text)
            entry_edit.select_range(0, tk.END)
            # entry_edit.configure(background="white", foreground="orange")
            entry_edit.bind("<FocusOut>", self.on_focus_out)
            entry_edit.bind("<Return>", self.on_enter_pressed)
            entry_edit.focus()

    def on_focus_out(self, event):
        event.widget.destroy()

    def on_enter_pressed(self, event):
        widget = event.widget
        new_text = widget.get()
        print(new_text)
        # selected_iid_str = "#" + str(self.selected_iid + 1)
        item = self.tree.item(self.selected_iid)
        current_values = item['values']  # , text=new_text)
        # print(current_values)
        current_values[self.column_index] = new_text
        self.tree.item(self.selected_iid, values=current_values)
        widget.destroy()

    def button_get_press(self):
        print("GET Button pressed")

    def button_set_press(self):
        print("SET Button pressed")

    def button_default_press(self):
        print("SET_DEFAULT Button pressed")

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