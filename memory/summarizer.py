def summarize_conversation(llm, conversation_text):

    prompt = f"""
Summarize the following conversation into important facts and context.

Conversation:
{conversation_text}

Summary:
"""

    response = llm.invoke(prompt)

    return response.content