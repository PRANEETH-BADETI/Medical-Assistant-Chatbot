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
from config import pc, embed_model, PINECONE_INDEX_NAME, GOOGLE_API_KEY, PINECONE_API_KEY, GLOBAL_KB_NAMESPACE
from models.user import User, UserRole

def load_vectorstore(user: User, file_paths: list = None):
    logger.info("Starting load_vectorstore")

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

    # Initialize Gemini Vision
    genai.configure(api_key=GOOGLE_API_KEY)
    vision_model = genai.GenerativeModel("gemini-1.5-flash-latest")

    # Correct and robust way to check if an index exists
    try:
        index_names = [index['name'] for index in pc.list_indexes()]
        if PINECONE_INDEX_NAME not in index_names:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=768,  # Correct dimension for Google's embedding model
                metric="cosine",
                spec=ServerlessSpec(cloud='aws', region='us-east-1')  # Example spec
            )
            logger.info(f"Created new Pinecone index: {PINECONE_INDEX_NAME}")
    except Exception as e:
        logger.error(f"Error checking for or creating Pinecone index: {e}")
        raise

    if file_paths:
        for file_path in tqdm(file_paths, desc="Processing files"):
            try:
                # Determine file type based on extension
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with open(file_path, "rb") as f:
                        # Read the file bytes into a BytesIO stream in memory
                        image_stream = io.BytesIO(f.read())
                    image = Image.open(image_stream)
                    response = vision_model.generate_content(
                        ["Describe this medical image in detail", image]
                    )
                    description = response.text
                    doc = Document(
                        page_content=description,
                        metadata={"source": f"{Path(file_path).name}_image"}
                    )
                    chunks = text_splitter.split_documents([doc])
                else:
                    # Process PDF
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                    chunks = text_splitter.split_documents(documents)
                    for i, chunk in enumerate(chunks):
                        chunk.metadata["source"] = f"{Path(file_path).name}_{i}"

                # Embed and store in Pinecone
                vectorstore = PineconeVectorStore(
                    index_name=PINECONE_INDEX_NAME,
                    embedding=embed_model,
                    pinecone_api_key=PINECONE_API_KEY,
                    namespace=namespace
                )
                vectorstore.add_documents(chunks)
                logger.info(f"Processed and stored {file_path}")
            except Exception as e:
                logger.exception(f"Failed to process {file_path}: {str(e)}")
                raise

    logger.info("Vectorstore loaded successfully")