import requests
import streamlit as st
import os

# --- API URL SETUP ---
api_url_env = os.getenv("API_URL")
if api_url_env:
    API_URL = api_url_env
else:
    try:
        API_URL = st.secrets.get("API_URL", "http://localhost:8000")
    except Exception:
        API_URL = "http://localhost:8000"

# --- AUTH FUNCTIONS ---

def login_api(email, password):
    try:
        response = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Login failed")}
    except Exception as e:
        return {"error": str(e)}

def register_api(email, password):
    """
    Step 1: Request OTP.
    Server sends OTP to email and stores password/OTP in Redis temporarily.
    """
    try:
        response = requests.post(f"{API_URL}/auth/register", json={"email": email, "password": password})
        if response.status_code == 200:
            return response.json() # Expecting {"message": "OTP sent..."}
        else:
            return {"error": response.json().get("detail", "Registration failed")}
    except Exception as e:
        return {"error": str(e)}

def verify_otp_api(email, otp, password):
    """
    Step 2: Verify OTP.
    Server checks OTP and finally creates the user in the database.
    """
    try:
        payload = {
            "email": email,
            "otp": otp,
            "password": password
        }
        response = requests.post(f"{API_URL}/auth/verify", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Verification failed")}
    except Exception as e:
        return {"error": str(e)}

# --- SESSION & CHAT FUNCTIONS (Keep existing) ---

def get_sessions_api(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/chat/sessions", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Failed to fetch sessions: {e}")
        return []

def create_session_api(token, title="New Chat"):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_URL}/chat/sessions",
            json={"title": title},
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to create session: {e}")
        return None

def delete_session_api(session_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        requests.delete(f"{API_URL}/chat/sessions/{session_id}", headers=headers)
        return True
    except Exception:
        return False

def get_session_messages_api(session_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/chat/sessions/{session_id}/messages", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def ask_question_stream(question, session_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        with requests.post(
                f"{API_URL}/ask/{session_id}",
                data={"question": question},
                stream=True,
                headers=headers
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    yield chunk.decode('utf-8')
    except requests.exceptions.RequestException as e:
        yield f"Connection Error: {e}"

def get_session_files_api(session_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{API_URL}/chat/sessions/{session_id}/files", headers=headers)
        return res.json() if res.status_code == 200 else []
    except: return []

def delete_file_api(session_id, file_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        requests.delete(f"{API_URL}/chat/sessions/{session_id}/files/{file_id}", headers=headers)
        return True
    except: return False

def upload_files_api(files, session_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {"session_id": str(session_id)}
        files_payload = [("files", (f.name, f.read(), f.type)) for f in files]

        response = requests.post(
            f"{API_URL}/upload_files/",
            data=data,
            files=files_payload,
            headers=headers
        )
        return response
    except Exception as e:
        return {"error": str(e)}

def check_task_status_api(task_id, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/upload_files/status/{task_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        return {"status": "UNKNOWN"}
    except Exception:
        return {"status": "ERROR"}