from tkinter import *
from tkinter import ttk
 
root = Tk()
root.title("Configurator")
root.geometry("350x350")
 
for r in range(3):
    for c in range(3):
        btn = ttk.Button(text=f"({r},{c})")
        btn.grid(row=r, column=c)

rows = []
for i in range(5):
    cols = []
    for j in range(4):
        e = Entry(relief=GROOVE)
        e.grid(row=i, column=j, sticky=NSEW)
        e.insert(END, '%d.%d' % (i, j))
        cols.append(e)
    rows.append(cols)
 
root.mainloop()