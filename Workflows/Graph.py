from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver

from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI
from Prompts import Prompts
from Workflows.BasicToolNode import BasicToolNode
from ChatModels.TokenManager import TokenManager 
from Workflows.Tools import tools

# Define the state of the graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

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

def create_graph(memory: MemorySaver):
    # Get the LLM Chat Model
    llm = CiscoAzureOpenAI(token_manager=TokenManager()).get_llm()

    # Create the state graph
    graph_builder = StateGraph(State)

    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        system_prompt_message = {"role": "system", "content": Prompts.system_prompt}

        if "messages" not in state or not isinstance(state["messages"], list):
            state["messages"] = []

        messages = [system_prompt_message] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    # Add the nodes to the graph
    graph_builder.add_node("chatbot", chatbot)

    # Create the tool node
    tool_node = BasicToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    # Add the conditional edges
    graph_builder.add_conditional_edges("chatbot", route_tools)

    # Add the nodes to the graph
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    graph = graph_builder.compile(checkpointer=memory)

    return graph