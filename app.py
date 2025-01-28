import json
import streamlit as st
import random
import time

from Tools.GetDependencies import get_dependencies

st.title("SAP Chat Bot")


# Streamed response emulator
def response_generator():
    dependencies = get_dependencies(class_name=st.session_state.messages[-1]["content"])
    response = json.dumps(dependencies, indent=4) 
    
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input(""):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):    
        response = st.write_stream(response_generator())

    st.session_state.messages.append({"role": "assistant", "content": response})
