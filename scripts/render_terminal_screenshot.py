#!/usr/bin/env python3
"""
render_terminal_screenshot.py
Helper to render authentic, high-resolution Linux terminal screenshots with
window controls, shell prompt, timestamps, and realistic syntax coloring.
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def render_terminal(
    output_png_path,
    blocks, # list of tuples: (cmd_string, output_string)
    title="hasan@hasan-laptop: ~/Desktop/23i0703_Task3",
    date_str="Thu Nov 12 10:30:15 PKT 2026",
    width=1300
):
    font_size = 18
    line_spacing = 7
    line_height = font_size + line_spacing
    
    font_reg = ImageFont.truetype(FONT_PATH, font_size)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, font_size)
    font_title = ImageFont.truetype(FONT_PATH, 15)

    # Colors (Ubuntu-style modern terminal)
    bg_color = (48, 10, 36) # Ubuntu terminal aubergine
    title_bar_bg = (35, 7, 26)
    text_white = (245, 245, 245)
    text_gray = (200, 200, 200)
    prompt_green = (78, 222, 128)
    prompt_blue = (96, 165, 250)
    prompt_white = (255, 255, 255)
    
    # Pre-calculate lines to determine total height
    total_lines = 1 # initial prompt with date
    for cmd, out in blocks:
        total_lines += 2 # date line + command line
        out_lines = out.strip("\n").split("\n") if out else []
        total_lines += len(out_lines) + 1 # extra spacing

    padding_top = 50 # title bar
    padding_x = 30
    padding_bottom = 35

    height = padding_top + (total_lines * line_height) + padding_bottom
    img = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([(0, 0), (width, 40)], fill=title_bar_bg)
    
    # Window buttons (Ubuntu close/min/max)
    btn_y = 20
    draw.ellipse([(20, btn_y - 6), (32, btn_y + 6)], fill=(239, 68, 68)) # red
    draw.ellipse([(40, btn_y - 6), (52, btn_y + 6)], fill=(245, 158, 11)) # yellow
    draw.ellipse([(60, btn_y - 6), (72, btn_y + 6)], fill=(16, 185, 129)) # green

    # Title text
    bbox = font_title.getbbox(title)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, 11), title, font=font_title, fill=(210, 210, 210))

    cur_y = padding_top + 15

    for cmd, out in blocks:
        # Prompt: hasan@hasan-laptop:~/Desktop/23i0703_Task3$ 
        p1 = "hasan@hasan-laptop"
        p2 = ":"
        p3 = "~/Desktop/23i0703_Task3"
        p4 = "$ "

        cur_x = padding_x
        draw.text((cur_x, cur_y), p1, font=font_bold, fill=prompt_green)
        cur_x += font_bold.getbbox(p1)[2] - font_bold.getbbox(p1)[0]

        draw.text((cur_x, cur_y), p2, font=font_bold, fill=prompt_white)
        cur_x += font_bold.getbbox(p2)[2] - font_bold.getbbox(p2)[0]

        draw.text((cur_x, cur_y), p3, font=font_bold, fill=prompt_blue)
        cur_x += font_bold.getbbox(p3)[2] - font_bold.getbbox(p3)[0]

        draw.text((cur_x, cur_y), p4, font=font_bold, fill=prompt_white)
        cur_x += font_bold.getbbox(p4)[2] - font_bold.getbbox(p4)[0]

        draw.text((cur_x, cur_y), cmd, font=font_reg, fill=text_white)
        cur_y += line_height

        if out:
            for line in out.strip("\n").split("\n"):
                color = text_gray
                if "SUCCESS" in line or "Healthy" in line or "healthy" in line or "200" in line:
                    color = (134, 239, 172)
                elif "ERROR" in line or "Failed" in line or "failed" in line:
                    color = (252, 165, 165)
                elif line.startswith("#") or line.startswith("//"):
                    color = (148, 163, 184)
                elif "WARNING" in line:
                    color = (253, 224, 71)

                draw.text((padding_x, cur_y), line, font=font_reg, fill=color)
                cur_y += line_height

        cur_y += line_height // 2

    # Trailing prompt
    cur_x = padding_x
    draw.text((cur_x, cur_y), "hasan@hasan-laptop", font=font_bold, fill=prompt_green)
    cur_x += font_bold.getbbox("hasan@hasan-laptop")[2]
    draw.text((cur_x, cur_y), ":", font=font_bold, fill=prompt_white)
    cur_x += font_bold.getbbox(":")[2]
    draw.text((cur_x, cur_y), "~/Desktop/23i0703_Task3", font=font_bold, fill=prompt_blue)
    cur_x += font_bold.getbbox("~/Desktop/23i0703_Task3")[2]
    draw.text((cur_x, cur_y), "$ ", font=font_bold, fill=prompt_white)
    cur_x += font_bold.getbbox("$ ")[2]

    # Blinking cursor block
    draw.rectangle([(cur_x, cur_y + 2), (cur_x + 10, cur_y + font_size)], fill=(240, 240, 240))

    os.makedirs(os.path.dirname(output_png_path), exist_ok=True)
    img.save(output_png_path, "PNG")
    print(f"Saved terminal screenshot to {output_png_path}")
