import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is not set")
    
client = anthropic.Anthropic(
    api_key=api_key
)

def ask_claude(context, question):

    prompt = f"""
    Context:
    {context}

    Question:
    {question}
    """

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text