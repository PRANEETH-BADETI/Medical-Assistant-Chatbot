# client/components/chatUI.py

import streamlit as st
from utils.api import ask_question_stream


def render_chat():
    st.subheader("💬 Chat with MediBot")

    # Add a logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    # Handle new user input
    user_input = st.chat_input("Type your question....")
    if user_input:
        token = st.session_state.get("token")
        if not token:
            st.error("Session expired. Please log in again.")
            return

        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            full_response = ""
            assistant_message = st.chat_message("assistant").empty()

            # Pass token to streaming API
            for chunk in ask_question_stream(user_input, token):
                full_response += chunk
                assistant_message.markdown(full_response + "▌")

            assistant_message.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})