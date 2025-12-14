import streamlit as st
from utils.api import get_sessions_api, create_session_api, delete_session_api
import time


def render_sidebar():
    st.sidebar.title("🩺 MediBot")

    token = st.session_state.get("token")
    if not token:
        return

    # --- 1. New Chat Button ---
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        new_session = create_session_api(token)
        if new_session:
            st.session_state.active_session_id = new_session["id"]
            # Clear messages so the UI reloads cleanly
            st.session_state.messages = []
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("History")

    # --- 2. Load Sessions ---
    sessions = get_sessions_api(token)

    # Initialize active session if not set
    if "active_session_id" not in st.session_state and sessions:
        st.session_state.active_session_id = sessions[0]["id"]
    elif "active_session_id" not in st.session_state and not sessions:
        # No sessions? Create one automatically for good UX
        new_session = create_session_api(token)
        if new_session:
            st.session_state.active_session_id = new_session["id"]
            st.rerun()

    # --- 3. Render Session List ---
    for sess in sessions:
        # Use columns to put the Delete button next to the name
        col1, col2 = st.sidebar.columns([0.8, 0.2])

        # Style the active button differently (simulated by checking ID)
        is_active = (st.session_state.get("active_session_id") == sess["id"])
        label = f"📂 {sess['title']}" if is_active else sess['title']

        with col1:
            if st.button(label, key=f"sess_{sess['id']}", use_container_width=True):
                st.session_state.active_session_id = sess["id"]
                st.session_state.messages = []  # Force reload of messages
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"del_{sess['id']}"):
                delete_session_api(sess["id"], token)
                # If we deleted the active one, clear the state
                if is_active:
                    del st.session_state.active_session_id
                st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()