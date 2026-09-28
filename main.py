from fastapi import FastAPI, Query
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests

app = FastAPI(title="Logo Generator API", version="5.0.0")

# ලස්සන Font එක auto download කරමු
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
FONT_PATH = "Montserrat-Bold.ttf"

if not os.path.exists(FONT_PATH):
    try:
        r = requests.get(FONT_URL, timeout=15)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"Font download failed: {e}")

# පාට තේමා (color themes) - ඔයාට කැමති එකක් තෝරන්න පුළුවන්
THEMES = {
    "tech":    {"bg1": "#0f172a", "bg2": "#1e293b", "fg": "#38bdf8", "accent": "#0ea5e9"},
    "sunset":  {"bg1": "#7c2d12", "bg2": "#ea580c", "fg": "#fef3c7", "accent": "#fbbf24"},
    "forest":  {"bg1": "#064e3b", "bg2": "#065f46", "fg": "#a7f3d0", "accent": "#10b981"},
    "royal":   {"bg1": "#1e1b4b", "bg2": "#312e81", "fg": "#c7d2fe", "accent": "#818cf8"},
    "rose":    {"bg1": "#4c0519", "bg2": "#881337", "fg": "#fecdd3", "accent": "#fb7185"},
    "gold":    {"bg1": "#1c1917", "bg2": "#292524", "fg": "#fde68a", "accent": "#f59e0b"},
    "ocean":   {"bg1": "#082f49", "bg2": "#0c4a6e", "fg": "#bae6fd", "accent": "#0ea5e9"},
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def create_gradient(size, c1, c2):
    """Diagonal gradient background එකක් හදනවා"""
    img = Image.new("RGB", (size, size), c1)
    top = Image.new("RGB", (size, size), c2)
    mask = Image.new("L", (size, size))
    md = ImageDraw.Draw(mask)
    for i in range(size * 2):
        md.line([(i, 0), (0, i)], fill=int(255 * (i / (size * 2))), width=2)
    img.paste(top, (0, 0), mask)
    return img


def render_logo(text, theme, shape, size):
    t = THEMES.get(theme, THEMES["tech"])
    bg1 = hex_to_rgb(t["bg1"])
    bg2 = hex_to_rgb(t["bg2"])
    fg = hex_to_rgb(t["fg"])
    accent = hex_to_rgb(t["accent"])
    
    # Gradient background
    img = create_gradient(size, bg1, bg2).convert("RGBA")
    
    # Shape mask එකක් හදමු
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    margin = int(size * 0.05)
    
    if shape == "circle":
        md.ellipse((margin, margin, size - margin, size - margin), fill=255)
    elif shape == "rounded":
        md.rounded_rectangle((margin, margin, size - margin, size - margin), radius=size // 5, fill=255)
    elif shape == "hexagon":
        pts = []
        import math
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            x = size / 2 + (size / 2 - margin) * math.cos(angle)
            y = size / 2 + (size / 2 - margin) * math.sin(angle)
            pts.append((x, y))
        md.polygon(pts, fill=255)
    else:
        md.rounded_rectangle((margin, margin, size - margin, size - margin), radius=size // 12, fill=255)
    
    img.putalpha(mask)
    draw = ImageDraw.Draw(img)
    
    # Inner ring එකක් (glow effect එකක් සමඟ)
    ring_margin = int(size * 0.10)
    ring_width = max(2, int(size * 0.012))
    ring_color = accent + (180,)
    
    if shape == "circle":
        draw.ellipse((ring_margin, ring_margin, size - ring_margin, size - ring_margin),
                     outline=ring_color, width=ring_width)
    elif shape == "rounded":
        draw.rounded_rectangle((ring_margin, ring_margin, size - ring_margin, size - ring_margin),
                                radius=(size // 5) - ring_margin, outline=ring_color, width=ring_width)
    
    # Initials ටික ගමු
    words = [w for w in text.strip().split() if w]
    if not words:
        initials = "?"
    elif len(words) == 1:
        initials = words[0][:2].upper()
    else:
        initials = (words[0][0] + words[1][0]).upper()
    
    # Font load කරමු
    try:
        font = ImageFont.truetype(FONT_PATH, int(size * 0.32))
    except:
        font = ImageFont.load_default(size=int(size * 0.32))
    
    # Text එක center කරමු
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - int(size * 0.02)
    
    # 1. Text Shadow එක (ගැඹුරු බවක් දෙන්න)
    shadow_offset = int(size * 0.012)
    draw.text((x + shadow_offset, y + shadow_offset), initials, font=font, fill=(0, 0, 0, 180))
    
    # 2. ඇත්ත Text එක (accent පාටින් outline එකක් සමඟ)
    outline_width = max(1, int(size * 0.003))
    draw.text((x, y), initials, font=font, fill=fg + (255,),
              stroke_width=outline_width, stroke_fill=accent + (255,))
    
    # 3. පහළින් විස්තර (small text)
    try:
        small_font = ImageFont.truetype(FONT_PATH, int(size * 0.055))
    except:
        small_font = ImageFont.load_default(size=int(size * 0.055))
    
    subtitle = text.upper()
    if len(subtitle) > 18:
        subtitle = subtitle[:18]
    
    bbox2 = draw.textbbox((0, 0), subtitle, font=small_font)
    tw2 = bbox2[2] - bbox2[0]
    x2 = (size - tw2) / 2 - bbox2[0]
    y2 = y + th + int(size * 0.06)
    
    draw.text((x2, y2), subtitle, font=small_font, fill=fg + (200,))
    
    return img


@app.get("/")
def health():
    return {"status": "ok", "service": "logo-api-v5"}


@app.get("/logo")
def logo(
    text: str = Query(..., description="ලොගෝ එකේ නම (උදා: 'Nima Tech')"),
    theme: str = Query("tech", description="tech, sunset, forest, royal, rose, gold, ocean"),
    shape: str = Query("circle", description="circle, rounded, hexagon, square"),
    size: int = Query(512, ge=128, le=1024),
):
    img = render_logo(text, theme, shape, size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
