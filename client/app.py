import streamlit as st
from components.auth_ui import render_auth
from components.upload import render_uploader
from components.sidebar import render_sidebar
from components.chatUI import render_chat

st.set_page_config(page_title="AI Medical Assistant", layout="wide")

if "token" not in st.session_state:
    render_auth()
else:
    # 1. Render the Sidebar (Manages Sessions & Navigation)
    render_sidebar()

    # 2. Main Area Layout
    # We can put the uploader in an expander at the top or keep it simple
    with st.expander("📂 Upload Documents", expanded=False):
        render_uploader()

    # 3. Render the Chat Interface
    render_chat()