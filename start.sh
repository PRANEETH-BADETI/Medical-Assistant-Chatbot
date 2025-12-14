#!/bin/bash

# Move into the server directory where main.py is
cd server

# 1. Start Celery Worker (Background process)
# --pool=solo is used because we are in a simple container environment
celery -A celery_app worker --loglevel=info --pool=solo &

# 2. Start FastAPI (Main process)
# We must use port 7860 for Hugging Face Spaces
uvicorn main:app --host 0.0.0.0 --port 7860