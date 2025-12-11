from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User

from datetime import timedelta
from utils.security import verify_password, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from utils.auth_deps import get_current_user
from database import get_db
import crud.user as crud
import schemas.user as schemas
from logger import logger

router = APIRouter(prefix='/auth', tags=["Authentication"])

@router.post("/register", response_model=schemas.UserDisplay)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register new user: {user.email}")

    db_user = crud.get_user_by_email(db, email = user.email)
    if db_user:
        logger.warning(f"Registration failed: Email already registered - {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = crud.create_user(db=db, user=user)
    logger.info(f"Successfully registered new user: {new_user.email} (ID: {new_user.id})")

    return new_user


@router.post("/login", response_model = schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")

    user = crud.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data = {"sub": user.email, "role": user.role.value},
                                       expires_delta = access_token_expires)

    logger.info(f"Successful login for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserDisplay)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the details of the currently logged-in user.
    """
    # The 'get_current_user' dependency has already validated
    # the token and fetched the user from the DB.
    # We just return it.
    return current_user