import os
import shutil
from fastapi import UploadFile
from logger import logger

UPLOAD_DIR = "./uploaded_docs"

def save_uploaded_files(files: list[UploadFile]) -> list[str]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_paths = []
    for file in files:
        temp_path = os.path.join(UPLOAD_DIR, file.filename)
        logger.info(f"Saving file: {temp_path}")
        try:
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            file_paths.append(temp_path)
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {str(e)}")
            raise
    return file_paths