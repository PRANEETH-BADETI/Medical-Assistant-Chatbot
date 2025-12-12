from fastapi import APIRouter, UploadFile, File, Depends, status
from fastapi.responses import JSONResponse
from logger import logger
from typing import List
from modules.pdf_handlers import save_uploaded_files  # Import the save function
from utils.auth_deps import get_current_user
from models.user import User

from tasks import process_documents_task

router = APIRouter(prefix="/upload_files", tags=["upload"])

@router.post("/")
async def upload_files(files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Received uploaded files from user: {current_user.email}")

        # Save files to a temporary directory and get their paths
        file_paths = save_uploaded_files(files)

        # Pass the list of file paths to the vector store loader
        process_documents_task.delay(file_paths=file_paths, user_id=current_user.id)

        logger.info(f"Task dispatched for user {current_user.email} with {len(file_paths)} files.")

        # Return an "Accepted" response immediately
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"message": "Files received and are being processed in the background."}
        )

    except Exception as e:
        logger.exception(f"Error during file upload: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})