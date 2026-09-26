#!/usr/bin/env python3
import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image, ImageOps, ImageEnhance
import random
# from escpos.printer import Serial
import time
from pathlib import Path

from StartPage import StartPage
from TarotPage import TarotPage
from PCPage import PCPage

wrap_length = 320

BASE_DIR = Path(__file__).resolve().parent

tarot_dir = BASE_DIR / "tarot_cards/"
meanings_path = BASE_DIR / "tarot_card_meanings.json"
 
class qcftApp(tk.Tk):
    
    # __init__ function for class qcftApp 
    def __init__(self, *args, **kwargs): 
        
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        # self.geometry("480x320")
        self.attributes('-fullscreen', True)
        self.resizable(False, False)
        self.title("Queer Coded Fortune Teller")
        
        # creating a container
        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True) 
 
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
 
        # initializing frames to an empty array
        self.frames = {}

        pages = {
            "StartPage": StartPage,
            "TarotPage": TarotPage,
            "PCPage": PCPage     
        }
 
        # iterating through a tuple consisting
        # of the different page layouts
        for name, PageClass in pages.items():
            frame = PageClass(container, self)
            self.frames[name] = frame
            frame.grid(row = 0, column = 0, sticky ="nsew")
 
        self.show_frame("StartPage")
 
    # to display the current frame passed as
    # parameter
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
 

# Driver Code
app = qcftApp()
app.mainloop()
