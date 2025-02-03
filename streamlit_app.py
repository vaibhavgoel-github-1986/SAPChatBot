import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from Prompts import GreetingMsg

from Workflows.UTMWorkflow import get_graph

# Set page config (has to be done before any Streamlit command)
st.set_page_config(
    page_title="SAP ChatBot",
    layout="centered",  # "wide",
    initial_sidebar_state="collapsed",
)

# Check if reset flag is set
reset_memory = st.session_state.pop("reset_memory", False)
graph = get_graph(
    reset_memory=reset_memory
)  # ✅ Reset memory only if button was clicked


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
            for event in graph.stream(
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
            yield (str(error))


def initial_greeting():
    if not any(msg.role == "assistant" for msg in st.session_state.messages):

        with st.chat_message("assistant"):
            st.markdown(GreetingMsg.greeting_msg)

        add_message(AIMessage(content=GreetingMsg.greeting_msg, role="assistant"))


def get_total_token_usage():
    # Fetches token usage statistics from the graph state.
    try:
        snapshot = graph.get_state(get_config())
        token_usage = snapshot.values.get("messages", [])[-1].response_metadata.get(
            "token_usage", {}
        )
        return token_usage.get("total_tokens", "0")
    except Exception as e:
        st.toast(f":red[Error fetching token usage:] {e}")
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
                st.toast(
                    ":green[Logging Activated]", icon=":material/steppers:"
                )
            else:
                st.toast(
                    ":red[Logging Deactivated]", icon=":material/steppers:"
                )

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
        if st.button(":material/restart_alt: Reset Chat Memory"):
            st.session_state["reset_memory"] = True  # Set flag for reset
            # Reset all the session state variables
            st.session_state.clear()
            # st.session_state.messages = []
            # st.session_state.total_token_usage = 0
            # st.session_state.last_token_usage = 0
            # st.session_state.display_logs_flag = False
            st.rerun()  # Refresh Streamlit page


# Main App
def main():

    st.header("SAP UTM Chat Bot", divider=True)

    # Initialize chat history
    initialize_chat_history()

    # Display chat history
    display_chat_messages()

    # Ensure initial AI greeting is displayed only once per session
    initial_greeting()

    # Streaming User Input
    if prompt := st.chat_input("Message UTM Chat Bot"):

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
