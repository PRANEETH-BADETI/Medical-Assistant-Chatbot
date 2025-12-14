import streamlit as st
import json
from utils.api import ask_question_stream, get_session_messages_api


def render_chat():
    token = st.session_state.get("token")
    session_id = st.session_state.get("active_session_id")

    if not session_id:
        st.info("Please create or select a new chat to begin.")
        return

    st.subheader("💬 Chat with MediBot")

    # --- Load History ---
    if st.session_state.get("loaded_session_id") != session_id:
        with st.spinner("Loading history..."):
            history = get_session_messages_api(session_id, token)
            st.session_state.messages = []
            for msg in history:
                st.session_state.messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            st.session_state.loaded_session_id = session_id

    # --- Display Messages ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- Chat Input ---
    user_input = st.chat_input("Type your question....")

    if user_input:
        if not token:
            st.error("Session expired.")
            return

        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            raw_stream_data = ""
            sources_data = []

            for chunk in ask_question_stream(user_input, session_id, token):
                raw_stream_data += chunk

                if "|||SOURCES|||" in raw_stream_data:
                    parts = raw_stream_data.split("|||SOURCES|||")
                    full_response = parts[0]
                    try:
                        if len(parts) > 1 and parts[1].strip():
                            sources_data = json.loads(parts[1])
                    except:
                        pass
                else:
                    full_response = raw_stream_data

                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            # --- Render Sources with Tags ---
            if sources_data:
                with st.expander("📚 Referenced Sources", expanded=False):
                    for idx, source in enumerate(sources_data):
                        score = source.get("score", 0)
                        src_type = source.get("type", "Private")

                        # Determine Badge Style
                        if src_type == "Global":
                            badge_html = "<span style='background-color:#E3F2FD; color:#0D47A1; padding:2px 6px; border-radius:4px; font-size:0.8em;'>🌐 Global</span>"
                        else:
                            badge_html = "<span style='background-color:#F3E5F5; color:#4A148C; padding:2px 6px; border-radius:4px; font-size:0.8em;'>🔒 Private</span>"

                        score_color = "green" if score > 0.7 else "orange" if score > 0.5 else "red"

                        st.markdown(
                            f"**{idx + 1}. {source['source']}** {badge_html} "
                            f"<span style='color:{score_color}; font-size:0.8em;'> "
                            f"(Similarity: {score:.2f})</span>",
                            unsafe_allow_html=True
                        )

        st.session_state.messages.append({"role": "assistant", "content": full_response})