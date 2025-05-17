from agent_manager import detect_intent
from trend_agent import TrendAnalysisAgent
# from forecasting_agent import ForecastingAgent  # For future use
# from bundling_agent import ProductBundlingAgent  # For future use

def main():
    print("👋 Welcome to the Gemini Assistant!")
    print("You can ask about trend analysis, forecasting, product bundling, and more.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        # Step 1: Use Gemini to detect intent
        intent = detect_intent(user_input)
        print(f"🔍 Detected intent: {intent}")

        # Step 2: Route to the correct intent agent
        if intent == "trend_analysis":
            agent = TrendAnalysisAgent()
            agent.chat.add_user_message(user_input)  # seed the conversation
            agent.run()

        elif intent == "forecasting":
            print("📈 ForecastingAgent coming soon!")

        elif intent == "product_bundling":
            print("📦 ProductBundlingAgent coming soon!")

        elif intent == "performance_metrics":
            print("📊 PerformanceMetricsAgent coming soon!")

        else:
            print("❓ Sorry, I couldn't understand your request. Try saying something like:")
            print("   'Show me the trend for product cap in eon'")

if __name__ == "__main__":
    main()
