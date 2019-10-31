from tkinter import *
from threading import Thread
from InstagramAPI import InstagramAPI
import time
from datetime import datetime
import tkinter.ttk
import urllib.request
from PIL import ImageTk, Image
import sys
import os

class ScrollFrame(tkinter.Frame):
    def __init__(self, parent):
        super().__init__(parent) # create a frame (self)

        self.canvas = tkinter.Canvas(self, borderwidth=0, background="#ffffff")
        self.viewPort = tkinter.Frame(self.canvas, background="#ffffff")
        self.vsb = tkinter.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.viewPort, anchor="nw",
                                  tags="self.viewPort")
        self.viewPort.bind("<Configure>", self.onFrameConfigure)
    def onFrameConfigure(self, event):                                              
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))




class Example(tkinter.Frame):
    def __init__(self, root,users):
        tkinter.Frame.__init__(self, root)
        self.scrollFrame = ScrollFrame(self)
        position_y=0
        for user in users:
            image = Image.open('assets\\icons\\'+user['username']+'.jpg')
            image = image.resize((30, 30), Image.ANTIALIAS)
            image.save('assets\\icons\\'+user['username']+'_resize.jpg')
            image = ImageTk.PhotoImage(file='assets\\icons\\'+user['username']+'_resize.jpg')
            bg_label = tkinter.ttk.Label(self.scrollFrame.viewPort, image = image)
            bg_label.place(x=0, y=position_y).grid(row=row, column=1)
            bg_label.image = image
            tkinter.ttk.Label(self.scrollFrame.viewPort, text=user['username'],font=("Helvetica", 15)).place(x=40,y=position_y).grid(row=row, column=1)
            position_y+=100;
        self.scrollFrame.pack(side="top", fill="both", expand=True)

root=tkinter.Tk()
root.geometry("600x800")
root.title("Instagram Direct by sergeitrigubovfleps@gmail.com")
chats = {}
API = InstagramAPI("login", "password")
API.login()
API.getv2Inbox()
threads = API.LastJson["inbox"]["threads"]
followers=[]
for message in threads:
    followers.append(message['users'][0])
for user in followers:
    urllib.request.urlretrieve(user['profile_pic_url'], "assets/icons/"+user['username']+".jpg")
Example(root,followers).pack(side="top", fill="both", expand=True)
root.mainloop()



"""def get_all_message_members(API):
    API.getv2Inbox()
    threads = API.LastJson["inbox"]["threads"]
    print(threads)

def chat(recipient):
    messages = Text(window)
    input_user = StringVar()
    img = ImageTk.PhotoImage(Image.open('assets\\icons\\'+recipient['username']+'.jpg'))
    panel = Label(window, image = img)
    panel.pack(side = "top", anchor=NW)
    Label(window,text=recipient['username'],font=("Helvetica", 20)).place(x=250, y=65)
    messages.pack(side = "top", anchor=NW)
    input_field = Entry(window, text=input_user)
    input_field.pack(side=BOTTOM, fill=X)
    messages.tag_configure('tag-left', justify='left')
    messages.tag_configure('tag-right', justify='right')
    def Enter_pressed(event):
        input_get = input_field.get()
        messages.insert(INSERT, '%s\n' % input_get,'tag-left')
        self.API.direct_message(input_get, recipient['pk'])
        input_user.set('')
        return "break"
    frame = Frame(window)
    input_field.bind("<Return>", Enter_pressed)
    frame.pack()

def create_widgets_in_first_frame(users):


def create_widgets_in_second_frame():
    second_window_label = tkinter.ttk.Label(second_frame, text='Window 2')


def call_first_frame_on_top():
    second_frame.grid_forget()
    first_frame.grid(column=0, row=0, sticky=(tkinter.W, tkinter.N, tkinter.E))

def call_second_frame_on_top():
    first_frame.grid_forget()
    second_frame.grid(column=0, row=0, sticky=(tkinter.W, tkinter.N, tkinter.E))


def quit_program():
    root_window.destroy()

root_window = tkinter.Tk()
root_window.geometry("600x800")
root_window.title("Instagram Direct by sergeitrigubovfleps@gmail.com")
root_window.resizable(0, 0)
window_width = 600
window_heigth = 800
chats = {}
API = InstagramAPI("login", "password")
API.login()
user_id = API.username_id
API.getv2Inbox()
threads = API.LastJson["inbox"]["threads"]
followers=[]
for message in threads:
    followers.append(message['users'][0])
for user in followers:
    urllib.request.urlretrieve(user['profile_pic_url'], "assets/icons/"+user['username']+".jpg")

first_frame=tkinter.ttk.Frame(root_window, width=window_width, height=window_heigth)
first_frame['borderwidth'] = 2
first_frame['relief'] = 'sunken'
first_frame.grid(column=0, row=0, sticky=(tkinter.W, tkinter.N, tkinter.E))

second_frame=tkinter.ttk.Frame(root_window, width=window_width, height=window_heigth)
second_frame['borderwidth'] = 2
second_frame['relief'] = 'sunken'
second_frame.grid(column=0, row=0, sticky=(tkinter.W, tkinter.N, tkinter.E))

# Create all widgets to all frames
create_widgets_in_second_frame()
create_widgets_in_first_frame(followers)

# Hide all frames in reverse order, but leave first frame visible (unhidden).
second_frame.grid_forget()

# Start tkinter event - loopw
root_window.mainloop()"""