import streamlit as st
from utils.api import ask_question_stream


def render_chat():
    st.subheader("💬 Chat with your assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    user_input = st.chat_input("Type your question....")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            full_response = ""
            assistant_message = st.chat_message("assistant").empty()
            for chunk in ask_question_stream(user_input):
                full_response += chunk
                assistant_message.write(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})