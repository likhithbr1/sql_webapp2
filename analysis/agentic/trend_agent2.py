from gemini_chat_agent import GeminiChatAgent
from trend_analysis_tools import (
    list_databases,
    validate_database,
    load_product_list,
    validate_product_name,
    get_monthly_sales,
    summarize_trend,
)
import json


trend_analysis_tool_schemas = [
    {"name": "list_databases", "description": "Returns the list of valid databases available for analysis.", "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "validate_database", "description": "Validates the database name. Suggests correction if invalid.", "parameters": {"type": "object", "properties": {"db_name": {"type": "string"}}, "required": ["db_name"]}},
    {"name": "load_product_list", "description": "Loads list of products from a given database.", "parameters": {"type": "object", "properties": {"db_name": {"type": "string"}}, "required": ["db_name"]}},
    {"name": "validate_product_name", "description": "Checks if product exists and suggests correction if needed.", "parameters": {"type": "object", "properties": {"product_name": {"type": "string"}, "product_list": {"type": "array", "items": {"type": "string"}}}, "required": ["product_name", "product_list"]}},
    {"name": "get_monthly_sales", "description": "Aggregates daily sales to monthly sales for a product in a database.", "parameters": {"type": "object", "properties": {"db_name": {"type": "string"}, "product_name": {"type": "string"}}, "required": ["db_name", "product_name"]}},
    {"name": "summarize_trend", "description": "Analyzes monthly sales and returns a classification of the trend.", "parameters": {"type": "object", "properties": {"product_name": {"type": "string"}, "monthly_sales": {"type": "string"}}, "required": ["product_name", "monthly_sales"]}}
]


class TrendAnalysisAgent:
    def __init__(self):
        self.chat = GeminiChatAgent(tools=trend_analysis_tool_schemas)
        self.db_name = None
        self.product_name = None
        self.product_list = []
        print("[DEBUG] TrendAnalysisAgent initialized with", len(trend_analysis_tool_schemas), "tools")

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
                print(f"[DEBUG] Calling tool: {result['tool']}({result['args']})")
                self._handle_tool(result["tool"], result["args"])
                self._continue_until_reply()
            else:
                print("❓ Unrecognized result type.")

    def _continue_until_reply(self, max_loops=5):
        for _ in range(max_loops):
            result = self.chat.call()
            print(f"[DEBUG] Chained call type: {result['type']}")
            if result["type"] == "reply":
                print(f"🧠 {result['text']}")
                break
            elif result["type"] == "tool_call":
                print(f"[DEBUG] Chained tool: {result['tool']}({result['args']})")
                self._handle_tool(result["tool"], result["args"])
            else:
                print("⚠️ Unexpected result type.")
                break

    def _handle_tool(self, tool, args):
        if tool == "list_databases":
            dbs = list_databases()
            print("📂 Available Databases:", ", ".join(dbs))
            self.chat.add_user_message(f"Available databases: {', '.join(dbs)}")

        elif tool == "validate_database":
            db_name = args.get("db_name", "")
            outcome = validate_database(db_name)
            if outcome["status"] == "valid":
                self.db_name = outcome["db_name"]
                print(f"✅ Selected DB: {self.db_name}")
                self.chat.add_user_message(f"Database '{self.db_name}' is valid and selected.")
            elif outcome["status"] == "suggest":
                print(f"🤔 Did you mean '{outcome['suggestion']}'?")
                self.chat.add_user_message(f"Database '{db_name}' not found. Did you mean '{outcome['suggestion']}'?")
            else:
                print("❌ Invalid DB name.")
                self.chat.add_user_message(f"Database '{db_name}' not found. Please try another database.")

        elif tool == "load_product_list":
            db_name = args.get("db_name", self.db_name)
            if not db_name:
                print("⚠️ Please select a valid database first.")
                self.chat.add_user_message("No database selected.")
            else:
                self.product_list = load_product_list(db_name)
                print(f"📦 Products in {db_name}:", ", ".join(self.product_list[:10]), "...")
                self.chat.add_user_message(f"Products available: {', '.join(self.product_list[:20])}")

        elif tool == "validate_product_name":
            product_name = args.get("product_name", "")
            product_list = args.get("product_list", self.product_list)
            if not product_list and self.db_name:
                self.product_list = load_product_list(self.db_name)
                product_list = self.product_list
            result = validate_product_name(product_name, product_list)
            if result["status"] == "valid":
                self.product_name = result["product_name"]
                print(f"✅ Product selected: {self.product_name}")
                self.chat.add_user_message(f"Product '{self.product_name}' is valid and selected.")
            elif result["status"] == "suggest":
                print(f"🤔 Did you mean '{result['suggestion']}'?")
                self.chat.add_user_message(f"Product '{product_name}' not found. Did you mean '{result['suggestion']}'?")
            else:
                print("❌ Product not found.")
                self.chat.add_user_message(f"Product '{product_name}' not found in the database.")

        elif tool == "get_monthly_sales":
            db_name = args.get("db_name", self.db_name)
            product_name = args.get("product_name", self.product_name)
            if not db_name or not product_name:
                missing = []
                if not db_name: missing.append("database")
                if not product_name: missing.append("product")
                self.chat.add_user_message(f"Missing {' and '.join(missing)} info.")
            else:
                print(f"[DEBUG] Getting monthly sales for {product_name} in {db_name}")
                sales = get_monthly_sales(db_name, product_name)
                for month, total in sales.items():
                    print(f"   {month}: {total}")
                sales_json = json.dumps(sales)
                self.chat.add_user_message(
                    f"Monthly sales data for '{product_name}': {sales_json}. Please summarize the trend."
                )

        elif tool == "summarize_trend":
            product_name = args.get("product_name", self.product_name)
            monthly_sales_str = args.get("monthly_sales", "{}")
            try:
                monthly_sales = json.loads(monthly_sales_str)
            except json.JSONDecodeError:
                print("❌ Could not decode sales JSON.")
                return
            print(f"[DEBUG] Summarizing trend for {product_name}")
            summary = summarize_trend(product_name, monthly_sales)
            print("📈 Trend Summary:")
            print(summary)
            self.chat.add_user_message(f"Trend summary for {product_name}: {summary}")
