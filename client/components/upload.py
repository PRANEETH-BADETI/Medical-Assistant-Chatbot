import streamlit as st
from utils.api import upload_files_api
import time


def render_uploader():
    st.sidebar.header("Upload Medical Documents (.PDFs)")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDFs", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True
    )

    if st.sidebar.button("Process and Upload Files"):
        if uploaded_files:
            # Use a progress bar for better user feedback
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()

            for i, file in enumerate(uploaded_files):
                status_text.write(f"Processing file {i + 1}/{len(uploaded_files)}: {file.name}...")

                # Call the API to upload this single file
                response = upload_files_api([file])

                if isinstance(response, dict) and "error" in response:
                    status_text.error(f"Error with {file.name}: {response['error']}")
                    st.stop()  # Stop execution on error
                else:
                    status_text.success(f"Successfully processed {file.name}")

                # Update progress bar
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                time.sleep(0.1)

            st.sidebar.success("All files processed and uploaded successfully!")
            progress_bar.empty()
            status_text.empty()
        else:
            st.sidebar.warning("Please upload files first.")