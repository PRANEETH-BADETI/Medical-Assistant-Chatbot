from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import json
from datetime import timedelta
import random
import redis
from fastapi_mail import FastMail, MessageSchema, MessageType

from models.user import User, UserRole
from utils.security import verify_password, create_access_token, get_password_hash
from config import ACCESS_TOKEN_EXPIRE_MINUTES, EMAIL_CONF, CELERY_BROKER_URL
from utils.auth_deps import get_current_user
from database import get_db
import crud.user as crud
import schemas.user as schemas
from logger import logger
from schemas.user import VerifyRequest

# --- Connect to Redis ---
redis_client = redis.from_url(CELERY_BROKER_URL)

router = APIRouter(prefix='/auth', tags=["Authentication"])


@router.post("/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user already exists in DB
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # 3. Hash the password NOW (so we don't store plain text in Redis)
    hashed_password = get_password_hash(user.password)

    # 4. Store EVERYTHING in Redis (Temporary Holding Area)
    # We store a JSON string containing the OTP, Email, and Hashed Password
    # Expires in 10 minutes (600 seconds)
    signup_data = {
        "email": user.email,
        "password": hashed_password,
        "otp": otp
    }
    redis_client.setex(f"signup_{user.email}", 600, json.dumps(signup_data))

    # 5. Send Email
    message = MessageSchema(
        subject="Your VitaAI Verification Code",
        recipients=[user.email],
        body=f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color:#2EC4B6;">VitaAI Verification</h2>

        <p>Hello,</p>
        <p>Your One-Time Password (OTP) for verifying your VitaAI account is:</p>

        <h1 style="letter-spacing: 5px; color: #333;">{otp}</h1>

        <p>If you did not request this verification, please ignore this email.</p>
        <p style="font-size: 12px; color: gray;">This code expires in 10 minutes.</p>
    </div>
    """,
        subtype=MessageType.html
    )
    fm = FastMail(EMAIL_CONF)
    await fm.send_message(message)

    return {"message": "OTP sent to your email. Please verify."}


@router.post("/verify")
def verify_otp(req: VerifyRequest, db: Session = Depends(get_db)):
    # 1. Retrieve data from Redis
    redis_data = redis_client.get(f"signup_{req.email}")

    if not redis_data:
        raise HTTPException(status_code=400, detail="OTP expired or invalid. Please register again.")

    # 2. Parse the JSON data
    signup_data = json.loads(redis_data)
    stored_otp = signup_data.get("otp")
    hashed_password = signup_data.get("password")

    # 3. Verify OTP
    if stored_otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # 4. OTP Matches -> FINALLY Create User in Postgres
    # We create the user manually since we already hashed the password
    new_user = User(
        email=req.email,
        hashed_password=hashed_password,
        role=UserRole.USER,
        is_active=True,
        is_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 5. Clean up Redis
    redis_client.delete(f"signup_{req.email}")

    return {"message": "Account verified successfully!"}


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")

    user = crud.get_user_by_email(db, email=form_data.username)

    # 1. Check Password
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. CRITICAL: Check Verification Status
    if not user.is_verified:
        logger.warning(f"Unverified login attempt: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please verify your account first."
        )

    # 3. Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value},
                                       expires_delta=access_token_expires)

    logger.info(f"Successful login for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserDisplay)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user