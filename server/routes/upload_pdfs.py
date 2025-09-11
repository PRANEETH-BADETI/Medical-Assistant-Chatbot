from fastapi import APIRouter, UploadFile, File
from modules.load_vectorstore import load_vectorstore
from fastapi.responses import JSONResponse
from logger import logger
from typing import List
from modules.pdf_handlers import save_uploaded_files  # Import the save function

router = APIRouter(prefix="/upload_files", tags=["upload"])


@router.post("/")
async def upload_files(files: List[UploadFile] = File(...)):
    try:
        logger.info("Received uploaded files")

        # Save files to a temporary directory and get their paths
        file_paths = save_uploaded_files(files)

        # Pass the list of file paths to the vector store loader
        load_vectorstore(file_paths)

        logger.info("Documents and images added to vectorstore")
        return {"message": "Files processed and vectorstore updated"}
    except Exception as e:
        logger.exception(f"Error during file upload: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})