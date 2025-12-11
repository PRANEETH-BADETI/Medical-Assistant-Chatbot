# server/utils/auth_deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database import get_db
from config import SECRET_KEY, ALGORITHM
from schemas.user import TokenData
from models.user import User
import crud.user as crud
from logger import logger

# This tells FastAPI to look for the token in the 'Authorization' header
# 'tokenUrl="auth/login"' tells the /docs UI which endpoint to use to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.

    1. Decodes the JWT token.
    2. Validates the token data.
    3. Fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the email (which we stored in the 'sub' field)
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token decoding error: 'sub' (email) field missing.")
            raise credentials_exception

        token_data = TokenData(email=email)

    except JWTError as e:
        logger.warning(f"JWT Error: {e}")
        raise credentials_exception

    # Get the user from the database
    user = crud.get_user_by_email(db, email=token_data.email)

    if user is None:
        logger.warning(f"Token refers to non-existent user: {token_data.email}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Token refers to inactive user: {user.email}")
        raise HTTPException(status_code=400, detail="Inactive user")

    return user