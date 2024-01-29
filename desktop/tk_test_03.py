import tkinter as tk
from tkinter import ttk
#from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import showinfo
import tkinter.font as tkfont


selected_iid = -1
column_index = -1

def on_window_resize(event):
    width = event.width
    height = event.height
    print(f"Window resized to {width}x{height}")
    print(f"tree_frame size ({tree_frame.winfo_width()} x {tree_frame.winfo_height()})")
    print(f"tree size ({tree.winfo_width()} x {tree.winfo_height()})")


root = tk.Tk()
root.title('Treeview demo')
root.geometry('800x600')

style = ttk.Style()


def button_1_press():
    print("1 Button pressed")


def button_2_press():
    print("2 Button pressed")


def button_3_press():
    print("3 Button pressed")


myFont = tkfont.Font(size = 20)

top_frame = ttk.Frame(borderwidth=0, relief=tk.SOLID, padding=[8, 10])

button_1 = tk.Button(top_frame, text="1 Button", command=button_1_press, font=myFont)
button_1.pack(side=tk.LEFT, padx=10)

button_2 = tk.Button(top_frame, text="2 Button", command=button_2_press, font=myFont)
button_2.pack(side=tk.LEFT, padx=10)

button_3 = tk.Button(top_frame, text="3 Button", command=button_3_press, font=myFont)
button_3.pack(side=tk.LEFT, padx=10)


top_frame.pack(padx=10, pady=10, ipadx=10, ipady=10)

# define columns
columns = ('first_name', 'last_name', 'email')

tree_frame = ttk.Frame(borderwidth=1, relief=tk.SOLID, padding=[8, 10])

tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

tree.tag_configure('odd', background='#f2f2f2')
tree.tag_configure('even', background='#d0d0d0')
#tree.pack(expand=True, fill=BOTH)
tree.pack()

style.configure("Treeview.Heading", font=(None, 25))
style.configure("Treeview", font=(None, 25))
style.configure('Treeview', rowheight=40)

# define headings
# tree.heading('first_name', text='First Name')
# tree.heading('last_name', text='Last Name')
# tree.heading('email', text='Email')

tree.heading(columns[0], text="First Name")
tree.column(columns[0], minwidth=0, width=250, stretch=tk.NO)
tree.heading(columns[1], text="Last Name")
tree.column(columns[1], minwidth=0, width=200, stretch=tk.NO)
tree.heading(columns[2], text="Email")
tree.column(columns[2], minwidth=0, width=200)

# generate sample data
contacts = []
for n in range(1, 50):
    textbox = tk.Text()
    comment = str(n) + " sdfeduioh  ehiusef \n  ehuihas eaa iheiuaseuh \
    e a89r983h  euihrf89we89ehrf  euwfheuf98ef8 \nasbndasdu88  udu8  hudhfdksfsdsdufsdhjb sdddfasf"
    contacts.append((f'first {n}', f'last {n}', comment))

# add data to the treeview
is_odd_line = True
for contact in contacts:
    tag = 'even'
    if is_odd_line:
        tag = 'odd'

    tree.insert('', tk.END, values=contact, tags=(tag,))
    is_odd_line = not is_odd_line


def item_selected(event):
    global selected_iid
    global column_index

    region_clicked = tree.identify_region(event.x, event.y)
    #print(region_clicked)
    if region_clicked not in ("cell"):
        return
    column = tree.identify_column(event.x)
    # Work for column #3 only
    column_index = int(column[1:]) - 1

    # if column != '#3':
    #     return
    selected_iid = tree.focus()
    #print(selected_iid)

    column_box = tree.bbox(selected_iid, column)
    #print(column_box)

    for selected_item in tree.selection():
        item = tree.item(selected_item)
        selected_values = item['values']
        selected_text = selected_values[column_index]
        #print(selected_text)
        # Show Info only
        record = item['values'][2]
        # show a message
        #showinfo(title='Information', message=','.join(record))
        #showinfo(title='Information', message=record)

    if column_index == 2:
        # show a message
        showinfo(title='Information', message=record)
    elif column_index == 1:
        entry_edit = ttk.Entry(root, width=column_box[2], font=myFont)
        tree_root_x = tree.winfo_x()
        tree_root_y = tree.winfo_y()
        tree_frame_x = tree_frame.winfo_x()
        tree_frame_y = tree_frame.winfo_y()
        entry_edit.place(x=column_box[0] + tree_root_x + tree_frame_x,
                         y=column_box[1] + tree_root_y + tree_frame_y,
                         w=column_box[2],
                         h=column_box[3])
        entry_edit.editing_column_index = column_index
        entry_edit.editing_item_iid = selected_iid
        entry_edit.insert(0, selected_text)
        entry_edit.select_range(0, tk.END)
        #entry_edit.configure(background="white", foreground="orange")
        entry_edit.bind("<FocusOut>", on_focus_out)
        entry_edit.bind("<Return>", on_enter_pressed )
        entry_edit.focus()


def on_focus_out(event):
    event.widget.destroy()


def on_enter_pressed(event):
    widget = event.widget
    new_text = widget.get()
    print(new_text)
    #selected_iid_str = "#" + str(selected_iid + 1)
    item = tree.item(selected_iid)
    current_values = item['values'] #, text=new_text)
    #print(current_values)
    current_values[column_index] = new_text
    tree.item(selected_iid, values=current_values)
    widget.destroy()

#tree.bind('<<TreeviewSelect>>', item_selected)
tree.bind('<Double-1>', item_selected)

tree.grid(row=0, column=0, sticky='nsew')
#
# tree.grid_columnconfigure(0,weight=1)
# tree.grid_rowconfigure(0,weight=1)


# add a scrollbar
scrollbar = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview, width=30)
tree.configure(yscroll=scrollbar.set)
scrollbar.grid(row=0, column=1, sticky='ns')

scrollbar.grid_columnconfigure(1,weight=1)
scrollbar.grid_rowconfigure(0,weight=1)

tree_frame.pack(anchor=tk.NW, fill=tk.BOTH)
tree_frame.columnconfigure(0, weight=1)
tree_frame.rowconfigure(0, weight=1)

# Bind the resize event to a function
root.bind("<Configure>", on_window_resize)

# run the app
root.mainloop()