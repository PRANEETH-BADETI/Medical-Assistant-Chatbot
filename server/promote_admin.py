from database import SessionLocal
from models.user import User, UserRole
import models.chat
import models.message
import models.file

# CHANGE THIS to your email
TARGET_EMAIL = "praneethbadeti@gmail.com"

db = SessionLocal()
try:
    # Now SQLAlchemy knows about User, ChatSession, AND Message
    user = db.query(User).filter(User.email == TARGET_EMAIL).first()

    if user:
        user.role = UserRole.ADMIN
        db.commit()
        print(f"✅ Success! {TARGET_EMAIL} is now an ADMIN.")
        print("Everything you upload now goes to the Global Knowledge Base.")
    else:
        print("❌ User not found. Register in the UI first!")
finally:
    db.close()