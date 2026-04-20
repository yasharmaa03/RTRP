"""
models.py - SQLAlchemy ORM models for the Complaint and User tables.
Stores complaint text, AI-generated category, priority, scores, and timestamps.
User model stores authentication credentials and role (user/admin).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """Represents a registered user (citizen or admin)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="user")  # "user" or "admin"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to complaints
    complaints = relationship("Complaint", back_populates="user")

    def to_dict(self):
        """Convert model instance to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Complaint(Base):
    """Represents a citizen complaint stored in the database."""
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    text = Column(Text, nullable=False)                    # Original complaint text
    category = Column(String(50), nullable=False)          # AI-classified category
    priority = Column(String(10), nullable=False)          # High / Medium / Low
    priority_score = Column(Float, default=0.0)            # Numeric priority score
    sentiment = Column(Float, default=0.0)                 # Sentiment polarity (-1 to +1)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # When submitted
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who submitted

    # Relationship to user
    user = relationship("User", back_populates="complaints")

    def to_dict(self):
        """Convert model instance to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "category": self.category,
            "priority": self.priority,
            "priority_score": round(self.priority_score, 2),
            "sentiment": round(self.sentiment, 2),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
        }
