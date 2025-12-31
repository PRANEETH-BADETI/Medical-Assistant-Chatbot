import streamlit as st
import time
from utils.api import login_api, register_api, verify_otp_api


def render_auth():
    """Renders ONLY the standard Login/Register tabs."""
    st.title("🔐 Welcome to VitaAI")

    # Initialize verification state
    if "verification_mode" not in st.session_state:
        st.session_state.verification_mode = False
    if "temp_reg_email" not in st.session_state:
        st.session_state.temp_reg_email = ""
    if "temp_reg_pass" not in st.session_state:
        st.session_state.temp_reg_pass = ""

    # --- 1. Standard Email/Password Tabs ---
    tab1, tab2 = st.tabs(["Login", "Register"])

    # --- LOGIN TAB ---
    with tab1:
        st.subheader("Login with Email")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if email and password:
                with st.spinner("Logging in..."):
                    result = login_api(email, password)
                    if "access_token" in result:
                        st.session_state["token"] = result["access_token"]
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result.get("error", "Login failed"))
            else:
                st.warning("Please enter both email and password")

    # --- REGISTER TAB ---
    with tab2:
        st.subheader("Create an Account")

        # CASE A: OTP VERIFICATION MODE
        if st.session_state.verification_mode:
            st.info(f"An OTP has been sent to **{st.session_state.temp_reg_email}**.")

            otp_code = st.text_input("Enter 6-digit OTP", key="otp_input")

            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                if st.button("Verify OTP"):
                    if otp_code:
                        with st.spinner("Verifying..."):
                            res = verify_otp_api(
                                st.session_state.temp_reg_email,
                                otp_code,
                                st.session_state.temp_reg_pass
                            )

                            if "error" not in res:
                                st.success("Account verified! Please Login.")
                                st.session_state.verification_mode = False
                                st.session_state.temp_reg_email = ""
                                st.session_state.temp_reg_pass = ""
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(res["error"])
                    else:
                        st.warning("Please enter the OTP.")

            with col2:
                if st.button("Cancel / Resend"):
                    st.session_state.verification_mode = False
                    st.rerun()

        # CASE B: INITIAL REGISTRATION
        else:
            new_email = st.text_input("Email", key="reg_email")
            new_pass = st.text_input("Password", type="password", key="reg_pass")

            if st.button("Register"):
                if new_email and new_pass:
                    with st.spinner("Sending OTP..."):
                        result = register_api(new_email, new_pass)

                        if "error" not in result:
                            st.session_state.verification_mode = True
                            st.session_state.temp_reg_email = new_email
                            st.session_state.temp_reg_pass = new_pass
                            st.success("OTP sent! Check your email.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(result.get("error"))
                else:
                    st.warning("Please fill in all fields")