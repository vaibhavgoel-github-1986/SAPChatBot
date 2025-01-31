import streamlit as st
from Workflows.SAPAgent import get_graph
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

# Global variable to store the graph
graph = get_graph()


# Define State with message management
class State(TypedDict):
    messages: Annotated[list, add_messages]  # Append new messages to the list


# Helper: Initialize chat history in session state
def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []


# Helper: Display chat messages
def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# Helper: Add a message to the chat history
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})


# Streamed response generator using LangGraph
def response_generator():
    """
    Streams responses from the chatbot graph with required config.
    """
    config = {"configurable": {"thread_id": "1"}}  # Required config

    print("DEBUG: Calling graph.stream() with messages:", st.session_state.messages)

    for event in graph.stream({"messages": st.session_state.messages}, config=config):
        print("DEBUG: Received event from graph.stream():", event)

        # Extract response from correct path
        if "chatbot" in event and "messages" in event["chatbot"]:
            chatbot_messages = event["chatbot"]["messages"]
            if chatbot_messages:
                response = chatbot_messages[-1].content  # Extract text response
                print("DEBUG: Extracted response:", response)
                yield response
            else:
                print("DEBUG: No chatbot messages found.")
        else:
            print("DEBUG: Unexpected event format received.")


# Main App
def main():
    st.title("SAP Chat Bot")

    # Initialize chat history
    initialize_chat_history()

    # Display chat history
    display_chat_messages()

    # Accept user input
    if prompt := st.chat_input("What can I help with?"):
        # Add user message to chat history
        add_message("user", prompt)

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            response_container = st.empty()
            response_lines = []

            for line in response_generator():
                response_lines.append(line)
                response_container.markdown("\n".join(response_lines))

            # Combine streamed response into a single string
            final_response = "\n".join(response_lines)

        # Add assistant response to chat history
        add_message("assistant", final_response)


# Run the app
if __name__ == "__main__":
    main()
