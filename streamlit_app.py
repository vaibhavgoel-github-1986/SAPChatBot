import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from Prompts import GreetingMsg
import streamlit_authenticator as stauth

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI
from Prompts import Prompts
from Workflows.BasicToolNode import BasicToolNode
from ChatModels.TokenManager import TokenManager

from Workflows.Tools import tools

# Set page config (has to be done before any Streamlit command)
st.set_page_config(
    page_title="SAP AI Chat Bot",
    layout="wide", 
    initial_sidebar_state="expanded",
)

# Graph Memory
if "memory" not in st.session_state:
    st.session_state.memory = MemorySaver()
    
# Initialize session state variables only if they are not already set
if "total_token_usage" not in st.session_state:
    st.session_state.total_token_usage = 0

if "last_token_usage" not in st.session_state:
    st.session_state.last_token_usage = 0

# Initialize the toggle in session_state only once
if "display_logs_flag" not in st.session_state:
    st.session_state.display_logs_flag = False

# Override with Custom CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
    
# Helper: Initialize chat history in session state
def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []


# Helper: Display chat messages
def display_chat_messages():
    # Display existing chat history
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            st.markdown(message.content)


# Get the configuration for the graph
def get_config():
    return {"configurable": {"thread_id": "1"}}


# Helper: Add a message to the chat history
def add_message(message):
    st.session_state.messages.append(message)


def set_last_token_usage(tokens: int):
    st.session_state.last_token_usage = tokens


def update_token_usage():
    st.session_state.total_token_usage = get_total_token_usage()


# Streamed response generator using LangGraph
def response_generator(role, prompt, **kwargs):

    # Define the configuration
    config = get_config()

    display_logs_flag = kwargs.get("display_logs_flag")

    with st.spinner("Processing..."):

        try:
            for event in st.session_state.graph.stream(
                # {"messages": st.session_state.messages}, config=config, stream_mode="values"
                {"messages": [{"role": role, "content": prompt}]},
                config=config,
                stream_mode="values",
            ):
                if "messages" in event and event["messages"]:
                    message = event["messages"][-1]
                    if isinstance(message, HumanMessage):
                        continue  # Skip user messages
                    elif isinstance(message, AIMessage):
                        if message.content:
                            yield message.content

                        elif message.tool_calls and display_logs_flag:
                            for tool_call in message.tool_calls:
                                markdown_text = f":green[Calling Tool:]\n\n```abap\n{(tool_call['name'])}\n{(tool_call['args'])}\n```"
                                yield markdown_text

                    elif isinstance(message, ToolMessage):
                        if message.content and display_logs_flag:
                            if "\\n" in message.content:
                                # Convert to a proper string (removes escaped backslashes)
                                formatted_string = message.content.replace("\\n", "\n")
                                markdown_text = f":green[Tool Output:]\n\n```abap\n{formatted_string}\n```"
                                yield markdown_text

        except Exception as error:
            print(f"\nException caught `response_generator`")
            yield (error["message"])


def initial_greeting():
    if not any(msg.role == "assistant" for msg in st.session_state.messages):

        with st.chat_message("assistant"):
            st.markdown(GreetingMsg.greeting_msg)

        add_message(AIMessage(content=GreetingMsg.greeting_msg, role="assistant"))

def create_graph():
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
    graph = graph_builder.compile(checkpointer=st.session_state.memory)
    
    if "graph" not in st.session_state:
        st.session_state.graph = graph

def get_total_token_usage():
    # Fetches token usage statistics from the graph state.
    try:
        snapshot = st.session_state.graph.get_state(get_config())
        if snapshot:
            token_usage = snapshot.values.get("messages", [])[-1].response_metadata.get(
                "token_usage", {}
            )
            # st.toast(f"Total Token Usage:{token_usage.get("total_tokens", "0")}")
            return token_usage.get("total_tokens", "0")
    except Exception as e:
        # st.toast(f":red[Error fetching token usage:] {str(e)}")
        return 0


def add_side_bar():
    # Adding SideBar for App Settings
    with st.sidebar:
        st.caption("**App Settings**")

        # Store the user’s choice persistently
        display_logs_flag = st.toggle(f"Enable Logs")

        # Update only if the value changes
        if display_logs_flag != st.session_state.display_logs_flag:
            st.session_state.display_logs_flag = display_logs_flag  # Persist state

            # Show toast only when the toggle changes
            if display_logs_flag:
                st.toast(":green[Logging Activated]", icon=":material/steppers:")
            else:
                st.toast(":red[Logging Deactivated]", icon=":material/steppers:")

        # Add a divider
        st.divider()

        # Add Token Usage Metrics
        st.metric(
            label="Tokens Usage",
            value=st.session_state.total_token_usage,
            delta=st.session_state.total_token_usage
            - st.session_state.last_token_usage,
            delta_color="normal",
            border=False,
        )

        # Add a divider
        st.divider()

        # Reset Button
        if st.button(":material/restart_alt: Clear Chat History", type="primary"):
            st.session_state["reset_memory"] = True  # Set flag for reset
            # Reset all the session state variables
            st.session_state.clear()
            st.toast(":green[Chat history was cleared]", icon=":material/ink_eraser:")
            st.rerun()  # Refresh Streamlit page


# Main App
def main():

    # Create the Grap and Store it in Session Variable
    create_graph()
    
    # Setting Header
    st.header("ABAP Unit Testing AI Helper", divider=True)
    
    # Initialize chat history
    initialize_chat_history()

    # Display chat history
    display_chat_messages()
        
    # Ensure initial AI greeting is displayed only once per session
    initial_greeting()

    # Streaming User Input
    if prompt := st.chat_input("Message AI Helper"):

        # Update the last token usage for Delta Calculation
        st.session_state.last_token_usage = st.session_state.total_token_usage

        # Add user message to chat history
        add_message(HumanMessage(content=prompt, role="user"))

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):  # ,avatar=":material/smart_toy:"):
            response_container = st.empty()
            response_lines = []
            for line in response_generator(
                "user",
                prompt,
                display_logs_flag=st.session_state.display_logs_flag,
            ):
                response_lines.append(line)
                response_container.markdown("  \n\n".join(response_lines))

            # Combine streamed response into a single string
            final_response = "  \n\n".join(response_lines)

            # Store AI response
            add_message(AIMessage(content=final_response, role="assistant"))

            # Update token usage
            update_token_usage()
    
    # Add a side bar for app settings
    add_side_bar()


# Run the app
if __name__ == "__main__":
    main()
