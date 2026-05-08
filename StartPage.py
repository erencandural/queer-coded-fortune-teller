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

wrap_length = 320

BASE_DIR = Path(__file__).resolve().parent

tarot_dir = BASE_DIR / "tarot_cards/"
meanings_path = BASE_DIR / "tarot_card_meanings.json"

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.controller = controller

        screen_w = 320
        screen_h = 480
        center_x = screen_w // 2

        # Background image
        card_back = Image.open(BASE_DIR / "card_back.png").convert("RGBA")
        card_back = card_back.resize((320, 480), Image.LANCZOS) # 245, 418 works nicely

        alpha = card_back.getchannel("A")
        alpha = alpha.point(lambda p: int(p * 0.22))   # try 0.15 to 0.30
        card_back.putalpha(alpha)

        self.bg_image = ImageTk.PhotoImage(card_back)

        # Center the card back on the screen
        self.canvas.create_image(center_x, screen_h // 2, image=self.bg_image, anchor="center")

        # Title
        self.canvas.create_text(
            center_x, 15,
            text="Queer Coded\nFortune Teller",
            font=("Courier", 16),
            justify="center",
            anchor="n",
            fill="black"
        )

        # Description
        desc_text = (
            "Tell your fortune either with tarot cards or playing cards. The most basic tarot spread is the three card spread. The cards drawn represent the past, the present and the future respectively."
        )

        self.canvas.create_text(
            center_x, 65,
            text=desc_text,
            width=300,
            justify="center",
            anchor="n",
            fill="black"
        )

        # Main image
        fortune_teller_image = Image.open(BASE_DIR / "fortune_teller_painting.png").convert("RGBA")
        fortune_teller_image = fortune_teller_image.resize((220, 165), Image.LANCZOS)
        self.fortune_teller_tk_img = ImageTk.PhotoImage(fortune_teller_image)

        self.canvas.create_image(
            center_x, 160,
            image=self.fortune_teller_tk_img,
            anchor="n"
        )

        # Credits
        credit_text = "This Queer fortune teller was coded by this queer:\nOmer Erencan Dural"

        self.canvas.create_text(
            center_x, 400,
            text=credit_text,
            width=300,
            justify="center",
            anchor="s",
            fill="black"
        ) 

        # Buttons row

        self.button_frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window(center_x, 450, window=self.button_frame, width=300, anchor="center")

        for col in range(3):
            self.button_frame.columnconfigure(col, weight=1, uniform="buttons")

        self.button_frame.rowconfigure(0, weight=1)

        tarot_button = ttk.Button(
            self.button_frame,
            text="Tarot Cards\nReading",
            command=lambda: controller.show_frame("TarotPage")
        )

        pc_button = ttk.Button(
            self.button_frame,
            text="Playing Cards\nReading",
            command=lambda: controller.show_frame("PCPage")
        )

        quit_button = ttk.Button(
            self.button_frame,
            text="Quit",
            command=controller.destroy
        )
        
        tarot_button.grid(row=0, column=0, sticky="nsew")
        pc_button.grid(row=0, column=1, sticky="nsew")
        quit_button.grid(row=0, column=2, sticky="nsew")
         