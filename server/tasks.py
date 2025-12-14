# server/tasks.py

import os
from pathlib import Path
from tqdm.auto import tqdm
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from logger import logger
import google.generativeai as genai
from PIL import Image
import io
import uuid
from pinecone import ServerlessSpec

from celery_app import celery
from config import (
    pc, embed_model, PINECONE_INDEX_NAME, GOOGLE_API_KEY,
    PINECONE_API_KEY, GLOBAL_KB_NAMESPACE
)

# Import Models
from models.user import User, UserRole
import models.chat
from models.chat import ChatSession
import models.file
import models.message
from models.file import UploadedFile
from database import SessionLocal


@celery.task(name="process_documents_task")
def process_documents_task(file_paths: list, session_id: int):
    """
    Processes files.
    - ADMIN uploads go to GLOBAL_KB_NAMESPACE.
    - USER uploads go to session_{id} namespace.
    """
    logger.info(f"Task started for session_id {session_id}")

    db = SessionLocal()

    # 1. Determine Namespace based on User Role
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            logger.error(f"Session {session_id} not found.")
            return

        user = session.user
        if user.role == UserRole.ADMIN:
            namespace = GLOBAL_KB_NAMESPACE
            logger.info(f"User is ADMIN. Uploading to Global Knowledge Base: '{namespace}'")
        else:
            namespace = f"session_{session_id}"
            logger.info(f"User is Standard. Uploading to Private Session: '{namespace}'")

    except Exception as e:
        logger.error(f"Error fetching session/user: {e}")
        db.close()
        return

    # 2. Process Files
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )
        genai.configure(api_key=GOOGLE_API_KEY)
        vision_model = genai.GenerativeModel("gemini-2.5-flash")

        # Create Index check (omitted for brevity, same as before)

        for file_path in file_paths:
            try:
                if not os.path.exists(file_path): continue

                filename = Path(file_path).name
                file_uuid = str(uuid.uuid4())[:8]
                pinecone_id_prefix = f"doc_{file_uuid}"

                chunks = []

                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with open(file_path, "rb") as f:
                        img_data = f.read()
                    image = Image.open(io.BytesIO(img_data))
                    resp = vision_model.generate_content(["Extract text and describe:", image])
                    doc = Document(page_content=resp.text, metadata={"source": filename})
                    chunks = text_splitter.split_documents([doc])
                else:
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                    chunks = text_splitter.split_documents(docs)

                for i, chunk in enumerate(chunks):
                    chunk.metadata["source"] = filename
                    chunk.metadata["file_uuid"] = file_uuid
                    chunk.id = f"{pinecone_id_prefix}_{i}"

                # Upload to determined namespace
                vectorstore = PineconeVectorStore(
                    index_name=PINECONE_INDEX_NAME,
                    embedding=embed_model,
                    pinecone_api_key=PINECONE_API_KEY,
                    namespace=namespace
                )
                vectorstore.add_documents(chunks, ids=[c.id for c in chunks])

                # Record in DB
                db_file = UploadedFile(
                    session_id=session_id,
                    filename=filename,
                    pinecone_id_prefix=file_uuid
                )
                db.add(db_file)
                db.commit()

                logger.info(f"Saved {filename} to namespace {namespace}")

                try:
                    os.remove(file_path)
                except:
                    pass

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    finally:
        db.close()