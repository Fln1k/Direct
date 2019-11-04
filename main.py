#!/usr/bin/env python3

import os
import threading
import time
import webbrowser
import json
import tkinter as tk

import keyring

import api
import pfp

class Chat:

    def __init__(self, app, entry, threadId, users):
        self.usr = app.usr
        self.entry = entry
        self.threadId = threadId
        self.users = users
        self.app = app
        self.last_msgs = []
        self.pending_msgs = []
        self.app.scroll_req = False

        get_user_pics_thread = threading.Thread(target=self.get_user_pics)
        get_user_pics_thread.daemon = True
        get_user_pics_thread.start()

    def get_user_pics(self):
        usr_pics = {} #{pk: profile_pic_url}
        for user in self.users + [self.app.usr_name]:
            self.usr.api.searchUsername(user)
            response = json.loads(json.dumps(self.usr.api.LastJson))
            pfp_url = response["user"]["profile_pic_url"]
            image = pfp.retrieve_picture(pfp_url)

            usr_pics[response["user"]["pk"]] = image

        self.usr_pics = usr_pics

    def get_msgs(self):
        while True:
            try:
                msgs = self.usr.getMessages(self.threadId)
                if msgs != self.last_msgs:
                    new_msgs = []
                    for msg in msgs:
                        new_msgs.append(tk.Label(
                            self.app.canvas_frame,
                            text=msg["text"]))

                        new_msgs[-1].config(
                            anchor=tk.W,
                            bg="#222",
                            fg="#ccc",
                            wraplength=self.app.root.winfo_width(),
                            justify=tk.LEFT
                        )
                        if msg["show_pfp"]:
                            new_msgs[-1].config(
                                compound=tk.LEFT,
                                image=self.usr_pics[msg["user"]]
                            )

                        if msg["text"] == u" \u2764\uFE0F":
                            new_msgs[-1].config(
                                fg="#BE1931",
                                font=("Arial", 30)
                            )

                        new_msgs[-1].item_id = msg["item_id"]
                        new_msgs[-1].thread_id = self.threadId
                        new_msgs[-1].unsendable = msg["user"] == self.app.usr_pk


                    if self.app.location == "convorun":
                        self.pending_msgs = new_msgs[::-1] #invert to fix packing of recently-sent messages
                        self.app.scroll_req = True

            except AttributeError:
                pass

    def send_msg(self):

        msg = self.entry.get()
        self.entry.delete(0, "end")
        self.entry.config(state="disabled")
        self.usr.sendMessage(self.users, msg)
        self.entry.config(state="normal")
        self.app.stop_spam.config(state="disabled")
        self.app.back.config(state="normal")
        self.app.inf_spam.config(state="normal")
        #Reset thread
        self.send_msg_thread = threading.Thread(target=self.send_msg)
        self.send_msg_thread.daemon = True

class App:

    def __init__(self):

        def attempt_login(usrname=None, psswd_stored=None):
            self.root.title("Direct - Logging in")

            if usrname and psswd_stored:
                self.usr = api.User(usrname, psswd_stored)
            else:
                self.usr_name = usr_login.get()
                password = psswd.get()
                self.usr = api.User(usr_login.get(), psswd.get())
                #disable editing while logging in
                usr_login.config(state="disabled")
                psswd.config(state="disabled")
                login.config(state="disabled")

            if self.usr.api.login():
                try:
                    self.password = psswd.get()
                except NameError:
                    pass #Autologin attempted

                self.usr.api.searchUsername(self.usr_name)
                self.usr_pk = self.usr.api.LastJson["user"]["pk"]
                self.root.quit()
                self.logged_in = True
                return True

            else:

                if json.loads(json.dumps(self.usr.api.LastJson))["message"] == "challenge_required":
                    webbrowser.open(json.loads(json.dumps(self.usr.api.LastJson))["challenge"]["url"], new=2)
                    if self.usr.api.login():
                        self.usr.api.searchUsername(self.usr_name)
                        self.usr_pk = self.usr.api.LastJson["user"]["pk"]
                        self.root.quit()
                        self.logged_in = True
                        return 0

                usr_login.config(state="normal")
                psswd.config(state="normal")
                login.config(state="normal")
                psswd.delete(0, "end")
                psswd.config(show="")
                psswd.insert(0, "Password")

                try:
                    del self.psswd_cleared
                except AttributeError:
                    pass

                self.root.title("Direct - Login")
                #Resetup login thread to allow rerun
                self.login_thread = threading.Thread(target=attempt_login)
                self.login_thread.daemon = True

        def clear_entry(event):
            try:
                self.usr_name_cleared

            except AttributeError:
                event.widget.delete(0, "end")
                self.usr_name_cleared = True

        def clear_entry_psswd(event):
            try:
                self.psswd_cleared
                event.widget.config(show="*")

            except AttributeError:
                event.widget.delete(0, "end")
                self.psswd_cleared = True
                event.widget.config(show="*")

            event.widget.config(show="*")

        self.location = "login"

        self.root = tk.Tk()
        self.root.title("Direct - Login")
        self.root.geometry(newGeometry=("500x500")) #Sizing
        self.root.minsize(500, 500)
        self.root.maxsize(500, 500)
        self.root.update()

        if keyring.get_password("W_DM", "W_DM_USERNAME") and keyring.get_password("W_DM", "W_DM_PASSWORD"):
            self.usr_name = keyring.get_password("W_DM", "W_DM_USERNAME")
            if attempt_login(keyring.get_password("W_DM", "W_DM_USERNAME"),
                             keyring.get_password("W_DM", "W_DM_PASSWORD")):
                self.homepage()

        #Setup attempt_login thread
        self.login_thread = threading.Thread(target=attempt_login)
        self.login_thread.daemon = True
        self.logged_in = False

        usr_login = tk.Entry()
        usr_login.insert(0, "Username")
        usr_login.bind("<Button-1>", clear_entry)
        usr_login.bind("<Key>", clear_entry)
        usr_login.bind("<Return>",
                    lambda event: self.login_thread.start())
        usr_login.place(relx=.5, rely=.475, anchor="center")

        psswd = tk.Entry()
        psswd.insert(0, "Password")
        psswd.bind("<Button-1>", clear_entry_psswd)
        psswd.bind("<Key>", clear_entry_psswd)
        psswd.bind("<Return>",
                    lambda event: self.login_thread.start())
        psswd.place(relx=.5, rely=.525, anchor="center")

        login = tk.Button(command=lambda: self.login_thread.start())
        login["text"] = "Login"
        login.place(relx=.44, rely=.555)

        #Styling
        font = ("Helvetica", 13)
        self.root.config(background="#000")
        usr_login.config(
                            background="#222",
                            fg="#ddd",
                            bd=0,
                            font=font)
        psswd.config(background="#222",
                        fg="#ddd",
                        bd=0,
                        font=font)
        login.config(background="#222",
                        fg="#ddd",
                        bd=0,
                        font=font)

        self.root.mainloop()
        #Clear icons
        usr_login.place_forget()
        psswd.place_forget()
        login.place_forget()

        self.scroll_req = True
        #Save login details here as they need to be set from main thread
        keyring.set_password("W_DM", "W_DM_USERNAME", self.usr_name)
        keyring.set_password("W_DM", "W_DM_PASSWORD", self.password)
        del self.password
        self.homepage()

    def homepage(self):

        def mouse_scroll(event):
            #Linux
            if event.num == 4:
                self.canvas.yview_scroll(-2, "units")

            if event.num == 5:
                self.canvas.yview_scroll(2, "units")

            #Windows
            elif event.delta in (120, -120):
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


        def getChats():
            chats = []
            self.pending_chats = []
            self.sleep_required = False
            self.clear_required = False

            while True:
                if self.sleep_required:

                    time.sleep(60)
                    self.sleep_required = False
                    self.clear_required = True

                if self.location != "homepage":
                    break

                new_chats = self.usr.getChats()
                self.num_required_chats = len(new_chats)

                if chats == []:

                    self.pending_chats.append(tk.Button(
                            self.canvas_frame,
                            text=" " * 16 + "New Chat",
                            command=self.new_convo,
                            font=("Helvetica", 12)
                    ))
                    self.pending_chats[-1].config(
                        bd=1,
                        anchor=tk.W,
                        bg="#222",
                        fg="#ccc"
                    )

                    #Logout button
                    self.pending_chats.append(tk.Button(
                        self.canvas_frame,
                        text=" " * 16 + "Logout & Exit",
                        command=logout,
                        font=("Helvetica", 12)
                    ))
                    self.pending_chats[-1].config(
                        bd=1,
                        anchor=tk.W,
                        bg="#222",
                        fg="#ccc"
                    )

                if new_chats != chats:

                    for chat in new_chats:

                        #Get thread icon
                        image = pfp.retrieve_picture(chat["thread_icon"])
                        font = ("Helvetica", 10)

                        if image: #Check image received ok
                            self.pending_chats.append(tk.Button(
                                self.canvas_frame,
                                text="    " + chat["thread_name"],
                                command=lambda thread_id=chat["thread_id"], users=chat["users"]: self.convo_run(thread_id, users),
                                font=font))

                            self.pending_chats[-1].image = image
                            self.pending_chats[-1].config(compound=tk.LEFT,
                                               image=image,
                                               anchor=tk.W,
                                               bd=1,
                                               highlightbackground="#333",
                                               bg="#222",
                                               fg="#ccc")

                        else: #Offer alternative if image not received
                            self.pending_chats.append(tk.Button(
                                self.canvas_frame,
                                text="    " + chat["thread_name"],
                                command=lambda: self.convo_run(str(chat["thread_id"]), list(chat["users"]))))

                            self.pending_chats[-1].config(
                                bd=1,
                                anchor=tk.W,
                                bg="#222",
                                fg="#ccc")

                    chats = new_chats

        def clear_chats():
            #clear all buttons
            for button in self.canvas_frame.winfo_children():
                button.destroy()
            self.pending_chats = None

        def update_chats():

            if self.location != "homepage":
                return

            try:

                if self.clear_required: #Check clearing
                    clear_chats()
                    self.clear_required = False

                try:
                    if len(self.pending_chats) > self.num_required_chats: #Check for repetition
                        self.sleep_required = True
                except AttributeError:
                    #Num required not yet set - Do nothing
                    pass

                if self.sleep_required:
                    return #Not needed

                #Update widths
                for button in self.canvas_frame.winfo_children():
                    width = int(self.root.geometry()[:self.root.geometry().index("x")])
                    button.config(width=width)

                for chat_button in self.pending_chats:
                    chat_button.pack(fill=tk.X)

            except TypeError:
                pass #Hasn"t loaded yet

            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            self.root.after(1, update_chats)

        def scrollbar_update():
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        def logout():
            keyring.delete_password("W_DM", "W_DM_USERNAME")
            keyring.delete_password("W_DM", "W_DM_PASSWORD")
            self.root.destroy()

        #Setup window
        for item in self.root.winfo_children():
            item.destroy()

        self.location = "homepage" #Used for checking in threads
        self.root.title("Direct Homepage")
        self.root.config(background="#000")
        self.root.maxsize(self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        self.root.update()

        #setup canvas
        self.canvas = tk.Canvas(self.root, scrollregion=(0,0,500,500), background="#000", bd=0, highlightthickness=0)
        self.canvas_frame = tk.Frame(self.canvas, background="#000", bd=0, highlightthickness=0)
        #Setup scrollbar
        self.vscroll = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.vscroll.config(command=self.canvas.yview)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.canvas.config(yscrollcommand=self.vscroll.set)
        self.canvas.pack(fill="both", expand=True)
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas.create_window((0,0), window=self.canvas_frame, anchor="nw")
        self.root.bind_all("<MouseWheel>", mouse_scroll)
        self.root.bind_all("<Button-4>", mouse_scroll)
        self.root.bind_all("<Button-5>", mouse_scroll)
        self.canvas_frame.bind("<Configure>", lambda event: scrollbar_update)

        #Styling
        self.canvas_frame.config(bd=0)
        self.canvas.config(bd=0)

        getChatsThread = threading.Thread(target=getChats)
        getChatsThread.daemon = True
        getChatsThread.start()

        self.root.after(1, update_chats) #update chat initial run
        self.root.mainloop()

    def new_convo(self):

        def check_user():
            self.target = user_select.get()
            msg_text = msg_entry.get()

            if None in (self.target, msg_text):
                self.check_send_thread = threading.Thread(target=check_user)
                self.check_send_thread.daemon = True
                return 1

            user_select.config(state="disabled")
            msg_entry.config(state="disabled")
            start_convo.config(state="disabled")

            if not isinstance(self.target, list):  #Make sure in proper format
                self.target = self.target.split(',')

            self.targets = []
            for target in self.target:
                self.usr.api.searchUsername(target)

                try:
                    self.usr.api.LastJson["user"]["pk"]
                    self.targets.append(target)
                except:
                    self.exists = False
                    self.usr_select_cleared = False
                    self.msg_entry_cleared = False
                    break

            else:
                self.usr.sendMessage(self.targets, msg_text)
                self.usr.api.getv2Inbox()
                self.thread_id = json.loads(self.usr.api.LastResponse.content)["inbox"]["threads"][-1]["thread_id"]
                self.exists = True

            self.check_send_thread = threading.Thread(target=check_user)
            self.check_send_thread.daemon = True

        def try_chat():
            try:
                if self.exists:
                    self.convo_run(self.thread_id, self.targets)

                else:
                    user_select.config(state="normal")
                    msg_entry.config(state="normal")
                    start_convo.config(state="normal")
                    if not self.usr_select_cleared:
                        user_select.delete(0, "end")
                        user_select.insert(0, "Target user(s)")

                    if not self.msg_entry_cleared:
                        msg_entry.delete(0, "end")
                        msg_entry.insert(0, "Message")


            except AttributeError:
                pass

            self.root.after(100, try_chat)

        def clear_usr_select():
            try:
                if not self.usr_select_cleared:
                    user_select.delete(0, "end")
                    self.usr_select_cleared = True
            except AttributeError:
                self.usr_select_cleared = False
                clear_usr_select()

        def clear_msg_entry():
            try:
                if not self.msg_entry_cleared:
                    msg_entry.delete(0, "end")
                    self.msg_entry_cleared = True
            except AttributeError:
                self.msg_entry_cleared = False
                clear_msg_entry()

        self.root.after(100, try_chat)
        self.root.title("Direct - New chat")
        self.location = "newchat"

        for item in self.root.winfo_children():
            item.destroy()

        self.check_send_thread = threading.Thread(target=check_user)
        self.check_send_thread.daemon = True
        self.root.after(100, try_chat)

        user_select = tk.Entry(self.root)
        user_select.config(
            bg="#222",
            fg="#ccc",
            font=("Helvetica", 15)
        )
        user_select.insert(0, "Target user(s)")

        msg_entry = tk.Entry(self.root)
        msg_entry.config(
            bg="#222",
            fg="#ccc",
            font=("Helvetica", 15)
        )
        msg_entry.insert(0, "Message")

        start_convo = tk.Button(self.root, command=self.check_send_thread.start, text="Start chat")
        start_convo.config(
            bg="#222",
            fg="#ccc",
            font=("Helvetica", 15)
        )

        to_home = tk.Button(self.root, command=self.homepage, text="Back")
        to_home.config(
            bg="#222",
            fg="#ccc",
            font=("Helvetica", 15)
        )

        user_select.pack(side=tk.TOP, fill=tk.X)
        msg_entry.pack(side=tk.TOP, fill=tk.X)
        start_convo.pack(side=tk.TOP, fill=tk.X)
        to_home.pack(side=tk.TOP, fill=tk.X)

        user_select.bind("<Return>", lambda event: self.check_send_thread.start())
        user_select.bind("<Key>", lambda event: clear_usr_select())
        user_select.bind("<Button-1>", lambda event: clear_usr_select())
        msg_entry.bind("<Return>", lambda event: self.check_send_thread.start())
        msg_entry.bind("<Key>", lambda event: clear_msg_entry())
        msg_entry.bind("<Button-1>", lambda event: clear_msg_entry())
        start_convo.bind("<Return>", lambda event: self.check_send_thread.start())
        start_convo.bind("<Key>", lambda event: self.check_send_thread.start())

        self.root.mainloop()

    def convo_run(self, threadId, users):

        #TODO: find some way of adding timestamp in small text in bottom corner
        #Maybe make each message a frame with multiple text widgets on it?

        #TODO: Add utilisation of image caching in pfp.py

        #TODO: Add support for other msg types

        def copy(event):
            self.root.clipboard_clear()
            self.root.clipboard_append(event.widget["text"])
            self.root.update()

        def scrollbar_update():
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        def update_convo():
            try:
                for msg in chat.pending_msgs:

                    if self.location != "convorun":
                        return

                    if msg.item_id not in chat.last_msgs:
                        msg.pack(side=tk.TOP, fill=tk.X)
                        chat.last_msgs.append(msg.item_id)

                chat.pending_msgs = []

            except AttributeError:
                pass

            #Autoscroll
            if self.vscroll.get()[1] >= 0.95 and self.scroll_req:
                self.canvas.yview_moveto(1) #Move to bottom if almost there already and new message received
                self.scroll_req = False

            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            self.root.after(100, update_convo)

        def clear_popups(event):
            self.menu.destroy()

        def update_msg_wraps():
            for widget in self.canvas_frame.winfo_children():
                if isinstance(widget, tk.Label): #NOTE: When I convert msg widgets to frames, Update this
                    widget.config(
                        wraplength=self.root.winfo_width()
                    )

        def popup(event):
            #Clear menu
            clear_popups(None)
            self.menu = tk.Menu(self.canvas_frame, tearoff=0) #Commands added in popup

            if isinstance(event.widget, tk.Label):
                self.menu.add_command(label="Copy", command=lambda event=event: copy(event))
                if event.widget.unsendable:
                    unsend_thread = threading.Thread(target=lambda thread_id=event.widget.thread_id, item_id=event.widget.item_id: self.usr.unsend(thread_id, item_id))
                    self.menu.add_command(label="Unsend", command=unsend_thread.start)
                self.menu.post(event.x_root, event.y_root)

        #Clear all widgets
        for item in self.root.winfo_children():
            item.destroy()

        self.location = "convorun"

        title = "Direct - Chatting with "
        for user in users:
            title += str(user) + ", "
        title = title[:-2]
        self.root.title(title)

        self.root.update()

        msg_in = tk.Entry(self.root)
        msg_in.config(
            bg="#222",
            fg="#ccc",
            font=("Helvetica", 12)
        )
        msg_in.pack(side=tk.BOTTOM, fill=tk.X)
        msg_in.focus_set()


        chat = Chat(self, msg_in, threadId, users)

        self.back = tk.Button(self.root, text="Return to homepage", command=self.homepage)
        self.back.config(
            bg="#222",
            fg="#ccc",
            font=("Helvetica", 12)
        )
        self.back.pack(side=tk.BOTTOM, fill=tk.X)

        #setup canvas/scrollbar
        self.canvas = tk.Canvas(self.root, scrollregion=(0, 0, 500, 500), background="#000", bd=0, highlightthickness=0)
        self.canvas_frame = tk.Frame(self.canvas, background="#000", bd=0, highlightthickness=0)
        #Setup scrollbar
        self.vscroll = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.vscroll.config(command=self.canvas.yview)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.canvas.config(yscrollcommand=self.vscroll.set)
        self.canvas.pack(fill="both", expand=True)
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas.yview_moveto(1)
        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")
        self.root.bind_all("<Configure>", lambda event: scrollbar_update)
        #Styling
        self.canvas_frame.config(bd=0)
        self.canvas.config(bd=0)
        self.root.bind("<Configure>", lambda event: update_msg_wraps())

        #Setup right click self.menu
        self.menu = tk.Menu(self.canvas_frame, tearoff=0) #Commands added in popup
        self.canvas_frame.bind_all("<Button-1>", clear_popups)
        self.canvas_frame.bind_all("<Button-3>", popup)

        #Thread setup
        get_msg_thread = threading.Thread(target=chat.get_msgs)
        get_msg_thread.daemon = True
        get_msg_thread.start()

        chat.send_msg_thread = threading.Thread(target=chat.send_msg)
        chat.send_msg_thread.daemon = True

        #Bindings
        msg_in.bind("<Return>", lambda event: chat.send_msg_thread.start())

        self.root.after(100, update_convo)
        self.root.mainloop()

def main():
    App()

if __name__ == "__main__":
    main()