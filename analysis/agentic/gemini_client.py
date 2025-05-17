import requests

# ------------------ GEMINI CONFIG ------------------
GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY_HERE"
GEMINI_MODEL = "gemini-1.5-pro-latest"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# ------------------ SIMPLE TEXT COMPLETION ------------------
def call_gemini(prompt: str) -> str:
    """
    Calls Gemini with a free-form prompt (no tools).
    Returns plain text output from Gemini.
    """
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    
    except Exception as e:
        return f"❌ Gemini API Error: {str(e)}"
