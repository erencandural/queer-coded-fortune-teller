#!/usr/bin/env python3
import os
import tkinter as tk
from PIL import ImageTk, Image
import random

tarot_dir = "/home/erencan/fortune_teller/tarot_cards/"
target_size = (128, 213)
wrap_length = 384


def load_tarot_cards():
    cards = {}
    
    for filename in os.listdir(tarot_dir):
        if not filename.endswith((".png", ".jpg", ".jpeg")):
            continue  # skip non-image files
        
        # Strip extension for label
        name, ext = os.path.splitext(filename)
        
        # Load
        path = os.path.join(tarot_dir, filename)
        img = Image.open(path)
        
        
        # Resize
        img = img.resize(target_size, Image.LANCZOS)
        
        # Dither
        img = img.convert("1")
        
        # Store PIL image
        cards[name] = img
    
    return cards


# Create the main window
root = tk.Tk()
root.title("Fortune Teller v2")
root.geometry("464x600")

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


def draw_three_cards():
    """
    Draw three random cards, randomize orientation, and update labels.
    """
    # Draw three (name, pil_img) pairs
    three_cards = random.sample(list(tarot_cards.items()), 3)

    positions = []   # "Upright"/"Reversed"
    tk_images = []   # (name, tk_img)

    for name, pil_img in three_cards:
        if random.choice([True, False]):
            pos = "Upright"
            img_to_use = pil_img
        else:
            pos = "Reversed"
            img_to_use = pil_img.rotate(180)

        positions.append(pos)

        # Convert PIL image (maybe rotated) to Tk image
        tk_img = ImageTk.PhotoImage(img_to_use)
        tk_images.append((name, tk_img))

    (past_name, past_img), (present_name, present_img), (future_name, future_img) = tk_images

    # Update labels' text + image
    past_card.config(text=f"Past\n{past_name}\n{positions[0]}", image=past_img)
    present_card.config(text=f"Present\n{present_name}\n{positions[1]}", image=present_img)
    future_card.config(text=f"Future\n{future_name}\n{positions[2]}", image=future_img)

    # Keep references so Tk doesn't garbage-collect images
    past_card.image = past_img
    present_card.image = present_img
    future_card.image = future_img


# "Draw Again" button
draw_button = tk.Button(root, text="Draw Again", command=draw_three_cards)
draw_button.grid(row=3, column=0, columnspan=3, pady=10)

# Initial draw
draw_three_cards()

# Run forever
root.mainloop()
