from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import requests
import os

app = FastAPI(title="AI Logo Generator API", version="1.0.0")

# Render එකේ Environment Variables වලට දාන්න
HF_TOKEN = os.environ.get("HF_TOKEN")

# ශීඝ්‍රතම සහ නොමිලේ වැඩ කරන AI Model එක (Flux.1-schnell)
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}


@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'minimalist tech logo for Nima'"),
    style: str = Query("flat vector, clean, minimalist, white background, professional logo design", description="Logo style")
):
    if not HF_TOKEN:
        raise HTTPException(status_code=500, detail="HF_TOKEN not set in Render environment variables")

    # Full prompt එක හදමු
    full_prompt = f"{prompt}, {style}, high quality, 4k"

    payload = {"inputs": full_prompt}

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI model took too long to respond")

    # Model එක cold start වෙනවා නම් 503 එවනවා
    if response.status_code == 503:
        raise HTTPException(status_code=503, detail="AI model is loading. Please retry in 20-30 seconds.")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return Response(content=response.content, media_type="image/png")
