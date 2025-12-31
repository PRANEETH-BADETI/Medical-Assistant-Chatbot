from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

from models.user import User, UserRole
from datetime import timedelta
from utils.security import verify_password, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from utils.auth_deps import get_current_user
from database import get_db
import crud.user as crud
import schemas.user as schemas
from logger import logger
import random
import redis
from fastapi_mail import FastMail, MessageSchema, MessageType
from config import EMAIL_CONF, CELERY_BROKER_URL
from schemas.user import VerifyRequest

# Connect to Redis
redis_client = redis.from_url(CELERY_BROKER_URL)

router = APIRouter(prefix='/auth', tags=["Authentication"])

# Get Google Client ID from environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


@router.post("/google", response_model=schemas.Token)
def google_login(token_data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Verifies a Google ID Token and returns an access token.
    """
    token = token_data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    try:
        # 1. Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo['email']
        logger.info(f"Google login attempt for: {email}")

        # 2. Check if user exists in your DB
        user = crud.get_user_by_email(db, email=email)

        if not user:
            logger.info(f"Creating new user from Google: {email}")
            user = User(
                email=email,
                hashed_password=None,  # No password for Google users
                role=UserRole.USER,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 3. Generate JWT Token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value},
            expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        logger.warning("Invalid Google Token provided")
        raise HTTPException(status_code=400, detail="Invalid Google Token")
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # 3. Store OTP in Redis (Expires in 5 minutes)
    redis_client.setex(f"otp_{user.email}", 300, otp)

    # 4. Send Email (UPDATED SUBJECT)
    message = MessageSchema(
        subject="Your VitaAI Verification Code",
        recipients=[user.email],
        body=f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color:#2EC4B6;">VitaAI Account Verification</h2>
        
        <p>Hello,</p>

        <p>Your One-Time Password (OTP) for verifying your VitaAI account is:</p>

        <h1 style="letter-spacing: 4px;">{otp}</h1>

        <p>If you did not request this verification, please ignore this email.</p>

        <br>
        <p style="font-size: 12px; color: gray;">
            This is an automated message. Please do not reply.
        </p>
    </div>
    """,
        subtype=MessageType.html
    )
    fm = FastMail(EMAIL_CONF)
    await fm.send_message(message)

    return {"message": "OTP sent to your email. Please verify."}


@router.post("/verify")
def verify_otp(req: VerifyRequest, db: Session = Depends(get_db)):
    # 1. Retrieve OTP from Redis
    stored_otp = redis_client.get(f"otp_{req.email}")

    if not stored_otp or stored_otp.decode('utf-8') != req.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # 2. OTP Matches -> Create User Now
    new_user = crud.create_user(db=db, user=schemas.UserCreate(email=req.email, password=req.password))

    # 3. Mark as verified
    new_user.is_verified = True
    db.commit()

    # 4. Clean up Redis
    redis_client.delete(f"otp_{req.email}")

    return {"message": "Account verified successfully!"}


@router.post("/login", response_model=schemas.Token)
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
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value},
                                       expires_delta=access_token_expires)

    logger.info(f"Successful login for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserDisplay)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user