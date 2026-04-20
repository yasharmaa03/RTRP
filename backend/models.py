"""
models.py - SQLAlchemy ORM model for the Complaint table.
Stores complaint text, AI-generated category, priority, scores, and timestamps.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database import Base


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
        }
