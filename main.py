from fastapi import FastAPI, Query
from fastapi.responses import Response
import requests
import urllib.parse

app = FastAPI(title="AI Logo Generator API", version="3.0.0")

@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}

@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'Nima Tech'"),
    style: str = Query("minimalist vector logo, flat design, clean lines, simple, white background, professional brand mark, high quality, no 3d, no realistic")
):
    # 1. Prompt එක හදමු (ලස්සන, පැතලි, නවීන ලොගෝ එකක් එන්න)
    full_prompt = f"{prompt}, {style}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 2. 🔴 Watermark එක අයින් කරන්න &nologo=true සහ හොඳම model එක (flux) දාමු
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux"
    
    try:
        # AI එකට image එක හදන්න වෙලා යන නිසා timeout එක 90 කරා
        response = requests.get(api_url, timeout=90)
        
        if response.status_code != 200:
            return Response(content=f"Error from AI provider: {response.text}", status_code=response.status_code)
            
        return Response(content=response.content, media_type="image/jpeg")
        
    except requests.exceptions.Timeout:
        return Response(content="AI model took too long to respond. Please try again.", status_code=504)
    except Exception as e:
        return Response(content=f"Connection error: {str(e)}", status_code=500)
