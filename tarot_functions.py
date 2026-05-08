#!/usr/bin/env python3
import os
import json
import tkinter as tk
from PIL import ImageTk, Image, ImageOps, ImageEnhance
import random
# from escpos.printer import Serial
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

tarot_dir = BASE_DIR / "tarot_cards/"
meanings_path = BASE_DIR / "tarot_card_meanings.json"

target_size = (128, 216)
wrap_length = 384

# Serial settings
PORT = "/dev/serial0"
BAUD = 9600

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


# Create the main window
root = tk.Tk()
root.title("Fortune Teller v3")
root.geometry("464x700")

meanings = load_meanings()
tarot_cards = load_tarot_cards()

# Title
title_label = tk.Label(
    root,
    text="Queer Coded Fortune Teller",
    justify=tk.CENTER,
    font=("Arial", 16),
)
title_label.grid(row=0, column=0, columnspan=3, pady=5)

# Description
desc_text = (
    "The most basic tarot spread is the three card spread. "
    "The cards drawn represent the past, the present and the future respectively."
)
desc_label = tk.Label(
    root,
    text=desc_text,
    wraplength=wrap_length,
    justify=tk.CENTER
)
desc_label.grid(row=1, column=0, columnspan=3, padx=40, pady=5)

# Empty labels for the three cards
past_card = tk.Label(root, text="Past", compound="top")
present_card = tk.Label(root, text="Present", compound="top")
future_card = tk.Label(root, text="Future", compound="top")

past_card.grid(row=2, column=0, padx=0, pady=4)
present_card.grid(row=2, column=1, padx=0, pady=4)
future_card.grid(row=2, column=2, padx=0, pady=4)

# A single meaning box under the 3 cards (cleaner than 3 separate blocks)
meaning_label = tk.Label(
    root,
    text="",
    wraplength=wrap_length,
    justify=tk.LEFT
)
meaning_label.grid(row=3, column=0, columnspan=3, padx=40, pady=10)

# Create a list of dictionaries
current_draw = []


def draw_three_cards():
    global current_draw

    picks = random.sample(list(tarot_cards.items()), 3)
    slots = [("Past", past_card), ("Present", present_card), ("Future", future_card)]

    current_draw = []
    meanings_text = []   # <-- fix name

    for (slot_name, slot_label), (card_id, base_img) in zip(slots, picks):
        is_upright = random.choice([True, False])
        orientation = "Upright" if is_upright else "Reversed"

        final_img = base_img if is_upright else base_img.rotate(180, expand=False)

        pretty_name, meaning = pick_meaning(meanings, card_id, is_upright)

        tk_img = ImageTk.PhotoImage(final_img, master=root)
        slot_label.config(
            text=f"{slot_name}\n{pretty_name}\n{orientation}",
            image=tk_img,
            compound="top",
        )
        slot_label.image = tk_img

        meanings_text.append(f"{slot_name} — {pretty_name} ({orientation})\n{meaning}\n")

        current_draw.append({
            "slot": slot_name,
            "card_id": card_id,
            "pretty_name": pretty_name,
            "upright": is_upright,
            "img": final_img,
            "meaning": meaning,
        })

    meaning_label.config(text="\n".join(meanings_text))

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

def print_fortune():
    if len(current_draw) != 3:
        return  # or show an error dialog

    entire_fortune = Image.new("L", (target_size[0] * 3, target_size[1]))

    entire_fortune.paste(current_draw[0]["img"].convert("L"), (0, 0))
    entire_fortune.paste(current_draw[1]["img"].convert("L"), (target_size[0], 0))
    entire_fortune.paste(current_draw[2]["img"].convert("L"), (2 * target_size[0], 0))

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
        for item in current_draw:
            orientation = "Upright" if item["upright"] else "Reversed"
            header = f'{item["slot"]}:\n{item["pretty_name"]} ({orientation})'
            printer.textln(header)
            printer.textln("-" * min(len(header), 32))
            printer.text(wrap_for_printer(item["meaning"], width=32))
            printer.text("\n\n")

        printer.text("\n\n\n")

    finally:
        printer.close()



# "Draw Again" button
draw_button = tk.Button(root, text="Draw Again", command=draw_three_cards)
draw_button.grid(row=4, column=0, columnspan=1, pady=10)

# Initial draw
three_cards = draw_three_cards()

# "Print Fortune" Button
print_button = tk.Button(root, text="Print Fortune", command=print_fortune)
print_button.grid(row=4, column=1, columnspan=1, pady=10)

# Run forever
root.mainloop()
