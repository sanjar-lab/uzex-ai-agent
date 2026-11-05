"""Generate the bot logo (512x512) and description banner (640x360) into assets/.

python scripts/make_assets.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(OUT, exist_ok=True)

BG_TOP = (11, 31, 58)       # deep navy
BG_BOT = (16, 52, 92)
WHITE = (255, 255, 255)
ACCENT = (46, 204, 170)     # teal
SS = 4                      # supersampling factor

FONT_B = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_SB = r"C:\Windows\Fonts\seguisb.ttf"
FONT_R = r"C:\Windows\Fonts\segoeui.ttf"


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return img


def draw_mark(d: ImageDraw.ImageDraw, cx, cy, size):
    """Three ascending rounded bars + an 'AI' spark dot — the whole logo."""
    bw = size * 0.17          # bar width
    gap = size * 0.08
    base = cy + size * 0.36
    heights = [0.34, 0.54, 0.76]
    total_w = 3 * bw + 2 * gap
    x0 = cx - total_w / 2
    r = bw / 2
    for i, h in enumerate(heights):
        x = x0 + i * (bw + gap)
        top = base - size * h
        color = ACCENT if i == 2 else WHITE
        d.rounded_rectangle([x, top, x + bw, base], radius=r, fill=color)
    # spark (4-point star) above the tallest bar
    sx = x0 + 2 * (bw + gap) + bw / 2
    sy = base - size * heights[2] - size * 0.17
    s = size * 0.085
    d.polygon([(sx, sy - s), (sx + s * 0.28, sy - s * 0.28), (sx + s, sy), (sx + s * 0.28, sy + s * 0.28),
               (sx, sy + s), (sx - s * 0.28, sy + s * 0.28), (sx - s, sy), (sx - s * 0.28, sy - s * 0.28)], fill=ACCENT)


def logo(px=512):
    W = px * SS
    img = gradient(W, W)
    d = ImageDraw.Draw(img)
    # Telegram crops avatars to a circle: keep the mark inside the central ~60%
    draw_mark(d, W / 2, W / 2 + W * 0.02, W * 0.56)
    img = img.resize((px, px), Image.LANCZOS)
    img.save(os.path.join(OUT, "logo.png"))
    return img


def banner(w=640, h=360):
    W, H = w * SS, h * SS
    img = gradient(W, H)
    d = ImageDraw.Draw(img)
    draw_mark(d, W * 0.20, H * 0.50, H * 0.50)
    f_title = ImageFont.truetype(FONT_B, int(H * 0.135))
    f_sub = ImageFont.truetype(FONT_SB, int(H * 0.058))
    f_small = ImageFont.truetype(FONT_R, int(H * 0.048))
    tx = W * 0.37
    d.text((tx, H * 0.24), "UZEX AI-agent", font=f_title, fill=WHITE)
    d.rounded_rectangle([tx, H * 0.43, tx + W * 0.07, H * 0.43 + H * 0.012], radius=H * 0.006, fill=ACCENT)
    d.text((tx, H * 0.49), "Birja bitimlari · faqat maʼlumotlar asosida", font=f_sub, fill=WHITE)
    d.text((tx, H * 0.58), "Биржевые сделки · строго по данным", font=f_sub, fill=(200, 214, 232))
    d.text((tx, H * 0.72), "500 000 bitim · 2022–2026 · UZ / RU", font=f_small, fill=(150, 172, 200))
    img = img.resize((w, h), Image.LANCZOS)
    img.save(os.path.join(OUT, "banner.png"))
    return img


if __name__ == "__main__":
    logo()
    banner()
    print("saved to", OUT)
