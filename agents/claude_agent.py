import os
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from tools.vector_search_tool import vector_search
from tools.general_llm_tool import general_llm
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is not set")

llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    temperature=0,
    api_key=api_key
)

tools = [vector_search, general_llm]
 
agent = create_react_agent(llm, tools)
