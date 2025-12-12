# client/components/upload.py

import streamlit as st
from utils.api import upload_files_api
import time


def render_uploader():
    st.sidebar.header("Upload Medical Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDFs/Images", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True
    )

    if st.sidebar.button("Process Files"):
        token = st.session_state.get("token")  # Get token

        if uploaded_files and token:
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()

            for i, file in enumerate(uploaded_files):
                status_text.write(f"Processing {file.name}...")

                # Pass token to API
                response = upload_files_api([file], token)

                if isinstance(response, dict) and "error" in response:
                    status_text.error(f"Error: {response['error']}")
                    st.stop()
                else:
                    # Handle the 202 Accepted response from Celery
                    if response.status_code == 202:
                        status_text.success(f"Queued: {file.name}")
                    else:
                        status_text.success(f"Uploaded: {file.name}")

                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                time.sleep(0.1)

            st.sidebar.success("All files sent for processing!")
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
        elif not token:
            st.sidebar.error("You must be logged in.")
        else:
            st.sidebar.warning("Please upload files first.")