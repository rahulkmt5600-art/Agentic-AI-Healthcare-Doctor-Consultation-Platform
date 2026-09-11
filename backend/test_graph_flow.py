from graph import graph
from langchain_core.messages import HumanMessage

# Simulate a conversation, one message at a time, reusing the same state
state = {"messages": [], "stage": "gathering", "reply": ""}

def send(message: str):
    global state
    state["messages"].append(HumanMessage(content=message))
    state = graph.invoke(state)
    print(f"\nPatient: {message}")
    print(f"AI: {state['reply']}")
    print(f"[stage: {state['stage']}]")


send("mere kamar me dard hai, 3 din se")
send("bukhar nahi hai, lekin uthne baithne me dikkat hoti hai")
send("koi chot nahi lagi, bas aise hi start hua")
send("subah uthte waqt zyada hota hai, aur neend thodi kharab ho rahi hai")
send("pehle kabhi aisa nahi hua, aur main zyada der baith kar office ka kaam karta hoon")