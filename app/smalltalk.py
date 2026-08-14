import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()
GROQ_MODEL = os.getenv("GROQ_MODEL")
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def talk(question, conversation_history=None):
    """
    Handle small-talk conversations using Groq.

    conversation_history contains the previous chat messages
    so the model understands conversational context.
    """
    messages = [
        {
            "role": "system",
            "content": """
You are a friendly e-commerce chatbot.

Handle casual conversations naturally.

IMPORTANT:
- Understand the user's message in the context of the previous conversation.
- If the user is answering a previous question, respond appropriately to that answer.
- Do not repeat a question that was already answered.
- Keep small-talk responses short and natural.
- If the user says "good", "fine", "great", "okay", etc.,
  treat it as a response to the previous conversational question.
- Do not suddenly restart the conversation.
- Do not talk about products unless the user asks about products.
"""
        }
    ]

    # Add previous conversation
    if conversation_history:

        for message in conversation_history:

            messages.append(
                {
                    "role": message["role"],
                    "content": message["content"]
                }
            )

    # Add current question
    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=200
    )

    return response.choices[0].message.content