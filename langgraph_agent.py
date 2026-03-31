from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
from agents.claude_agent import llm

# define state
class State(TypedDict):
    input: str
    response: str

@tool(description="This is a tool for form builder form")
def form_builder_tool(query: str) -> Dict[str, Any]:
    prompt = f"""
    You are a form builder AI.

    Convert the user request into JSON form schema.

    Rules:
    - Return ONLY JSON
    - Fields must have: name, type, label, required
    - Supported types: text, number, date, email, select

    User request:
    {query}
    """

    response = llm.invoke(prompt)
    
    print(response.content)
    return {
        "response": response.content,
        "type": "form",
        "title": "Generated Form",
        "fields": [],
    }

@tool
def tool1(query: str) -> str:
    """This tool returns a greeting message."""

    print(f"Tool1 Receive Query: {query}")
    return "hi i m tool1"
    
def call_tool1(state):
    print("tool1 calling...", state)
    
    query = state.get("input", "")
    result = form_builder_tool.invoke({"query": query})
    
    return {"response": result}

@tool(description="This is tool2")
def tool2(query: str) -> str:

    print(f"Tool2 Receive Query: {query}")
    return "hi i m tool2"

def call_tool2(state):
    print("tool2 calling...", state)

    query = state.get("input", "")
    result = tool2.invoke({"query": query})

    return {"response": result}

def decide(state):
    print(f"Decideing...", state)

    query = state.get("input", "")
    if "MongoDB" in query:
        return "tool2"
    return "tool1"
# graph
graph = StateGraph(State)

graph.add_node("tool1", call_tool1)
# graph.add_node("tool2", call_tool2)

graph.set_entry_point("tool1")
# graph.add_edge("tool1", "tool2")
graph.add_edge("tool1", END)

# graph.add_conditional_edges(
#     "tool1", 
#     decide, 
#     {
#         "tool2": "tool2",
#         "tool1": END 
#     }
# )

app = graph.compile()

app.invoke({"input": "Create a form with name, age and dob"})