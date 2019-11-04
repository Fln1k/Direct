#!/usr/bin/env python3

import tkinter as tk
from io import BytesIO
import requests

from PIL import Image, ImageTk, ImageOps, ImageDraw

# Note - This stores and provides an easy interface for accessing pfps, to reduce load times

pictures = {} # {pic_url: picture}

def retrieve_picture(pic_url):

    if pic_url in pictures and pictures[pic_url]:
        return pictures[pic_url]

    response = requests.get(pic_url)

    if response.status_code == 200: #Check image received ok
        tk.Tk()
        tmp_img = Image.open(BytesIO(response.content))
        tmp_img = tmp_img.resize((50, 50))
        #Generate mask for circularising image
        mask = Image.new("L", (50, 50), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + mask.size, fill=255)
        tmp_img = ImageOps.fit(tmp_img, mask.size, centering=(.5, .5))
        tmp_img.putalpha(mask)
        image = ImageTk.PhotoImage(tmp_img)
        #Save image
        pictures[pic_url] = image
        return image
