from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
import os
import base64

app = FastAPI(title="AI Logo Generator API", version="12.0.0")

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

# 🔴 SDXL Base 1.0 — ලොගෝ හදන්න ගොඩක් හොඳ model එකක්
MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}


@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'Nima Tech'"),
    style: str = Query(
        "professional logo design for company, minimalist emblem, "
        "flat vector illustration, geometric icon, modern branding, "
        "clean simple design, centered composition, isolated on white background, "
        "high detail, 4k, trending on dribbble, behance"
    )
):
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        raise HTTPException(status_code=500, detail="Cloudflare credentials not set")

    # 🔴 prompt එක ගොඩක් ශක්තිමත් කරමු
    full_prompt = f"logo for {prompt}, {style}"

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": full_prompt}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        # SDXL එකෙන් සමහර වෙලාවට raw bytes එනවා, සමහර වෙලාවට JSON
        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            return Response(content=response.content, media_type=content_type)

        result = response.json()
        if result.get("success") and "result" in result and "image" in result["result"]:
            img_base64 = result["result"]["image"]
            img_bytes = base64.b64decode(img_base64)
            return Response(content=img_bytes, media_type="image/png")
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected response: {result}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI took too long. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
