from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from tool_registry import registered_tools

# ---- Gemini LLM with system prompt binding ----
GEMINI_API_KEY = "your_actual_gemini_api_key_here"

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.3,
    google_api_key=GEMINI_API_KEY
).bind(system_message="""
You are a conversational assistant that performs product trend analysis.

Follow this logic:
1. If user doesn't provide both `database` and `product`, ask for the missing info.
2. When user gives a value, validate using tools:
   - Use `validate_database` and `load_product_list`
   - Then `validate_product_name`
3. Once both are valid, call `get_monthly_sales` → then `summarize_trend`
4. Always use tools. Don’t hallucinate values.
5. Maintain conversation context.
""")

# ---- Memory for multi-turn tracking ----
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# ---- Conversational ReAct agent ----
trend_agent = initialize_agent(
    tools=registered_tools,
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)
