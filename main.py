from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont
import requests
import os
import base64
import io

app = FastAPI(title="AI Logo Generator API", version="14.0.0")

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"

# Font එක download කරමු
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

        # Image එක ගමු
        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            img_bytes = response.content
        else:
            result = response.json()
            if result.get("success") and "result" in result and "image" in result["result"]:
                img_bytes = base64.b64decode(result["result"]["image"])
            else:
                raise HTTPException(status_code=500, detail=f"Unexpected response: {result}")

        # Text add කරන්නද?
        if add_text:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            w, h = img.size

            # පහළින් නම ලියන්න ඉඩ තියෙනවා. ඒ නිසා උඩට ටිකක් තල්ලු කරමු.
            new_h = int(h * 1.15)
            new_img = Image.new("RGBA", (w, new_h), (255, 255, 255, 255))
            new_img.paste(img, (0, 0))

            draw = ImageDraw.Draw(new_img)

            # Font එක load කරමු
            try:
                font = ImageFont.truetype(FONT_PATH, int(w * 0.07))
            except:
                font = ImageFont.load_default(size=int(w * 0.07))

            # නම center කරමු
            text = prompt.upper()
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = (w - tw) / 2
            y = h + int(h * 0.02)

            # Text එක ලියමු (තද අළු පාටින්)
            draw.text((x, y), text, font=font, fill=(30, 30, 40, 255))

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
