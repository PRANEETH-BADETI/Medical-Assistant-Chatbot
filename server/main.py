from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.exception_handlers import catch_exception_middleware
from routes.upload_pdfs import router as upload_router
from routes.ask_question import router as ask_router
from routes.chat import router as chat_router
from routes.auth import router as auth_router
from logger import logger
from config import *
from database import engine, Base
from routes.files import router as files_router

# Import all models so Alembic/SQLAlchemy knows about them
import models.user
import models.message
import models.chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VitaAI API", description="API for VitaAI Medical Assistant")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.middleware("http")(catch_exception_middleware)

app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(files_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting VitaAI API")