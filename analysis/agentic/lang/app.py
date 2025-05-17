# app.py

from flask import Flask, request, jsonify
from trend_agent import trend_agent

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "No message provided."}), 400

        response = trend_agent.run(user_message)
        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return "✅ LangChain Gemini Agent is running.", 200

if __name__ == "__main__":
    app.run(debug=True)
