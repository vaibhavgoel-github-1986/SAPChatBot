import traceback
# from IPython.display import Image, display
import json
import os

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# import sys
# sys.path.append('/Users/vaibhago/Documents/SAPChatBot')

from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI
from Prompts.SystemPrompts import get_sap_agent_prompt
from SequentialAgents.BasicToolNode import BasicToolNode
from ChatModels.TokenManager import TokenManager
from Tools.GetInterfaceDefinition import GetInterfaceDefinition
from Tools.GetClassDefinition import GetClassDefinition
from Tools.GetMethodCode import GetMethodCode

from langchain_community.tools.tavily_search import TavilySearchResults 

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Use `logger.info()`, `logger.warning()`, `logger.error()`, etc.


# Define the state of the graph
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    # tool_outputs: Annotated[list, add_messages]


def route_tools(state: State):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """

    messages = state.get("messages", [])

    if not messages:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    ai_message = messages[-1]  # Always get the last message

    if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
        return "tools"

    return END


# Define the tools the chatbot will use
# @tool
# def human_assistance(query: str) -> str:
#     """Request assistance from a human."""
#     human_response = interrupt({"query": query})
#     # return str(human_response)
#     return human_response["data"]


# Get the LLM Chat Model
llm = CiscoAzureOpenAI(
    token_manager=TokenManager(),
).get_llm()

# Create the state graph
graph_builder = StateGraph(State)

os.environ["TAVILY_API_KEY"] = "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"

# Define the tools the chatbot will use
tools = [
    TavilySearchResults(max_results=2),
    GetClassDefinition(),
    GetInterfaceDefinition(),
    GetMethodCode(),
]

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    system_prompt_message = {"role": "system", "content": get_sap_agent_prompt()}

    if "messages" not in state or not isinstance(state["messages"], list):
        state["messages"] = []  # Ensure messages is always a list

    messages = [system_prompt_message] + state["messages"]

    return {"messages": [llm_with_tools.invoke(messages)]}

#Configurable is a dictionary that can be passed to the graph to configure the graph
config = {"configurable": {"thread_id": "1"}}

# Add the nodes to the graph
graph_builder.add_node("chatbot", chatbot)

# Create the tool node
tool_node = BasicToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Add the conditional edges
graph_builder.add_conditional_edges("chatbot", route_tools)

# The memory saver will save the state of the graph to disk
memory = MemorySaver()

# Add the nodes to the graph
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile(checkpointer=memory)


def token_usage():
    print("\nTokens Usage: ")

    try:
        # Get the current state of the graph
        snapshot = graph.get_state(config)

        # Extract token usage details safely
        token_usage = snapshot.values.get("messages", [])[-1].response_metadata.get(
            "token_usage", {}
        )

        if not token_usage:
            print("Token usage data not available.")
            return

        # Print input and output tokens
        print(f"Input Tokens: {token_usage.get('prompt_tokens', 'N/A')}")
        print(f"Output Tokens: {token_usage.get('completion_tokens', 'N/A')}")
        print(f"Total Tokens: {token_usage.get('total_tokens', 'N/A')}")
        print(f"Next: {snapshot.next}\n")

    except Exception as e:
        print(f"Error in token_usage(): {e}")


def stream_graph_updates(user_input: str):

    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )

    for event in events:
        if "messages" in event and event["messages"]:
            event["messages"][-1].pretty_print()
        else:
            print("\nNo messages received from the assistant.\n")


def start_chatbot():
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            # Stream the graph updates
            stream_graph_updates(user_input)

            # Print the token usage
            # token_usage()

        except Exception as e:
            print(f"\nException caught in 'start_chatbot'. Error: {str(e)}")
            traceback.print_exc()  # Logs full error details
            continue  # Stop execution if an error occurs

# def generate_graph_image():
#     # Get the graph as a Mermaid diagram
#     png_data = graph.get_graph().draw_mermaid_png()

#     if png_data:
#         with open("graph.png", "wb") as f:
#             f.write(png_data)
#         print("Graph saved as graph.png")
#     else:
#         print("Failed to generate graph visualization.")
        
def get_graph():
    return graph