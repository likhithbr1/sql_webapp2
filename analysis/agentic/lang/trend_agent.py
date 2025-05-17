from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from tool_registry import registered_tools

# --------------- CONFIG -------------------
GEMINI_API_KEY = "your_actual_gemini_api_key_here"  # Replace securely in prod

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.3,
    google_api_key=GEMINI_API_KEY  # 🔐 Explicitly passed
)

# --------------- MEMORY -------------------
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# --------------- AGENT -------------------
trend_agent = initialize_agent(
    tools=registered_tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,  # Use function-calling style
    memory=memory,
    verbose=True
)
