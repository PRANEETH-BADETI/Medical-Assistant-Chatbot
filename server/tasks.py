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
from pinecone import ServerlessSpec

# Import our Celery app instance
from celery_app import celery

# Import configs and models
from config import (
    pc, embed_model, PINECONE_INDEX_NAME, GOOGLE_API_KEY,
    PINECONE_API_KEY, GLOBAL_KB_NAMESPACE
)
from models.user import User, UserRole
from database import SessionLocal  # Import the session
import crud.user as crud


# This is the @celery.task decorator
@celery.task(name="process_documents_task")
def process_documents_task(file_paths: list, user_id: int):
    """
    Celery task to process and load documents into the vector store.
    This runs in a separate background worker.
    """

    # --- Task-specific logic ---
    db = SessionLocal()
    try:
        user = crud.get_user_by_id(db, user_id)

    finally:
        db.close()

    logger.info(f"Celery task started for user_id {user_id}")

    # --- Task-specific logic ---
    db = SessionLocal()
    user = None
    try:
        # Use the new function we just "added"
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"Task failed: No user found with ID {user_id}")
            return
    finally:
        db.close()

    logger.info(f"Task processing for user: {user.email}")

    # Determine the correct namespace
    if user.role == UserRole.ADMIN:
        namespace = GLOBAL_KB_NAMESPACE
        logger.info(f"User is ADMIN, uploading to '{namespace}' namespace.")
    else:
        namespace = f"user_{user.id}"
        logger.info(f"User is USER, uploading to private '{namespace}' namespace.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    genai.configure(api_key=GOOGLE_API_KEY)
    vision_model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        index_names = [index['name'] for index in pc.list_indexes()]
        if PINECONE_INDEX_NAME not in index_names:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            logger.info(f"Created new Pinecone index: {PINECONE_INDEX_NAME}")
    except Exception as e:
        logger.error(f"Error checking for or creating Pinecone index: {e}")
        return

    if file_paths:
        for file_path in tqdm(file_paths, desc=f"Processing files for {namespace}"):
            try:
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with open(file_path, "rb") as f:
                        image_stream = io.BytesIO(f.read())
                    image = Image.open(image_stream)
                    response = vision_model.generate_content(
                        ["Extract all text, data, and numerical values from this medical image and Describe this medical image in detail", image]
                    )
                    description = response.text
                    doc = Document(
                        page_content=description,
                        metadata={"source": f"{Path(file_path).name}_image"}
                    )
                    chunks = text_splitter.split_documents([doc])
                else:
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                    chunks = text_splitter.split_documents(documents)
                    for i, chunk in enumerate(chunks):
                        chunk.metadata["source"] = f"{Path(file_path).name}_{i}"

                vectorstore = PineconeVectorStore(
                    index_name=PINECONE_INDEX_NAME,
                    embedding=embed_model,
                    pinecone_api_key=PINECONE_API_KEY,
                    namespace=namespace
                )
                vectorstore.add_documents(chunks)
                logger.info(f"Processed and stored {file_path} in namespace '{namespace}'")

                # Clean up the file after processing
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {file_path}: {e}")

            except Exception as e:
                logger.exception(f"Failed to process {file_path}: {str(e)}")
                # Continue to next file

    logger.info(f"Celery task finished for user_id {user_id}")