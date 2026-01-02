from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import json
from datetime import timedelta
import random
import redis
from fastapi_mail import FastMail, MessageSchema, MessageType

from models.user import User, UserRole
from utils.security import verify_password, create_access_token, get_password_hash # <--- Import get_password_hash
from config import ACCESS_TOKEN_EXPIRE_MINUTES, EMAIL_CONF, CELERY_BROKER_URL
from utils.auth_deps import get_current_user
from database import get_db
import crud.user as crud
import schemas.user as schemas
from logger import logger
from schemas.user import VerifyRequest

# Connect to Redis
redis_client = redis.from_url(CELERY_BROKER_URL)

router = APIRouter(prefix='/auth', tags=["Authentication"])
# Connect to Redis
redis_client = redis.from_url(CELERY_BROKER_URL)

router = APIRouter(prefix='/auth', tags=["Authentication"])


@router.post("/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # 3. Hash the password NOW
    hashed_password = get_password_hash(user.password)

    # 4. Store EVERYTHING in Redis
    # We store a JSON string containing the OTP, Email, and Hashed Password
    signup_data = {
        "email": user.email,
        "password": hashed_password,
        "otp": otp
    }
    redis_client.setex(f"signup_{user.email}", 600, json.dumps(signup_data))
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