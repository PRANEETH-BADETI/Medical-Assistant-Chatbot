# client/utils/api.py

import requests
import streamlit as st
import os

api_url_env = os.getenv("API_URL")

if api_url_env:
    API_URL = api_url_env
else:
    # Fallback to secrets or localhost only if Env Var is missing
    try:
        API_URL = st.secrets.get("API_URL", "http://localhost:8000")
    except Exception:
        API_URL = "http://localhost:8000"

def login_api(email, password):
    """Sends login request and returns the access token."""
    try:
        # OAuth2 expects form data, not JSON
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            return response.json() # Returns {"access_token": "...", "token_type": "bearer"}
        else:
            return {"error": response.json().get("detail", "Login failed")}
    except Exception as e:
        return {"error": str(e)}

def register_api(email, password):
    """Registers a new user."""
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Registration failed")}
    except Exception as e:
        return {"error": str(e)}

def get_history_api(token):
    """Fetches chat history for the logged-in user."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/chat/history", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch history: {e}")
        return []

def upload_files_api(files, token):
    """Uploads files with the auth token."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        files_payload = [
            ("files", (f.name, f.read(), f.type)) for f in files
        ]
        response = requests.post(
            f"{API_URL}/upload_files/",
            files=files_payload,
            headers=headers # <-- Added Header
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def ask_question_stream(question, token):
    """Streams the response with the auth token."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Use a context manager for the request
        with requests.post(
                f"{API_URL}/ask/",
                data={"question": question},
                stream=True,
                headers=headers
        ) as r:
            r.raise_for_status()

            # --- CRITICAL FIX: Set chunk_size=None ---
            # This tells requests to yield data as soon as it arrives
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    yield chunk.decode('utf-8')

    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with the API: {e}")
        yield f"Connection Error: {e}"