#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 800, 1100

# Create image with gradient
img = Image.new('RGB', (W, H), color='#e8f5e9')
draw = ImageDraw.Draw(img)

# Gradient background (green tones)
for y in range(H):
    ratio = y / H
    r = int(232 - ratio * 60)
    g = int(245 - ratio * 50)
    b = int(233 - ratio * 60)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Decorative circles
from PIL import ImageDraw
draw.ellipse([500, -150, 950, 300], fill=(255, 255, 255, 80))
draw.ellipse([-100, 800, 300, 1200], fill=(255, 255, 255, 60))

# Fonts
font_title = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 88)
font_sub = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 22)
font_date = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 42)
font_date_sub = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 20)
font_normal = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 18)
font_english = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 17)

# Text helper
def draw_centered(draw, text, y, font, fill, spacing=0):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + (bbox[3] - bbox[1]) + 4

# Content
y = 80
draw_centered(draw, "春暖花开  踏青时节", y, font_sub, '#558b2f')

y = 120
draw_centered(draw, "清明假期", y, font_title, '#2e7d32')

y = 210
draw_centered(draw, "QINGMING FESTIVAL HOLIDAY", y, font_english, '#689f38')

# Divider
y = 250
for x in range(W // 2 - 70, W // 2 + 70):
    alpha = 1 - abs(x - W // 2) / 70
    draw.line([(x, y), (x, y + 1)], fill=(85, 139, 47, int(alpha * 200)))

y = 280
draw_centered(draw, "放 假 时 间", y, font_normal, '#689f38')

y = 320
draw_centered(draw, "4月4日 — 4月6日", y, font_date, '#2e7d32')

y = 370
draw_centered(draw, "共三天 · 周六至周一", y, font_date_sub, '#558b2f')

# Tips box
box_y = 430
box_h = 180
box_x = 120
box_w = 560

# Semi-transparent rounded rect
box_img = Image.new('RGBA', (W, H), (255, 255, 255, 0))
box_draw = ImageDraw.Draw(box_img)
box_draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=18, fill=(255, 255, 255, 95))
img = img.convert('RGBA')
img = Image.alpha_composite(img, box_img)
draw = ImageDraw.Draw(img)

draw_centered(draw, "温 馨 提 示", box_y + 15, font_normal, '#2e7d32')

tips = [
    "🌿  祭扫出行，注意安全",
    "🌿  错峰踏青，文明出游",
    "🌿  提前安排工作，假期安心休息",
]
tip_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 17)
ty = box_y + 55
for tip in tips:
    bbox = draw.textbbox((0, 0), tip, font=tip_font)
    tw = bbox[2] - bbox[0]
    tx = (W - tw) // 2
    draw.text((tx, ty), tip, font=tip_font, fill='#388e3c')
    ty += 38

# Footer
draw_centered(draw, "— 清明时节 · 万物清明 —", 950, font_normal, '#81c784')

# Save
out_path = "/Users/lobster/workspace/lali/qingming-poster.png"
img = img.convert('RGB')
img.save(out_path, 'PNG', quality=95)
print(f"Saved to {out_path}")
print(f"Size: {img.size}")
