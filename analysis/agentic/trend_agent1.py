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
                "monthly_sales": {"type": "string", "description": "JSON string of monthly sales data"}
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
        print("[DEBUG] TrendAnalysisAgent initialized with", len(trend_analysis_tool_schemas), "tools")

    def run(self):
        print("📈 Trend Analysis Agent: Hi! I can help you analyze sales trends.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            self.chat.add_user_message(user_input)
            result = self.chat.call()
            
            print(f"[DEBUG] Tool call result type: {result['type']}")

            if result["type"] == "reply":
                print(f"🧠 {result['text']}")

            elif result["type"] == "tool_call":
                tool = result["tool"]
                args = result["args"]
                print(f"[DEBUG] Calling tool: {tool} with args: {args}")

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
                        self.chat.add_user_message("No database selected. Please select a valid database first.")
                    else:
                        self.product_list = load_product_list(db_name)
                        print(f"📦 Products in {db_name}:", ", ".join(self.product_list[:10]), "...")
                        self.chat.add_user_message(f"Products available in {db_name}: {', '.join(self.product_list[:20])}")

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
                        msg = f"❌ Missing {' and '.join(missing)} info."
                        print(msg)
                        self.chat.add_user_message(msg)
                    else:
                        print(f"[DEBUG] Getting monthly sales for {product_name} in {db_name}")
                        sales = get_monthly_sales(db_name, product_name)
                        print("📊 Monthly Sales:")
                        for month, total in sales.items():
                            print(f"   {month}: {total}")
                        
                        sales_json = json.dumps(sales)
                        self.chat.add_user_message(
                            f"Monthly sales data for '{product_name}': {sales_json}. Please summarize the trend."
                        )

                        # ✅ This was missing before
                        result = self.chat.call()
                        if result["type"] == "reply":
                            print("📈 Trend Summary:")
                            print(result["text"])
                        elif result["type"] == "tool_call":
                            print(f"[DEBUG] Gemini responded with another tool call: {result['tool']}({result['args']})")
                        else:
                            print("🤖 Gemini didn’t respond as expected.")

                elif tool == "summarize_trend":
                    product_name = args.get("product_name", self.product_name)
                    monthly_sales_str = args.get("monthly_sales", "{}")
                    
                    try:
                        monthly_sales = json.loads(monthly_sales_str)
                    except json.JSONDecodeError:
                        print("❌ Invalid sales data format.")
                        monthly_sales = {}
                    
                    if not product_name or not monthly_sales:
                        print("❌ Missing product name or sales data.")
                        self.chat.add_user_message("Missing information to summarize trend.")
                    else:
                        print(f"[DEBUG] Summarizing trend for {product_name}")
                        summary = summarize_trend(product_name, monthly_sales)
                        print("📈 Trend Summary:")
                        print(summary)
                        self.chat.add_user_message(f"Trend summary for {product_name}: {summary}")

            elif result["type"] == "error":
                print(f"❌ Error: {result['text']}")
