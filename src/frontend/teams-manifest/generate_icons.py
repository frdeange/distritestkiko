"""
Generate placeholder icons for the Teams manifest.
Run once: python generate_icons.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

DIR = os.path.dirname(os.path.abspath(__file__))

def create_color_icon():
    """192x192 color icon."""
    img = Image.new("RGBA", (192, 192), (0, 120, 212, 255))  # #0078D4
    draw = ImageDraw.Draw(img)
    # Draw "DP" text centered
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except OSError:
        font = ImageFont.load_default()
    text = "DP"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((192 - w) / 2, (192 - h) / 2 - 10), text, fill="white", font=font)
    img.save(os.path.join(DIR, "color.png"))
    print("Created color.png (192x192)")

def create_outline_icon():
    """32x32 outline icon (transparent bg, single color)."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    text = "DP"
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((32 - w) / 2, (32 - h) / 2 - 2), text, fill=(0, 120, 212, 255), font=font)
    img.save(os.path.join(DIR, "outline.png"))
    print("Created outline.png (32x32)")

if __name__ == "__main__":
    create_color_icon()
    create_outline_icon()
