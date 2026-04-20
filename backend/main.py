"""
main.py - FastAPI application for the Smart Citizen Complaint Analyzer.

API Endpoints:
  POST /register           - Register a new user account
  POST /login              - Login and receive JWT token
  GET  /me                 - Get current user info
  POST /submit_complaint   - Submit a new complaint (authenticated users)
  GET  /my_complaints      - Get current user's complaints
  GET  /get_complaints     - Retrieve all complaints (admin only)
  GET  /analyze            - Get aggregate statistics (admin only)
  POST /speech_to_text     - Convert audio to text

Pages:
  /                        - Login page
  /user                    - User portal
  /admin                   - Admin dashboard
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import jwt
import bcrypt

from database import engine, get_db, Base
from models import Complaint, User
from nlp_processor import nlp
from priority import calculate_priority
from speech import speech_to_text

# ─── Configuration ───────────────────────────────────────────────────────────
JWT_SECRET = "smart-citizen-complaint-analyzer-secret-key-2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# ─── Create tables ───────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Citizen Complaint Analyzer",
    description="AI-powered citizen complaint classification and priority system",
    version="2.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ─── Auth Helpers ────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hashed one."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user_id: int, username: str, role: str) -> str:
    """Create a JWT token for the given user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token. Please login again.")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Extract and validate the current user from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated. Please login.")
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


# ─── Startup: Create default admin ──────────────────────────────────────────

@app.on_event("startup")
def create_default_admin():
    """Create a default admin account if none exists."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin_user)
            db.commit()
            print("🔑 Default admin account created (username: admin, password: admin123)")
        else:
            print("🔑 Admin account already exists.")
    finally:
        db.close()


# ─── Page Routes ─────────────────────────────────────────────────────────────

@app.get("/")
async def serve_login():
    """Serve the login page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/user")
async def serve_user_portal():
    """Serve the user portal page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "user.html"))


@app.get("/admin")
async def serve_admin_dashboard():
    """Serve the admin dashboard page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Register a new citizen user account."""
    # Validate input
    if len(username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")

    # Check if username exists
    existing = db.query(User).filter(User.username == username.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken.")

    # Create user
    user = User(
        username=username.strip().lower(),
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.username, user.role)

    return {
        "status": "success",
        "message": "Account created successfully.",
        "token": token,
        "user": user.to_dict(),
    }


@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Login with username and password. Returns JWT token."""
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_token(user.id, user.username, user.role)

    return {
        "status": "success",
        "message": "Login successful.",
        "token": token,
        "user": user.to_dict(),
    }


@app.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {"status": "success", "user": user.to_dict()}


# ─── Complaint Routes ───────────────────────────────────────────────────────

@app.post("/submit_complaint")
async def submit_complaint(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new citizen complaint (authenticated users only).
    Accepts either text or an audio file (which will be transcribed).
    The complaint is analyzed, classified, and stored in the database.
    """
    complaint_text = text

    # If audio file is provided, convert to text
    if audio and not complaint_text:
        try:
            audio_bytes = await audio.read()
            complaint_text = speech_to_text(audio_bytes, audio.filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

    if not complaint_text or not complaint_text.strip():
        raise HTTPException(status_code=400, detail="Please provide complaint text or an audio file.")

    complaint_text = complaint_text.strip()

    # Step 1: NLP Processing — classify and get sentiment
    nlp_result = nlp.process(complaint_text)

    # Step 2: Priority Scoring
    priority_result = calculate_priority(
        text=complaint_text,
        category=nlp_result["category"],
        sentiment=nlp_result["sentiment"],
        db=db,
    )

    # Step 3: Store in database
    complaint = Complaint(
        text=complaint_text,
        category=nlp_result["category"],
        priority=priority_result["priority"],
        priority_score=priority_result["priority_score"],
        sentiment=nlp_result["sentiment"],
        user_id=user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {
        "status": "success",
        "message": "Complaint submitted and analyzed successfully.",
        "data": {
            **complaint.to_dict(),
            "priority_breakdown": priority_result["breakdown"],
        },
    }


@app.get("/my_complaints")
async def my_complaints(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's own complaints, most recent first."""
    complaints = (
        db.query(Complaint)
        .filter(Complaint.user_id == user.id)
        .order_by(Complaint.timestamp.desc())
        .all()
    )
    return {
        "status": "success",
        "count": len(complaints),
        "data": [c.to_dict() for c in complaints],
    }


@app.get("/get_complaints")
async def get_complaints(
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority (High/Medium/Low)"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve all complaints (admin only), with optional filters.
    Results are ordered by most recent first.
    """
    query = db.query(Complaint)

    if category:
        query = query.filter(Complaint.category == category)
    if priority:
        query = query.filter(Complaint.priority == priority)

    complaints = query.order_by(Complaint.timestamp.desc()).all()

    return {
        "status": "success",
        "count": len(complaints),
        "data": [c.to_dict() for c in complaints],
    }


@app.get("/analyze")
async def analyze(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get aggregate statistics about all complaints (admin only).
    Returns total count, category distribution, and priority distribution.
    """
    total = db.query(Complaint).count()

    # Category distribution
    category_counts = (
        db.query(Complaint.category, func.count(Complaint.id))
        .group_by(Complaint.category)
        .all()
    )
    categories = {cat: count for cat, count in category_counts}

    # Priority distribution
    priority_counts = (
        db.query(Complaint.priority, func.count(Complaint.id))
        .group_by(Complaint.priority)
        .all()
    )
    priorities = {pri: count for pri, count in priority_counts}

    # Recent complaints (last 5)
    recent = db.query(Complaint).order_by(Complaint.timestamp.desc()).limit(5).all()

    return {
        "status": "success",
        "data": {
            "total_complaints": total,
            "category_distribution": categories,
            "priority_distribution": priorities,
            "recent_complaints": [c.to_dict() for c in recent],
        },
    }


@app.post("/speech_to_text")
async def convert_speech(
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    Convert an uploaded audio file to text using speech recognition.
    Returns the transcribed text.
    """
    try:
        audio_bytes = await audio.read()
        text = speech_to_text(audio_bytes, audio.filename)
        return {"status": "success", "text": text}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ─── Run Server ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Smart Citizen Complaint Analyzer...")
    print("📍 Open http://localhost:8000 in your browser\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
