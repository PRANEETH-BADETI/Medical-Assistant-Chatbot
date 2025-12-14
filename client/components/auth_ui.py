# client/components/auth_ui.py

import streamlit as st
from utils.api import login_api, register_api  # <--- Removed get_history_api
import time


def render_auth():
    """Renders the Login and Register tabs."""
    st.title("🔐 Welcome to MediBot")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if email and password:
                with st.spinner("Logging in..."):
                    result = login_api(email, password)
                    if "access_token" in result:
                        # 1. Save token to session state
                        st.session_state["token"] = result["access_token"]
                        st.success("Login successful!")

                        # Note: We NO LONGER fetch history here.
                        # The app will rerun, and the Sidebar will fetch the list of sessions.

                        time.sleep(1)
                        st.rerun()  # Refresh app to load the main UI
                    else:
                        st.error(result.get("error", "Login failed"))
            else:
                st.warning("Please enter both email and password")

    with tab2:
        st.subheader("Create an Account")
        new_email = st.text_input("Email", key="reg_email")
        new_pass = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Register"):
            if new_email and new_pass:
                with st.spinner("Creating account..."):
                    result = register_api(new_email, new_pass)
                    if "id" in result:
                        st.success("Account created! Please log in.")
                    else:
                        st.error(result.get("error", "Registration failed"))
            else:
                st.warning("Please fill in all fields")