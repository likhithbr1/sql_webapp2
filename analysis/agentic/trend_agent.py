from gemini_chat_agent import GeminiChatAgent
from trend_analysis_tools import (
    list_databases,
    validate_database,
    load_product_list,
    validate_product_name,
    get_monthly_sales,
    summarize_trend,
)

# ------------------ TOOL SCHEMAS ------------------

trend_analysis_tool_schemas = [
    {
        "name": "list_databases",
        "description": "Returns the list of valid databases available for analysis.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "validate_database",
        "description": "Validates the database name. Suggests correction if invalid.",
        "parameters": {
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "Database name"}
            },
            "required": ["db_name"]
        }
    },
    {
        "name": "load_product_list",
        "description": "Loads list of products from a given database.",
        "parameters": {
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "Database name"}
            },
            "required": ["db_name"]
        }
    },
    {
        "name": "validate_product_name",
        "description": "Checks if product exists and suggests correction if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "product_list": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["product_name", "product_list"]
        }
    },
    {
        "name": "get_monthly_sales",
        "description": "Aggregates daily sales to monthly sales for a product in a database.",
        "parameters": {
            "type": "object",
            "properties": {
                "db_name": {"type": "string"},
                "product_name": {"type": "string"}
            },
            "required": ["db_name", "product_name"]
        }
    },
    {
        "name": "summarize_trend",
        "description": "Analyzes monthly sales and returns a classification of the trend.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "monthly_sales": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                }
            },
            "required": ["product_name", "monthly_sales"]
        }
    }
]

# ------------------ AGENT CLASS ------------------

class TrendAnalysisAgent:
    def __init__(self):
        self.chat = GeminiChatAgent(tools=trend_analysis_tool_schemas)
        self.db_name = None
        self.product_name = None
        self.product_list = []

    def run(self):
        print("📈 Trend Analysis Agent: Hi! I can help you analyze sales trends.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            self.chat.add_user_message(user_input)
            result = self.chat.call()

            if result["type"] == "reply":
                print(f"🧠 {result['text']}")

            elif result["type"] == "tool_call":
                tool = result["tool"]
                args = result["args"]

                if tool == "list_databases":
                    dbs = list_databases()
                    print("📂 Available Databases:", ", ".join(dbs))

                elif tool == "validate_database":
                    outcome = validate_database(args["db_name"])
                    if outcome["status"] == "valid":
                        self.db_name = outcome["db_name"]
                        print(f"✅ Selected DB: {self.db_name}")
                    elif outcome["status"] == "suggest":
                        print(f"🤔 Did you mean '{outcome['suggestion']}'?")
                    else:
                        print("❌ Invalid DB name.")

                elif tool == "load_product_list":
                    if not self.db_name:
                        print("⚠️ Please select a valid database first.")
                    else:
                        self.product_list = load_product_list(self.db_name)
                        print(f"📦 Products in {self.db_name}:", ", ".join(self.product_list[:10]), "...")

                elif tool == "validate_product_name":
                    result = validate_product_name(args["product_name"], args["product_list"])
                    if result["status"] == "valid":
                        self.product_name = result["product_name"]
                        print(f"✅ Product selected: {self.product_name}")
                    elif result["status"] == "suggest":
                        print(f"🤔 Did you mean '{result['suggestion']}'?")
                    else:
                        print("❌ Product not found.")

                elif tool == "get_monthly_sales":
                    if self.db_name and self.product_name:
                        sales = get_monthly_sales(self.db_name, self.product_name)
                        print("📊 Monthly Sales:")
                        for month, total in sales.items():
                            print(f"   {month}: {total}")
                        # Now pass back to Gemini for summarization
                        self.chat.add_user_message(
                            f"Please summarize the trend for '{self.product_name}' using this sales data: {sales}"
                        )
                        result = self.chat.call()
                        print("📈", result.get("text"))
                    else:
                        print("❌ Missing DB or product info.")

                elif tool == "summarize_trend":
                    summary = summarize_trend(args["product_name"], args["monthly_sales"])
                    print("📈 Trend Summary:")
                    print(summary)
