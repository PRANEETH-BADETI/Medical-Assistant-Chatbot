from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.exception_handlers import catch_exception_middleware
from routes.upload_pdfs import router as upload_router
from routes.ask_question import router as ask_router
from logger import logger
from config import *
from database import engine, Base
import models.user
from routes.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Medical Assistant API", description="API for AI Medical Assistant Chatbot")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Middleware for exception handling
app.middleware("http")(catch_exception_middleware)

# Routers
app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(auth_router)

# Startup event for debugging
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Medical Assistant API")
    logger.debug(f"PINECONE_INDEX_NAME: {PINECONE_INDEX_NAME}")
    # The clients are already initialized via config.py import.