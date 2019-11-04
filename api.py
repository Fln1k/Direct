#!/usr/bin/env python3

import json

import imageio
from InstagramAPI import InstagramAPI

imageio.plugins.ffmpeg.download() #Ensure installed

class User: #Setup custom user class
    def __init__(self, usr_name, password):
        self.name = usr_name
        self.api = InstagramAPI(usr_name, password)

        InstagramAPI.USER_AGENT = "Instagram 99.0.0.19.93 Android (5000/5000.0; 1dpi; 1x1; noname; noname; noname; noname)"
        #Setup custom UA to ensure reading dms allowed

    def sendMessage(self, target, msgText):
        targets = []
        if type(target) != type([]):
            target = [target]

        for user in target:
            try:
                int(user)
                targets.append(str(user))
            except ValueError:
                target = self.api.searchUsername(user)
                try:
                    targets.append(str(self.api.LastJson["user"]["pk"]))
                except:
                    return ValueError("Invalid User")

        url = "direct_v2/threads/broadcast/text/"

        target = "[[{}]]".format(",".join([str(user) for user in targets]))
        data = {
            "text": msgText,
            "_uuid": self.api.uuid,
            "_csrftoken": self.api.token,
            "recipient_users": target,
            "_uid": self.api.username_id,
            "action": "send_item",
            "client_context": self.api.generateUUID(True)}

        return self.api.SendRequest(url, data)

    def getChats(self):
        #TODO: Find some way of checking if thread is unread
        self.api.getv2Inbox()
        content = json.loads(self.api.LastResponse.content)["inbox"]["threads"]
        chats = []
        for chat in content:
            users = []
            if len(chat["users"]) == 0:
                self.api.searchUsername(self.name)
                response = json.loads(json.dumps(self.api.LastJson))
                chats.append({
                    "thread_name": self.name,
                    "thread_id"  : chat["thread_id"],
                    "users"      : [self.name],
                    "thread_icon": response["user"]["profile_pic_url"]
                })
                continue

            for user in chat["users"]:
                users.append(user["username"])

            chats.append({
                "thread_name": chat["thread_title"],
                "thread_id"  : chat["thread_id"],
                "users"      : [user["username"] for user in chat["users"]],
                "thread_icon": chat["users"][0]["profile_pic_url"]
            })

        return chats

    def getMessages(self, chat_id):
        self.api.getv2Threads(str(chat_id))
        thread = json.loads(json.dumps(self.api.LastJson))["thread"]

        users = {} #Get list of people
        for user in thread["users"]:
            users[user["pk"]] = user["username"]

        items = [] #List of dict(UID: Item data)

        for item in thread["items"]:
            type = item["item_type"]
            # TODO: Add new messages in this order: image, link, profile
            if type == "text":
                items.append({"user"    : item["user_id"],
                              "text"    : " " * 4 + item["text"],
                              "time"    : item["timestamp"],
                              "item_id" : item["item_id"],
                              "show_pfp": True})

            elif type == "video_call_event":
                items.append({"user"    : item["user_id"],
                              "text"    : " " * 4 + item["video_call_event"]["description"],
                              "time"    : item["timestamp"],
                              "item_id" : item["item_id"],
                              "show_pfp": False})

            elif type == "like":
                items.append({"user"    : item["user_id"],
                              "text"    : u" \u2764\uFE0F",
                              "time"    : item["timestamp"],
                              "item_id" : item["item_id"],
                              "show_pfp": True})

            else:
                items.append({"user"    : item["user_id"],
                              "text"    : "    Unsupported message type: " + item["item_type"],
                              "time"    : item["timestamp"],
                              "item_id" : item["item_id"],
                              "show_pfp": True})

        return items

    def unsend(self, thread_id, item_id):
        thread_id = str(thread_id)
        item_id = str(item_id)
        endpoint = "direct_v2/threads/"+thread_id+"/items/"+item_id+"/delete/"
        data = {
            "_uuid": self.api.uuid,
            "_csrftoken": self.api.token}

        response = self.api.s.post(self.api.API_URL + endpoint, data=data)

        if response.status_code == 200:
            self.api.LastResponse = response
            self.api.LastJson = json.loads(response.text)
            return True

        else:
            try:
                self.api.LastResponse = response
                self.api.LastJson = json.loads(response.text)
            except:
                pass

            return False