from pydantic import ValidationError
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.callbacks import get_openai_callback
from Prompts import GreetingMsg

from datetime import datetime
import time
import pytz
import re
 
from Workflows.Tools import tools
from Workflows.Graph import create_graph

# Set page config (has to be done before any Streamlit command)
st.set_page_config(
    page_title="SAP AI Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure all session state variables are initialized
# Step 1: Ensure "memory" is initialized first
if "memory" not in st.session_state:
    st.session_state["memory"] = MemorySaver()

# Step 2: Now initialize other session variables, using memory
for var, default in {
    "total_token_usage": 0,
    "last_token_usage": 0,
    "show_logs": False,
    "login_time": time.time(),
    "graph": create_graph(st.session_state["memory"]),  # Now memory is available
}.items():
    if var not in st.session_state:
        st.session_state[var] = default


def check_and_reinstantiate_graph():
    current_time = time.time()
    elapsed_time = current_time - st.session_state["login_time"]
    if elapsed_time >= 3600:  # 60 minutes * 60 seconds
        st.session_state["graph"] = create_graph(st.session_state["memory"])
        st.session_state["login_time"] = current_time  # Reset login time
        st.toast(":green[oAuth Token was refreshed]", icon=":material/refresh:")


# Override with Custom CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_current_timestamp():

    # Format HH:MM:SS
    return datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%H:%M:%S")


def get_time_html(current_pst_time):
    # HTML to display timestamp in a compact, small format
    html = f"""
    <div id="timestamp-div" 
        style="display: flex; 
               justify-content: flex-end; 
               font-size: 12px; 
               color: gray; ">{current_pst_time}</div>
    """

    return html


# Helper: Initialize chat history in session state
def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []


def extract_code_blocks(text):
    """
    Splits the LLM response into alternating text and code segments.
    Handles edge cases where code may appear first, consecutively, or not at all.
    """
    pattern = (
        r"```(?:\w+)?\n(.*?)```"  # Matches code blocks enclosed in triple backticks
    )
    raw_parts = re.split(pattern, text, flags=re.DOTALL)

    structured_parts = []
    is_code = text.startswith("```")  # Check if the response starts with code

    for part in raw_parts:
        part_type = "code" if is_code else "text"
        structured_parts.append({"type": part_type, "content": part.strip()})
        is_code = not is_code  # Flip between text and code

    return structured_parts  # Returns structured list


# Helper: Display chat messages
def display_chat_messages():
    # Display existing chat history
    for message in st.session_state.messages:
        with st.chat_message(message.role):
            # content_parts = extract_code_blocks(message.content)
            # for content in content_parts:
            #     if content["type"] == "text":
            #         st.markdown(content["content"])  # Display normal text
            #     else:
            #         st.code(body=content["content"], language="abap", line_numbers=True)
            st.markdown(message.content)
            st.html(get_time_html(message.additional_kwargs["time"]))


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

    show_logs = kwargs.get("show_logs")

    with st.spinner("Processing..."):

        try:
            with get_openai_callback() as cb:
                for event in st.session_state.graph.stream( 
                    {"messages": [{"role": role, "content": prompt}]},
                    config=config,
                    stream_mode="values",
                ):
                    if "messages" in event and event["messages"]:
                        message = event["messages"][-1]
                        if isinstance(message, HumanMessage):
                            print(f"\nUser Message: {message.content}")
                            continue  # Skip user messages

                        elif isinstance(message, AIMessage):
                            if message.content:
                                print(f"\nAI Message: {message.content}")
                                yield message.content

                            elif message.tool_calls:
                                for tool_call in message.tool_calls:
                                    markdown_text = f":green[Calling Tool:]\n\n```abap\n{(tool_call['name'])}\n{(tool_call['args'])}\n```"
                                    print(f"\nAI Tool Call: {markdown_text}")
                                    if show_logs:
                                        yield markdown_text

                        elif isinstance(message, ToolMessage):
                            if message.content:
                                print(f"\nTool Message: {message.content}")
                                if "\\n" in message.content:
                                    # Convert to a proper string (removes escaped backslashes)
                                    formatted_string = message.content.replace(
                                        "\\n", "\n"
                                    )
                                    markdown_text = f":green[Tool Output:]\n\n```abap\n{formatted_string}\n```"
                                    print(f"\nTool Message Output having ABAP Code")                                    
                                    if show_logs:
                                        yield markdown_text

            st.session_state.total_token_usage = cb.total_tokens

        except Exception as error:
            print(f"\nException caught `response_generator`")

            # Check if error has 'args' and it's a dictionary
            if hasattr(error, "args") and len(error.args) > 0:
                yield str(error.args[0])
            else:
                yield "Some exception was caught in `response_generator`"


def initial_greeting():  # Display initial greeting message
    if not any(msg.role == "assistant" for msg in st.session_state.messages):

        with st.chat_message("assistant"):
            st.markdown(GreetingMsg.greeting_msg)
            st.html(get_time_html(get_current_timestamp()))

        add_message(
            AIMessage(
                content=GreetingMsg.greeting_msg,
                role="assistant",
                additional_kwargs={"time": get_current_timestamp()},
            )
        )


def get_total_token_usage():
    # Fetches token usage statistics from the graph state.
    try:
        snapshot = st.session_state.graph.get_state(get_config())
        if snapshot:
            response_metadata = snapshot.values.get("messages", [])[
                -1
            ].response_metadata
            if response_metadata:
                token_usage = response_metadata.get("token_usage", {})
                if token_usage:
                    # st.toast(f"Total Token Usage:{token_usage}")
                    return token_usage["total_tokens"]
            else:
                st.toast(f":red[Error fetching token usage:] {str(e)}")
                return 0
    except Exception as e:
        st.toast(f":red[Error fetching token usage:] {str(e)}")
        return 0


def add_side_bar():

    # Adding SideBar for App Settings
    with st.sidebar.container(border=True):
        st.caption(":material/settings: **Settings**")

        # Store the user’s choice persistently
        show_logs = st.toggle(f"Enable Logs")

        # Update only if the value changes
        if show_logs != st.session_state.show_logs:
            st.session_state.show_logs = show_logs  # Persist state

            # Show toast only when the toggle changes energy_savings_leaf
            if show_logs:
                st.toast(":green[Logging Activated]", icon=":material/steppers:")
            else:
                st.toast(":red[Logging Deactivated]", icon=":material/steppers:")

    with st.sidebar.container(border=False):
        # Add a separator
        st.write("") 
        
    with st.sidebar.container(border=True):
        if st.session_state.total_token_usage >= 0:
            # Add Token Usage Metrics
            st.metric(
                label=":blue[Token Usage]",
                value=st.session_state.total_token_usage,
                delta=st.session_state.total_token_usage
                - st.session_state.last_token_usage,
                delta_color="normal",
                border=False,
            )

    with st.sidebar.container(border=False):
        # Add a separator
        st.write("")
    
    with st.sidebar.container(border=True):
        st.caption(":material/settings: **Manage History**")
        # Reset Button
        if st.button(":material/restart_alt: Clear Chat History", type="secondary"):
            st.session_state["reset_memory"] = True  # Set flag for reset
            # Reset all the session state variables
            st.session_state.clear()
            st.toast(":green[Chat history was cleared]", icon=":material/ink_eraser:")
            st.rerun()  # Refresh Streamlit page

# Main App
def main():

    # Check and reinstantiate graph after 1 hour
    check_and_reinstantiate_graph()

    # Initialize chat history
    initialize_chat_history()

    # Setting Header
    st.header(":blue[SAP ABAP Unit Testing AI Agent]", divider=True)

    # Display chat history
    display_chat_messages()

    # Ensure initial AI greeting is displayed only once per session
    initial_greeting()

    # Streaming User Input
    if prompt := st.chat_input("Message AI Agent"):

        # Update the last token usage for Delta Calculation
        st.session_state.last_token_usage = st.session_state.total_token_usage

        # Add user message to chat history
        add_message(
            HumanMessage(
                content=prompt,
                role="user",
                additional_kwargs={"time": get_current_timestamp()},
            )
        )

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            st.html(get_time_html(get_current_timestamp()))

        # Generate assistant response
        with st.chat_message("assistant"):  # ,avatar=":material/smart_toy:"):
            response_container = st.empty()
            response_lines = []

            for line in response_generator(
                "user",
                prompt,
                show_logs=st.session_state.show_logs,
            ):
                response_lines.append(line)
                response_container.markdown("  \n\n".join(response_lines))

            # Combine streamed response into a single string
            final_response = "  \n\n".join(response_lines)

            # Store AI response
            add_message(
                AIMessage(
                    content=final_response,
                    role="assistant",
                    additional_kwargs={"time": get_current_timestamp()},
                )
            )

            st.html(get_time_html(get_current_timestamp()))

    # Add a side bar for app settings
    add_side_bar()


# Run the app
if __name__ == "__main__":
    main()
