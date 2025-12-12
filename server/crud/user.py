from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from utils.security import get_password_hash
from logger import logger

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    logger.info(f"Hashing password for user {user.email}")
    hashed_password = get_password_hash(user.password)

    db_user = User(
        email = user.email,
        hashed_password = hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_id(db: Session, user_id: int):
    '''Fetches a single user by their ID.'''
    return db.query(User).filter(User.id == user_id).first()