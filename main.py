from fastapi import FastAPI, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI(title="Logo Generator API", version="1.0.0")


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render_logo(text: str, bg: str, fg: str, shape: str, size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bg_rgba = hex_to_rgb(bg) + (255,)

    if shape == "circle":
        draw.ellipse((0, 0, size - 1, size - 1), fill=bg_rgba)
    elif shape == "rounded":
        draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 6, fill=bg_rgba)
    else:
        draw.rectangle((0, 0, size - 1, size - 1), fill=bg_rgba)

    words = [w for w in text.strip().split() if w]
    if not words:
        initials = "?"
    elif len(words) == 1:
        initials = words[0][:2].upper()
    else:
        initials = (words[0][0] + words[1][0]).upper()

    font = ImageFont.load_default(size=int(size * 0.35))
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
        initials, font=font, fill=hex_to_rgb(fg) + (255,),
    )
    return img


class LogoRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=40)
    bg: str = "#0f172a"
    fg: str = "#38bdf8"
    shape: str = "circle"        # circle | rounded | square
    size: int = Field(512, ge=64, le=1024)


@app.get("/")
def health():
    return {"status": "ok", "service": "logo-api"}


@app.post("/logo")
def logo_post(req: LogoRequest):
    img = render_logo(req.text, req.bg, req.fg, req.shape, req.size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@app.get("/logo")
def logo_get(
    text: str = Query(..., min_length=1, max_length=40),
    bg: str = "#0f172a",
    fg: str = "#38bdf8",
    shape: str = "circle",
    size: int = Query(512, ge=64, le=1024),
):
    img = render_logo(text, bg, fg, shape, size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
