from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
import os
import base64

app = FastAPI(title="AI Logo Generator API", version="6.0.0")

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}


@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'Nima Tech'"),
    style: str = Query(
        "minimalist vector logo, flat design, clean lines, simple, "
        "white background, professional brand identity, modern, "
        "high quality, no 3d, no realistic, no photo"
    )
):
    if not TOGETHER_API_KEY:
        raise HTTPException(status_code=500, detail="TOGETHER_API_KEY not set")

    full_prompt = f"{prompt}, {style}"

    api_url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": full_prompt,
        "width": 1024,
        "height": 1024,
        "steps": 4,
        "n": 1,
        "response_format": "b64_json"
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        result = response.json()
        img_base64 = result["data"][0]["b64_json"]
        img_bytes = base64.b64decode(img_base64)

        return Response(content=img_bytes, media_type="image/png")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI took too long")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
