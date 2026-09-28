from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
import requests
import os
import base64
import io

app = FastAPI(title="AI Logo Generator API", version="15.0.0")

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf"
FONT_PATH = "Montserrat-Bold.ttf"

if not os.path.exists(FONT_PATH):
    try:
        r = requests.get(FONT_URL, timeout=15)
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"Font download failed: {e}")


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}


@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'Nima Tech'"),
    add_text: bool = Query(True, description="නම add කරන්නද?"),
    style: str = Query(
        "a single minimalist emblem, one badge, one symbol, one mark, "
        "flat vector illustration, geometric shape, modern brand identity, "
        "clean simple design, centered, isolated on pure white background, "
        "professional, high detail, 4k"
    )
):
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        raise HTTPException(status_code=500, detail="Cloudflare credentials not set")

    full_prompt = f"a single modern emblem symbol for {prompt}, {style}"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": full_prompt}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            img_bytes = response.content
        else:
            result = response.json()
            if result.get("success") and "result" in result and "image" in result["result"]:
                img_bytes = base64.b64decode(result["result"]["image"])
            else:
                raise HTTPException(status_code=500, detail=f"Unexpected response: {result}")

        # ✅ අලුත් text block එක
        if add_text:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            w, h = img.size

            new_h = int(h * 1.18)
            new_img = Image.new("RGBA", (w, new_h), (255, 255, 255, 255))
            new_img.paste(img, (0, 0))

            draw = ImageDraw.Draw(new_img)

            try:
                font = ImageFont.truetype(FONT_PATH, int(w * 0.06))
            except:
                font = ImageFont.load_default(size=int(w * 0.06))

            text = prompt.upper()
            letter_spacing = int(w * 0.015)
            total_width = 0
            letters = []
            for ch in text:
                bbox_ch = draw.textbbox((0, 0), ch, font=font)
                ch_w = bbox_ch[2] - bbox_ch[0]
                letters.append((ch, ch_w))
                total_width += ch_w + letter_spacing
            total_width -= letter_spacing

            x = (w - total_width) / 2
            y = h + int(h * 0.025)

            for ch, ch_w in letters:
                draw.text((x, y), ch, font=font, fill=(25, 35, 55, 255))
                x += ch_w + letter_spacing

            line_y = int(y + h * 0.085)
            line_x1 = int(w * 0.35)
            line_x2 = int(w * 0.65)
            line_color = (150, 160, 175, 200)
            draw.line([(line_x1, line_y), (line_x2, line_y)], fill=line_color, width=max(1, int(w * 0.003)))

            buf = io.BytesIO()
            new_img.save(buf, format="PNG")
            buf.seek(0)
            return Response(content=buf.read(), media_type="image/png")

        return Response(content=img_bytes, media_type="image/png")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI took too long. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
