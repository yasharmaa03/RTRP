"""
main.py - FastAPI application for the Smart Citizen Complaint Analyzer.

API Endpoints:
  POST /submit_complaint  - Submit a new complaint (text or audio)
  GET  /get_complaints    - Retrieve complaints with optional filters
  GET  /analyze           - Get aggregate statistics
  POST /speech_to_text    - Convert audio to text
"""

import os
import sys

# Add backend directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from database import engine, get_db, Base
from models import Complaint
from nlp_processor import nlp
from priority import calculate_priority
from speech import speech_to_text

# ─── Create tables ───────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Citizen Complaint Analyzer",
    description="AI-powered citizen complaint classification and priority system",
    version="1.0.0",
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


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Smart Citizen Complaint Analyzer API — visit /docs for API documentation"}


@app.post("/submit_complaint")
async def submit_complaint(
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Submit a new citizen complaint.
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


@app.get("/get_complaints")
async def get_complaints(
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority (High/Medium/Low)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all complaints, with optional filters by category and priority.
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
async def analyze(db: Session = Depends(get_db)):
    """
    Get aggregate statistics about all complaints.
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
async def convert_speech(audio: UploadFile = File(...)):
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
