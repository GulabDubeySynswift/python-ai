import os
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from tools.vector_search_tool import vector_search
from tools.general_llm_tool import general_llm
from dotenv import load_dotenv
from tools.db_query_tool import db_query

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is not set")

llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    temperature=0,
    api_key=api_key
)

tools = [general_llm, db_query, vector_search]
 
# memory
memory = MemorySaver()

agent = create_react_agent(
    llm, 
    tools,
    checkpointer=memory
)
