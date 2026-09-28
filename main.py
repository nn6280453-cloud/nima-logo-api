from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
import urllib.parse
import random
import os

app = FastAPI(title="AI Logo Generator API", version="8.0.0")

POLLINATIONS_API_KEY = os.environ.get("POLLINATIONS_API_KEY")


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
    if not POLLINATIONS_API_KEY:
        raise HTTPException(status_code=500, detail="POLLINATIONS_API_KEY not set")

    full_prompt = f"{prompt}, {style}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = random.randint(1, 999999)

    api_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1024&height=1024"
        f"&nologo=true&private=true&model=flux&seed={seed}&enhance=true"
        f"&key={POLLINATIONS_API_KEY}"
    )

    try:
        response = requests.get(api_url, timeout=90)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return Response(content=response.content, media_type="image/jpeg")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI took too long. Try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
