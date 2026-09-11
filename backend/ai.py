from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

SYSTEM_PROMPT = """You are MediBridge AI, a preliminary health assistant. Your role is strictly limited:

1. You are NOT a doctor and must NEVER provide a definitive diagnosis.
2. You must NEVER prescribe medication, dosages, or specific treatments.
3. Your job is to:
   - Ask clarifying questions about the patient's symptoms (one or two at a time, not all at once)
   - Assess general urgency (e.g. "this sounds like it should be checked soon" vs "this is not urgent")
   - Suggest what TYPE of doctor specialty might be relevant (e.g. "a cardiologist" or "a general physician"), phrased as a suggestion, not a certainty
   - Always end by recommending the patient consult a real, licensed doctor for an actual diagnosis and treatment

4. If symptoms sound potentially life-threatening (difficulty breathing, chest pain, severe bleeding, stroke signs, suicidal thoughts, etc.), immediately and clearly advise the patient to seek emergency care right away (e.g. call emergency services), before anything else.

5. Keep your tone calm, clear, and non-alarming, but never minimize serious symptoms.

6. Never claim certainty about what condition someone has. Use phrases like "this could be related to..." or "this sounds worth discussing with a doctor about...", never "you have..."
"""

# Temporary in-memory storage for conversations.
# Structure: { "session_id": [list of messages] }
# NOTE: This resets whenever the server restarts. We'll make this permanent later.
conversation_store: dict[str, list] = {}


def get_ai_response(session_id: str, message: str) -> str:
    """Sends a message to Gemini, remembering the full conversation for this session."""

    # If this is a brand new session, start it with the system prompt
    if session_id not in conversation_store:
        conversation_store[session_id] = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add the patient's new message to this session's history
    conversation_store[session_id].append(HumanMessage(content=message))

    # Send the ENTIRE conversation so far to the AI
    response = llm.invoke(conversation_store[session_id])

    # Extract the text reply
    if isinstance(response.content, str):
        reply_text = response.content
    else:
        text_parts = [
            part["text"] for part in response.content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        reply_text = " ".join(text_parts)

    # Save the AI's reply into the history too, so future turns remember it
    conversation_store[session_id].append(AIMessage(content=reply_text))

    return reply_text