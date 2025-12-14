from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User, UserRole
from models.file import UploadedFile
from models.chat import ChatSession
from utils.auth_deps import get_current_user
from config import pc, PINECONE_INDEX_NAME, GLOBAL_KB_NAMESPACE
from logger import logger

router = APIRouter(prefix="/chat", tags=["files"])


@router.get("/sessions/{session_id}/files")
def get_session_files(session_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UploadedFile).filter(UploadedFile.session_id == session_id).all()


@router.delete("/sessions/{session_id}/files/{file_id}")
def delete_file(session_id: int, file_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Get File record
    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.session_id == session_id
    ).first()

    if not file_record:
        raise HTTPException(404, "File not found")

    # 2. Determine Namespace (Check Session Owner Role)
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    namespace = f"session_{session_id}"

    if session.user.role == UserRole.ADMIN:
        namespace = GLOBAL_KB_NAMESPACE

    # 3. Delete Vectors from Pinecone
    try:
        index = pc.Index(PINECONE_INDEX_NAME)
        index.delete(
            filter={"file_uuid": file_record.pinecone_id_prefix},
            namespace=namespace
        )
        logger.info(f"Deleted vectors for {file_record.filename} from {namespace}")

    except Exception as e:
        logger.error(f"Pinecone delete error: {e}")

    # 4. Delete from DB
    db.delete(file_record)
    db.commit()
    return {"message": "File deleted"}