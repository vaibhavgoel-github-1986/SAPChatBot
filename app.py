import streamlit as st
import time
from Utilities.GetDependencies import get_dependencies
from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI
from ChatModels.TokenManager import TokenManager
from pprint import pformat
from langchain.chains import LLMChain
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# Define State with message management
class State(TypedDict):
    messages: Annotated[list, add_messages]  # Append new messages to the list


# Initialize StateGraph
graph_builder = StateGraph(State)

# Get the LLM Chat Model
llm = CiscoAzureOpenAI(
    token_manager=TokenManager(),
).get_llm()


# Define the chatbot node
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()


# Streamed response generator with full context
def response_generator():
    for event in graph.stream({"messages": st.session_state.messages}):
        for value in event.values():
            yield value["messages"][-1].content


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
                response_container.markdown("".join(response_lines))

            # Combine streamed response into a single string
            final_response = "".join(response_lines)

        # Add assistant response to chat history
        add_message("assistant", final_response)


# Run the app
if __name__ == "__main__":
    main()
