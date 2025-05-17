import requests

# ------------------ GEMINI CONFIG ------------------
GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY_HERE"
GEMINI_MODEL = "gemini-1.5-pro-latest"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# ------------------ CHAT AGENT ------------------
class GeminiChatAgent:
    def __init__(self, tools=None):
        """
        :param tools: List of function tool schemas this agent can call
        """
        self.history = []
        self.tools = tools if tools else []

    def add_user_message(self, message: str):
        self.history.append({
            "role": "user",
            "parts": [{"text": message}]
        })

    def add_agent_message(self, message: str):
        self.history.append({
            "role": "model",
            "parts": [{"text": message}]
        })

    def call(self):
        """
        Calls Gemini with memory + tool support.
        Returns one of:
          - {type: "reply", text: "..."}
          - {type: "tool_call", tool: "...", args: {...}}
        """
        headers = {"Content-Type": "application/json"}
        body = {
            "contents": self.history,
            "tools": self.tools,
            "toolConfig": {
                "functionCallingConfig": {
                    "mode": "AUTO"  # Let Gemini decide when to call a tool
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
                return {
                    "type": "tool_call",
                    "tool": parts[0]["functionCall"]["name"],
                    "args": parts[0]["functionCall"]["args"]
                }

            elif parts and "text" in parts[0]:
                message = parts[0]["text"]
                self.add_agent_message(message)
                return {"type": "reply", "text": message}

            else:
                return {"type": "unknown", "text": "No response."}

        except Exception as e:
            return {"type": "error", "text": f"❌ Gemini API Error: {str(e)}"}
