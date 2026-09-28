from fastapi import FastAPI, Query
from fastapi.responses import Response
import requests
import urllib.parse

app = FastAPI(title="AI Logo Generator API", version="2.0.0")

@app.get("/")
def health():
    return {"status": "ok", "service": "ai-logo-api"}

@app.get("/ai-logo")
def generate_ai_logo(
    prompt: str = Query(..., description="උදා: 'minimalist tech logo for Nima'"),
    style: str = Query("flat vector, clean, minimalist, white background, professional logo design")
):
    # Prompt එක හදලා URL එකට ගැලපෙන විදියට encode කරමු
    full_prompt = f"{prompt}, {style}, high quality, 4k"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 🔴 නොමිලේ වැඩ කරන Pollinations AI ලින්ක් එක (Token අවශ්‍ය නැත)
    api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    
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
