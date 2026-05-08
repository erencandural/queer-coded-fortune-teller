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

playing_cards_dir = BASE_DIR / "playing_cards/"
meanings_path = BASE_DIR / "playing_card_meanings.json"

# Serial settings
PORT = "/dev/serial0"
BAUD = 9600

target_screen_size = (90, 130)
target_print_size = (128, 186)
wrap_length = 300

#       _     _   _  _   __ 
#  |_| |_ |  |_) |_ |_) (_  
#  | | |_ |_ |   |_ | \ __) 
                          

def load_meanings():
    with open(meanings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_playing_cards():
    """
    Returns dict: card_id -> PIL.Image (dithered, resized)
    where card_id == filename without extension.
    """
    cards = {}

    for filename in os.listdir(playing_cards_dir):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        card_id, _ = os.path.splitext(filename)

        path = os.path.join(playing_cards_dir, filename)
        img = Image.open(path)

        screen_img = img.resize(target_screen_size, Image.LANCZOS)

        cards[card_id] = {
            "screen": screen_img,
            "path": path,
        }

    return cards

def pick_meaning(meanings, card_id):
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
    meaning = entry.get("meaning", "(Meaning missing)")
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

class PCPage(tk.Frame):
    
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.configure(bg="white")

        self.grid_rowconfigure(0, weight=0)  # title
        self.grid_rowconfigure(1, weight=1)  # cards
        self.grid_rowconfigure(2, weight=0)  # buttons

        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label = tk.Label(
            self,
            text="Playing Cards Reading",
            font=("Bodoni MT Poster Compressed", 16),
            bg="white"
        )
        self.title_label.grid(row=0, column=0, pady=(10, 5))

        self.cards_frame = tk.Frame(self, bg="white")
        self.cards_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        for col in range(3):
            self.cards_frame.columnconfigure(col, weight=1, uniform="cards")

        self.button_frame = tk.Frame(self, bg="white")
        self.button_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5, 10))


        self.meanings = load_meanings()
        self.playing_cards = load_playing_cards()

        # Empty labels for the three cards
        self.past_card = tk.Label(self.cards_frame, text="Past", compound="top")
        self.present_card = tk.Label(self.cards_frame, text="Present", compound="top")
        self.future_card = tk.Label(self.cards_frame, text="Future", compound="top")

        self.past_card.grid(row=0, column=0, sticky="n")
        self.present_card.grid(row=0, column=1, sticky="n")
        self.future_card.grid(row=0, column=2, sticky="n")

        # Create a list of dictionaries
        self.current_draw = []


        #  _     ___ ___ _        __ 
        # |_) | | |   | / \ |\ | (_  
        # |_) |_| |   | \_/ | \| __) 

        for col in range(3):
            self.button_frame.columnconfigure(col, weight=1, uniform="buttons")

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

        home_button = ttk.Button(
            self.button_frame,
            text="Home\nPage",
            command=lambda: controller.show_frame("StartPage")
        )

        draw_button.grid(row=0, column=0, sticky="nsew")
        print_button.grid(row=0, column=1, sticky="nsew")
        home_button.grid(row=0, column=2, sticky="nsew")

        self.draw_three_cards()
    
    def draw_three_cards(self):
        picks = random.sample(list(self.playing_cards.items()), 3)

        slots = [
            ("Past", self.past_card),
            ("Present", self.present_card),
            ("Future", self.future_card),
        ]

        self.current_draw = []

        for (slot_name, slot_label), (card_id, card_data) in zip(slots, picks):
            base_img = card_data["screen"]
            is_upright = random.choice([True, False])
            orientation = "Upright" if is_upright else "Reversed"

            final_img = base_img if is_upright else base_img.rotate(180, expand=False)
            pretty_name, meaning = pick_meaning(self.meanings, card_id, is_upright)

            tk_img = ImageTk.PhotoImage(final_img, master=self)

            slot_label.config(
                text=f"{slot_name}\n{pretty_name}\n{orientation}",
                image=tk_img,
                compound="top",
                bg="white"
            )
            slot_label.image = tk_img

            self.current_draw.append({
                "slot": slot_name,
                "card_id": card_id,
                "pretty_name": pretty_name,
                "upright": is_upright,
                "img": final_img,
                "path": card_data["path"],
                "meaning": meaning,
            })
    
    def print_fortune(self):
        if len(self.current_draw) != 3:
            return

        entire_fortune = Image.new("L", (target_print_size[0] * 3, target_print_size[1]))

        print_imgs = []

        for item in self.current_draw:
            img = Image.open(item["path"]).convert("RGBA")
            img = img.resize(target_print_size, Image.LANCZOS)

            if not item["upright"]:
                img = img.rotate(180, expand=False)

            print_imgs.append(img.convert("L"))

        entire_fortune = Image.new("L", (target_print_size[0] * 3, target_print_size[1]))

        entire_fortune.paste(print_imgs[0], (0, 0))
        entire_fortune.paste(print_imgs[1], (target_print_size[0], 0))
        entire_fortune.paste(print_imgs[2], (2 * target_print_size[0], 0))

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
            printer.textln("(coded by a queer)")

            printer.set_with_default()
            printer.print_and_feed(1)
            time.sleep(0.25)

            printer.set(align="center")
            printer.image(entire_fortune)
            printer.text("\n")

            printer.set_with_default()

            for item in self.current_draw:
                orientation = "Upright" if item["upright"] else "Reversed"

                header = f'{item["slot"]}:\n{item["pretty_name"]} ({orientation})'

                printer.set(align="left", bold=True)
                printer.textln(header)
                printer.set_with_default()

                printer.textln("-" * 32)
                printer.text(wrap_for_printer(item["meaning"], width=32))
                printer.text("\n\n")

            printer.text("\n\n\n")

        finally:
            printer.close()