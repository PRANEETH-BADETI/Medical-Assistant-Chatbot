# client/app.py

import streamlit as st
from components.auth_ui import render_auth
from components.upload import render_uploader
from components.history_download import render_history_download
from components.chatUI import render_chat

st.set_page_config(page_title="AI Medical Assistant", layout="wide")

# Check if user is logged in
if "token" not in st.session_state:
    # --- State 1: Not Logged In ---
    render_auth()
else:
    # --- State 2: Logged In (The Main App) ---
    st.sidebar.title("🩺 Medical Assistant")

    render_uploader()
    render_chat()

    st.sidebar.markdown("---")
    render_history_download()