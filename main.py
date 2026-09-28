from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
import os
import base64

app = FastAPI(title="AI Logo Generator API", version="11.0.0")

# Render Environment Variables වලට දාන්න
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

# 🔴 FLUX.1-schnell — Cloudflare එකේ නොමිලේ දෙන හොඳම AI model එක
MODEL = "@cf/black-forest-labs/flux-1-schnell"
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}


@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'Nima Tech'"),
    style: str = Query(
        "logo design, minimalist, flat vector, simple icon, clean lines, "
        "centered, isolated on white background, professional brand identity, "
        "no text, no letters, no words, no 3d, no realistic, no photo, no people"
    )
):
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        raise HTTPException(status_code=500, detail="Cloudflare credentials not set")

    full_prompt = f"{prompt}, {style}"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": full_prompt}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        result = response.json()

        # Cloudflare එකෙන් image එක base64 විදියට එවනවා
        if result.get("success") and "result" in result and "image" in result["result"]:
            img_base64 = result["result"]["image"]
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected response: {result}")

        img_bytes = base64.b64decode(img_base64)
        return Response(content=img_bytes, media_type="image/jpeg")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI took too long. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
