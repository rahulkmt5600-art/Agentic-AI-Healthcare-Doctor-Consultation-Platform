from langgraph.graph import StateGraph, END
from typing import TypedDict


# This defines the "shape" of data that flows through our graph.
# Think of it as a shared notebook that gets passed from node to node,
# where each node can read from it and write new information into it.
class GraphState(TypedDict):
    name: str
    greeting: str


# A "node" is just a normal Python function.
# It receives the current state, and returns updates to merge into it.
def greet_node(state: GraphState) -> GraphState:
    print("Running greet_node...")
    return {"greeting": f"Hello, {state['name']}!"}


def farewell_node(state: GraphState) -> GraphState:
    print("Running farewell_node...")
    return {"greeting": state["greeting"] + " Goodbye!"}


# Build the graph
graph_builder = StateGraph(GraphState)

# Register our two nodes
graph_builder.add_node("greet", greet_node)
graph_builder.add_node("farewell", farewell_node)

# Define the flow: start at "greet", then go to "farewell", then end
graph_builder.set_entry_point("greet")
graph_builder.add_edge("greet", "farewell")
graph_builder.add_edge("farewell", END)

# Compile it into something we can actually run
graph = graph_builder.compile()

# Run it with some starting data
result = graph.invoke({"name": "Rahul", "greeting": ""})

print("\nFinal result:", result)