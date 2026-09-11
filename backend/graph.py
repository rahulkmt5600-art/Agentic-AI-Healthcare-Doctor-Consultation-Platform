from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from rag import retrieve_relevant_knowledge

from database import SessionLocal
import models

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")


class ConversationState(TypedDict):
    messages: list          # full conversation history
    stage: str               # "gathering", "urgency", "specialty", "done"
    reply: str                # the latest AI reply to send back


GATHER_PROMPT = """You are MediBridge AI, a preliminary health assistant.
You are in the SYMPTOM GATHERING stage. Ask the patient clarifying questions 
about their symptoms, ONE OR TWO at a time. Do not diagnose or prescribe.

LANGUAGE: Detect the language and style the patient is using (English, Hindi, 
Hinglish/Roman Hindi, or any other language) and respond naturally in that 
same language and style. For example, if the patient writes in Hinglish like 
"mere kamar me dard hai", respond in Hinglish too, not English. Keep your tone 
natural and conversational in whichever language you're using.

BE THOROUGH: Do not rush to a conclusion. Before you consider yourself ready to 
move to the assessment stage, make sure you have naturally explored MOST of these 
angles across the conversation (not all in one message — spread across your questions):
- What exactly the symptom feels like, and where
- How long it has lasted, and whether it's constant or comes and goes
- Severity (mild/moderate/severe), and whether it's getting better, worse, or the same
- What triggers it or makes it better/worse (movement, food, time of day, stress, etc.)
- Any related or accompanying symptoms
- Relevant history (previous similar episodes, existing conditions, injuries, medications)
- Whether it's affecting daily activities, sleep, or work

Aim for at least 4-6 patient replies before considering yourself ready, unless the 
patient describes something urgent/emergency, in which case prioritize safety over 
thoroughness and move faster.

Only once you have a genuinely well-rounded picture, end your reply with exactly 
this marker on its own line:
[READY_FOR_ASSESSMENT]

Do not mention this marker to the patient or explain it — just include it silently 
at the end of your reply once you're ready to move forward.
"""

URGENCY_AND_SPECIALTY_PROMPT = """You are MediBridge AI. Based on the full conversation so far, 
do two things clearly:

1. Give a brief urgency assessment: is this "non-urgent", "should be seen soon (within a few days)", 
   or "seek care urgently/immediately"?
2. Suggest ONE most relevant doctor specialty (e.g. General Physician, Cardiologist, Dermatologist, etc.), 
   phrased as a suggestion, not certainty.

LANGUAGE: Respond in the same language and style the patient has been using throughout 
the conversation (English, Hindi, Hinglish, or otherwise). Keep it natural and easy to understand.

Never provide a definitive diagnosis or prescribe medication. 
End by reminding the patient this is not a substitute for a real doctor's evaluation.
"""


def gather_symptoms_node(state: ConversationState) -> ConversationState:
    print("Running gather_symptoms_node...")

    messages = state["messages"]

    # Make sure the system prompt for this stage is set correctly
    system_msg = SystemMessage(content=GATHER_PROMPT)
    full_messages = [system_msg] + [m for m in messages if not isinstance(m, SystemMessage)]

    response = llm.invoke(full_messages)
    reply_text = _extract_text(response)

    # Check if the AI signaled it's ready to move on
    if "[READY_FOR_ASSESSMENT]" in reply_text:
        reply_text = reply_text.replace("[READY_FOR_ASSESSMENT]", "").strip()
        next_stage = "urgency_and_specialty"
    else:
        next_stage = "gathering"

    updated_messages = messages + [AIMessage(content=reply_text)]

    return {
        "messages": updated_messages,
        "stage": next_stage,
        "reply": reply_text,
    }


def urgency_and_specialty_node(state: ConversationState) -> ConversationState:
    print("Running urgency_and_specialty_node...")

    messages = state["messages"]

    conversation_history = [m for m in messages if not isinstance(m, SystemMessage)]

    # Build a plain-text summary of the conversation to use as our search query
    conversation_text = "\n".join([
        m.content for m in conversation_history if isinstance(m, HumanMessage)
    ])

    # Retrieve relevant medical knowledge based on what the patient described
    retrieved_knowledge = retrieve_relevant_knowledge(conversation_text)

    system_prompt_with_context = URGENCY_AND_SPECIALTY_PROMPT + f"""

Here is relevant reference information that may help inform your specialty suggestion:

{retrieved_knowledge}

Use this reference information to help guide your specialty suggestion, but still use your own judgment based on the full conversation.
"""

    system_msg = SystemMessage(content=system_prompt_with_context)

    trigger_msg = HumanMessage(
        content="Based on our conversation so far, please now provide your urgency assessment and specialty suggestion."
    )

    full_messages = [system_msg] + conversation_history + [trigger_msg]

    response = llm.invoke(full_messages)
    reply_text = _extract_text(response)

    updated_messages = messages + [AIMessage(content=reply_text)]

    return {
        "messages": updated_messages,
        "stage": "done",
        "reply": reply_text,
    }


def _extract_text(response) -> str:
    """Helper to extract plain text from Gemini's response."""
    if isinstance(response.content, str):
        return response.content
    text_parts = [
        part["text"] for part in response.content
        if isinstance(part, dict) and part.get("type") == "text"
    ]
    return " ".join(text_parts)


def route_after_gathering(state: ConversationState) -> Literal["gathering", "urgency_and_specialty"]:
    """Decides which node to run next, based on the current stage."""
    return state["stage"]


# Build the graph
graph_builder = StateGraph(ConversationState)

graph_builder.add_node("gathering", gather_symptoms_node)
graph_builder.add_node("urgency_and_specialty", urgency_and_specialty_node)

graph_builder.set_entry_point("gathering")

# After "gathering," check the stage to decide: loop back, or move forward
graph_builder.add_conditional_edges(
    "gathering",
    route_after_gathering,
    {
        "gathering": END,   # if still gathering, END this turn (wait for patient's next message)
        "urgency_and_specialty": "urgency_and_specialty",
    }
)

graph_builder.add_edge("urgency_and_specialty", END)

graph = graph_builder.compile()

# Temporary in-memory storage for each patient's conversation state.
# Structure: { "session_id": ConversationState }
# NOTE: resets when the server restarts — we'll persist this properly later.





def run_chat_turn(session_id: str, message: str, patient_id: int) -> dict:
    """Runs one turn of the conversation for a given session, persisting to the database."""

    db = SessionLocal()
    try:
        conversation = db.query(models.Conversation).filter(
            models.Conversation.session_id == session_id
        ).first()

        if conversation is None:
            conversation = models.Conversation(
                session_id=session_id,
                patient_id=patient_id,
                stage="gathering",
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Save the patient's new message to the database
        patient_msg = models.Message(
            conversation_id=conversation.id,
            sender="patient",
            content=message,
        )
        db.add(patient_msg)
        db.commit()

        db_messages = db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).order_by(models.Message.id).all()

        langchain_messages = []
        for m in db_messages:
            if m.sender == "patient":
                langchain_messages.append(HumanMessage(content=m.content))
            else:
                langchain_messages.append(AIMessage(content=m.content))

        state: ConversationState = {
            "messages": langchain_messages,
            "stage": conversation.stage,
            "reply": "",
        }
        updated_state = graph.invoke(state)

        ai_msg = models.Message(
            conversation_id=conversation.id,
            sender="ai",
            content=updated_state["reply"],
        )
        db.add(ai_msg)

        conversation.stage = updated_state["stage"]
        db.commit()

        return {
            "reply": updated_state["reply"],
            "stage": updated_state["stage"],
        }
    finally:
        db.close()