#!/bin/bash

# 1. Navigate to server directory
cd server

# 2. Start Celery Worker (Background PDF processing)
celery -A celery_app worker --loglevel=info &

# 3. Start FastAPI Backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# 4. Navigate back to root
cd ..

# 5. Start Streamlit Frontend
streamlit run client/app.py --server.port $PORT --server.address 0.0.0.0