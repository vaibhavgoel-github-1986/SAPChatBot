# main.py
import pprint
import traceback
from IPython.display import Image, display
import json
import os

from typing import Annotated
from typing_extensions import TypedDict

from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_core.messages import ToolMessage, trim_messages
from langchain_core.tools import tool, ToolException, InjectedToolArg
from langgraph.prebuilt import ToolNode, tools_condition

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

import sys
sys.path.append('/Users/vaibhago/Documents/SAPChatBot')

from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI
from SequentialAgents.BasicToolNode import BasicToolNode
from Utilities.TokenManager import TokenManager
from Tools.GetDependencies import get_dependencies
from Tools.GetSourceCode import get_source_code
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.types import Command, interrupt


# Define the state of the graph
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    tool_outputs: Annotated[list, add_messages]


def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """

    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


# System prompt message
system_prompt_text = """
    You are an expert SAP ABAP Developer specializing in writing ABAP Unit Test Cases. 

    You ar expecting user to provide you with the name of an ABAP Class. 
    Your task is to write a unit test cases for the given ABAP class one method at a time to reduce the complexity of the task.

    You have access to a lot of tools to help you with your task.
    You can ask the user in case you need more information.
    """


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    # return str(human_response)
    return human_response["data"]


# Get the LLM Chat Model
llm = CiscoAzureOpenAI(
    token_manager=TokenManager(),
).get_llm()

# Create the state graph
graph_builder = StateGraph(State)

os.environ["TAVILY_API_KEY"] = "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"
tool = TavilySearchResults(max_results=2)
tools = [tool, get_source_code]

# Define the tools the chatbot will use
# tools = [get_source_code, get_dependencies]

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    system_prompt_message = {"role": "system", "content": system_prompt_text}

    if "messages" not in state or not isinstance(state["messages"], list):
        state["messages"] = []  # Ensure messages is always a list

    messages = [system_prompt_message] + state["messages"]

    return {"messages": [llm_with_tools.invoke(messages)]}


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

config = {"configurable": {"thread_id": "1"}}


def token_usage():
    print("Tokens Usage: ")

    # Get the current state of the graph
    snapshot = graph.get_state(config)
    # Extract token usage details
    token_usage = snapshot.values["messages"][-1].response_metadata["token_usage"]
    # Print input and output tokens
    print(f"Input Tokens: {token_usage['prompt_tokens']}")
    print(f"Output Tokens: {token_usage['completion_tokens']}")
    print(f"Total Tokens: {token_usage['total_tokens']}")
    print(f"Next: {snapshot.next}")

    # Print stored tool outputs
    tool_output = snapshot.values.get("tool_outputs", [])
    print(f"Tool Outputs: {len(tool_output)}")
    for index, tool_output in enumerate(tool_output):
        print(f"{index + 1}. Tool: '{tool_output.name}' was called.")

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
            token_usage()

        except Exception as e:
            print(f"\nException caught in 'start_chatbot'. Error: {str(e)}")
            break  # Stop execution if an error occurs


def get_graph():
    # Get the graph as a Mermaid diagram
    png_data = graph.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png_data)



