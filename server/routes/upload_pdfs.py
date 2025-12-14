from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from logger import logger
from typing import List
from modules.pdf_handlers import save_uploaded_files
from utils.auth_deps import get_current_user
from models.user import User
from tasks import process_documents_task
from celery.result import AsyncResult  # <--- Import this

router = APIRouter(prefix="/upload_files", tags=["upload"])


@router.post("/")
async def upload_files(
        files: List[UploadFile] = File(...),
        session_id: int = Form(...),
        current_user: User = Depends(get_current_user)
):
    try:
        file_paths = save_uploaded_files(files)

        # Start the task
        task = process_documents_task.delay(file_paths=file_paths, session_id=session_id)

        # Return the Task ID so the frontend can track it
        return JSONResponse(
            status_code=202,
            content={
                "message": "Processing started.",
                "task_id": task.id  # <--- sending this back
            }
        )

    except Exception as e:
        logger.exception(f"Error during file upload: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/status/{task_id}")
async def get_upload_status(task_id: str):
    """
    Checks the status of a Celery background task.
    """
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,  # PENDING, STARTED, SUCCESS, FAILURE
        "result": str(task_result.result) if task_result.ready() else None
    }