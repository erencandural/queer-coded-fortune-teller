#!/usr/bin/env python3
import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image, ImageOps, ImageEnhance
import random
from escpos.printer import Serial
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

tarot_dir = BASE_DIR / "tarot_cards/"
meanings_path = BASE_DIR / "tarot_card_meanings.json"

# Serial settings
PORT = "/dev/serial0"
BAUD = 9600

target_size = (109, 181)
wrap_length = 300

#       _     _   _  _   __ 
#  |_| |_ |  |_) |_ |_) (_  
#  | | |_ |_ |   |_ | \ __) 
                          

def load_meanings():
    with open(meanings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_tarot_cards():
    """
    Returns dict: card_id -> PIL.Image (dithered, resized)
    where card_id == filename without extension.
    """
    cards = {}

    for filename in os.listdir(tarot_dir):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        card_id, _ = os.path.splitext(filename)

        path = os.path.join(tarot_dir, filename)
        img = Image.open(path)

        img = img.resize(target_size, Image.LANCZOS)
        # ~ img = img.convert("1")  # dither/1-bit

        cards[card_id] = img

    return cards


def pick_meaning(meanings, card_id, is_upright):
    """
    Returns (pretty_name, meaning_text).
    Falls back gracefully if JSON entry is missing.
    """
    entry = meanings.get(card_id)
    if not entry:
        pretty_name = card_id.replace("_", " ")
        meaning = "(No meaning found in JSON)"
        return pretty_name, meaning

    pretty_name = entry.get("name", card_id.replace("_", " "))
    meaning = entry.get("upright" if is_upright else "reversed", "(Meaning missing)")
    return pretty_name, meaning

def wrap_for_printer(text, width=32):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + (1 if line else 0) <= width:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return "\n".join(lines)

class TarotPage(tk.Frame):
    
    def __init__(self, parent, controller):
        super().__init__(parent)

        screen_w = 320
        screen_h = 480
        center_x = screen_w // 2

        # Setting up the background
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.controller = controller

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
            center_x, 25,
            text="Tarot Cards Reading",
            font=("Courier", 16),
            justify="center",
            anchor="n",
            fill="black"
        )

        self.controller = controller

        self.meanings = load_meanings()
        self.tarot_cards = load_tarot_cards()

        # Tarot Frame

        self.tarot_frame = tk.Frame(self.canvas, bg="gold")
        self.canvas.create_window(center_x, 50, window=self.tarot_frame, width=300, anchor="center")

        for col in range(3):
            self.tarot_frame.columnconfigure(col, weight=1, uniform="tarot")

        self.tarot_frame.rowconfigure(0, weight=1)

        # Empty labels for the three cards
        self.past_card = tk.Label(self.tarot_frame, text="Past", compound="top")
        self.present_card = tk.Label(self.tarot_frame, text="Present", compound="top")
        self.future_card = tk.Label(self.tarot_frame, text="Future", compound="top")

        self.past_card.grid(row=2, column=0)
        self.present_card.grid(row=2, column=1)
        self.future_card.grid(row=2, column=2)

        # A single meaning box under the 3 cards (cleaner than 3 separate blocks)
        self.meaning_label = tk.Label(
            self.tarot_frame,
            text="",
            wraplength=wrap_length,
            justify=tk.LEFT
        )
        self.meaning_label.grid(row=3, column=0, columnspan=3) 

        # Create a list of dictionaries
        self.current_draw = []


        #  _     ___ ___ _        __ 
        # |_) | | |   | / \ |\ | (_  
        # |_) |_| |   | \_/ | \| __) 

        self.button_frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window(center_x, 430, window=self.button_frame, width=300, anchor="center")

        for col in range(3):
            self.button_frame.columnconfigure(col, weight=1, uniform="buttons")

        for row in range(2):
            self.button_frame.rowconfigure(row, weight=1, uniform="buttons")

        draw_button = ttk.Button(
            self.button_frame,
            text="Draw again",
            command=self.draw_three_cards
        )

        print_button = ttk.Button(
            self.button_frame,
            text="Print\nFortune",
            command=self.print_fortune
        )

        draw_button.grid(row=0, column=0, columnspan=2, sticky="nsew")
        print_button.grid(row=0, column=2, sticky="nsew")

        pc_button = ttk.Button(
            self.button_frame,
            text="Playing Cards\nReading",
            command=lambda: controller.show_frame("PCPage")
        )

        home_button = ttk.Button(
            self.button_frame,
            text="Home\nPage",
            command=lambda: controller.show_frame("StartPage")
        )

        quit_button = ttk.Button(
            self.button_frame,
            text="Quit",
            command=controller.destroy
        )
        
        pc_button.grid(row=1, column=0, sticky="nsew")
        home_button.grid(row=1, column=1, sticky="nsew")
        quit_button.grid(row=1, column=2, sticky="nsew")

        self.draw_three_cards()

    def draw_three_cards(self):
        picks = random.sample(list(self.tarot_cards.items()), 3)
        slots = [("Past", self.past_card), ("Present", self.present_card), ("Future", self.future_card)]

        self.current_draw = []
        meanings_text = []   # <-- fix name

        for (slot_name, slot_label), (card_id, base_img) in zip(slots, picks):
            is_upright = random.choice([True, False])
            orientation = "Upright" if is_upright else "Reversed"

            final_img = base_img if is_upright else base_img.rotate(180, expand=False)

            pretty_name, meaning = pick_meaning(self.meanings, card_id, is_upright)

            tk_img = ImageTk.PhotoImage(final_img, master=self)
            slot_label.config(
                text=f"{slot_name}\n{pretty_name}\n{orientation}",
                image=tk_img,
                compound="top",
            )
            slot_label.image = tk_img

            meanings_text.append(f"{slot_name} — {pretty_name} ({orientation})\n{meaning}\n")

            self.current_draw.append({
                "slot": slot_name,
                "card_id": card_id,
                "pretty_name": pretty_name,
                "upright": is_upright,
                "img": final_img,
                "meaning": meaning,
            })

        self.meaning_label.config(text="\n".join(meanings_text))

    def print_fortune(self):
        if len(self.current_draw) != 3:
            return  # or show an error dialog

        entire_fortune = Image.new("L", (target_size[0] * 3, target_size[1]))

        entire_fortune.paste(self.current_draw[0]["img"].convert("L"), (0, 0))
        entire_fortune.paste(self.current_draw[1]["img"].convert("L"), (target_size[0], 0))
        entire_fortune.paste(self.current_draw[2]["img"].convert("L"), (2 * target_size[0], 0))

        # Enhance (works only on L/RGB, so do it BEFORE converting to 1-bit)
        entire_fortune = ImageOps.autocontrast(entire_fortune)
        entire_fortune = ImageEnhance.Contrast(entire_fortune).enhance(1.4)
        entire_fortune = ImageEnhance.Sharpness(entire_fortune).enhance(1.8)
        
        printer = Serial(
            devfile=PORT,
            baudrate=BAUD,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False,
            profile="POS-5890",
        )
        try:
            printer.set(align="center", bold=True, double_height=True, double_width=True)
            printer.textln("Queer Coded\nFortune Teller")
            
            printer.set_with_default()
            
            printer.set(align="center")
            printer.textln('(coded by a queer)')
            
            printer.set_with_default()
            
            printer.print_and_feed(1)
            time.sleep(0.25)
            
            printer.image(entire_fortune)
            printer.text("\n")

            # Print meanings (left aligned, wrapped)
            printer.set_with_default()
            for item in self.current_draw:
                orientation = "Upright" if item["upright"] else "Reversed"
                header = f'{item["slot"]}:\n{item["pretty_name"]} ({orientation})'
                printer.textln(header)
                printer.textln("-" * min(len(header), 32))
                printer.text(wrap_for_printer(item["meaning"], width=32))
                printer.text("\n\n")

            printer.text("\n\n\n")

        finally:
            printer.close()