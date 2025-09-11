import requests
import streamlit as st

def upload_files_api(files):
    """Handles the upload of multiple files to the backend API."""
    try:
        files_payload = [
            ("files", (f.name, f.read(), f.type)) for f in files
        ]
        api_url = st.secrets["API_URL"]
        response = requests.post(f"{api_url}/upload_files/", files=files_payload)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def ask_question_stream(question):
    """Streams the chatbot's response from the backend."""
    try:
        api_url = st.secrets["API_URL"]
        with requests.post(f"{api_url}/ask/", data={"question": question}, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk.decode('utf-8')
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with the API: {e}")
        yield f"I'm sorry, I couldn't connect to the server. Please try again later."