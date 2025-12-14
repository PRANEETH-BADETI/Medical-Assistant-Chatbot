import streamlit as st
from utils.api import upload_files_api, get_session_files_api, delete_file_api, check_task_status_api
import time


def render_uploader():
    session_id = st.session_state.get("active_session_id")
    token = st.session_state.get("token")

    if not session_id or not token:
        st.info("Select a chat to manage files.")
        return

    # --- 1. File List (Persistent) ---
    st.subheader("📂 Files in this Chat")

    # We use a container so we can refresh just this part if needed
    file_list_container = st.container()

    # Fetch files
    files = get_session_files_api(session_id, token)

    with file_list_container:
        if files:
            for f in files:
                col1, col2 = st.columns([0.8, 0.2])
                col1.text(f"📄 {f['filename']}")
                if col2.button("🗑️", key=f"del_file_{f['id']}"):
                    delete_file_api(session_id, f['id'], token)
                    st.rerun()
        else:
            st.caption("No files uploaded yet.")

    st.markdown("---")

    # --- 2. Upload Area ---
    uploaded_files = st.file_uploader(
        "Add new documents", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True
    )

    if st.button("Upload & Process"):
        if uploaded_files:
            with st.spinner("Initiating upload..."):
                # 1. Start the Upload
                resp = upload_files_api(uploaded_files, session_id, token)

                # Check if we got a valid JSON response (requests object)
                if hasattr(resp, "status_code") and resp.status_code == 202:
                    resp_data = resp.json()
                    task_id = resp_data.get("task_id")

                    if task_id:
                        # 2. Poll for Completion
                        progress_text = st.empty()
                        progress_bar = st.progress(0)

                        status = "PENDING"
                        while status not in ["SUCCESS", "FAILURE"]:
                            status_data = check_task_status_api(task_id, token)
                            status = status_data.get("status", "PENDING")

                            if status == "PENDING":
                                progress_text.text("⏳ Queued...")
                                progress_bar.progress(10)
                            elif status == "STARTED":
                                progress_text.text("⚙️ Processing vectors (this may take a moment)...")
                                progress_bar.progress(50)
                            elif status == "SUCCESS":
                                progress_bar.progress(100)
                                progress_text.success("✅ Complete!")
                                time.sleep(1)
                                break
                            elif status == "FAILURE":
                                progress_text.error("❌ Processing Failed.")
                                break

                            time.sleep(1)  # Wait 1 second before checking again

                        # 3. Refresh to show new files
                        st.rerun()
                    else:
                        st.warning("Upload started, but could not track progress.")
                else:
                    st.error("Upload failed. Please check server logs.")