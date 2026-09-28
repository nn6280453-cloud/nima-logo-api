from fastapi import FastAPI, Query
from fastapi.responses import Response
import requests
import urllib.parse
import random

app = FastAPI(title="AI Logo Generator API", version="4.0.0")

@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}

@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'Nima Tech'"),
    style: str = Query("logo design, minimalist, flat vector, clean lines, simple icon, centered, white background, professional branding, high quality, vivid colors, no text, no letters, no words, no 3d, no realistic, no photo")
):
    # 1. Prompt එක හදමු
    full_prompt = f"{prompt}, {style}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 2. Random seed එකක් දාමු (හැම පාරම අලුත් design එකක් එන්න)
    seed = random.randint(1, 999999)
    
    # 3. 🔴 Watermark අයින් කරන්න, හොඳම model එක (flux), සහ අලුත් seed එක
    api_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1024&height=1024"
        f"&nologo=true&model=flux&seed={seed}&enhance=true"
    )
    
    try:
        response = requests.get(api_url, timeout=90)
        
        if response.status_code != 200:
            return Response(content=f"Error from AI provider: {response.text}", status_code=response.status_code)
            
        return Response(content=response.content, media_type="image/jpeg")
        
    except requests.exceptions.Timeout:
        return Response(content="AI model took too long to respond. Please try again.", status_code=504)
    except Exception as e:
        return Response(content=f"Connection error: {str(e)}", status_code=500)
