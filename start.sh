#!/bin/bash

# Start the FastAPI server in the background
uvicorn server.main:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit app
streamlit run client/app.py --server.port $PORT