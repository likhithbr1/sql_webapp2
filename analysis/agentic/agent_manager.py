import requests

# ------------------ GEMINI CONFIG ------------------
GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY_HERE"
GEMINI_MODEL = "gemini-1.5-pro-latest"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# ------------------ TOOL SCHEMA ------------------
extract_intent_tool = {
    "name": "extract_intent",
    "description": (
        "Classify the user's intent into one of the following categories: "
        "'trend_analysis', 'forecasting', 'product_bundling', 'performance_metrics'. "
        "If the intent is unclear, ask a clarifying question."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_message": {
                "type": "string",
                "description": "The full message from the user"
            }
        },
        "required": ["user_message"]
    }
}
intent_tools = [extract_intent_tool]

# ------------------ INTENT DETECTOR ------------------
def detect_intent(user_input: str) -> str:
    """
    Sends the user message to Gemini with the extract_intent tool schema.
    Returns one of: 'trend_analysis', 'forecasting', 'product_bundling', 'performance_metrics'
    """
    headers = {"Content-Type": "application/json"}

    body = {
        "contents": [{"role": "user", "parts": [{"text": user_input}]}],
        "tools": intent_tools,
        "toolConfig": {
            "functionCallingConfig": {
                "mode": "AUTO"
            }
        }
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()

        candidate = result.get("candidates", [])[0]
        parts = candidate.get("content", {}).get("parts", [])

        if parts and "functionCall" in parts[0]:
            tool_call = parts[0]["functionCall"]
            intent = tool_call["args"]["user_message"]
            return intent.strip()

        elif parts and "text" in parts[0]:
            # Gemini couldn't decide clearly
            print(f"Gemini: {parts[0]['text']}")
            return "unknown"

    except Exception as e:
        print(f"❌ Error detecting intent: {e}")

    return "unknown"
