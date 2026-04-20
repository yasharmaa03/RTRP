"""
priority.py - Priority scoring system for citizen complaints.

Calculates priority based on three factors:
  1. Urgency: keyword matching for urgent/emergency words
  2. Frequency: number of similar complaints in the database (simulated)
  3. Sentiment: negative sentiment → higher priority

Formula: priority_score = urgency_score + frequency_score + sentiment_score
Score range: 0 to 10
  - High:   score >= 7
  - Medium: score >= 4
  - Low:    score < 4
"""

import random

# Keywords that indicate urgency (each worth points)
URGENT_KEYWORDS = {
    # High urgency (3 points each)
    "emergency": 3, "urgent": 3, "danger": 3, "dangerous": 3,
    "life-threatening": 3, "critical": 3, "death": 3, "dying": 3,
    "fire": 3, "flood": 3, "collapse": 3, "electrocution": 3,

    # Medium urgency (2 points each)
    "accident": 2, "injured": 2, "injury": 2, "broken": 2,
    "severe": 2, "serious": 2, "immediate": 2, "asap": 2,
    "health hazard": 2, "toxic": 2, "contaminated": 2,

    # Low urgency (1 point each)
    "problem": 1, "issue": 1, "complaint": 1, "bad": 1,
    "poor": 1, "damaged": 1, "not working": 1, "failed": 1,
    "leaking": 1, "blocked": 1, "overflowing": 1, "missing": 1,
}


def calculate_urgency_score(text: str) -> float:
    """
    Score urgency based on keyword matching.
    Returns a score from 0 to 4 (capped).
    """
    text_lower = text.lower()
    score = 0
    for keyword, weight in URGENT_KEYWORDS.items():
        if keyword in text_lower:
            score += weight
    # Cap at 4
    return min(score, 4.0)


def calculate_frequency_score(category: str, db=None) -> float:
    """
    Score based on how many similar complaints exist.
    In a real system, this would query the DB for complaints in the same category.
    For this prototype, we simulate with a small random factor + base count.
    Returns a score from 0 to 3.
    """
    if db:
        from models import Complaint
        count = db.query(Complaint).filter(Complaint.category == category).count()
        # Scale: 0-2 complaints = 0, 3-5 = 1, 6-10 = 2, >10 = 3
        if count > 10:
            return 3.0
        elif count > 5:
            return 2.0
        elif count > 2:
            return 1.0
        else:
            return 0.5
    # Fallback: simulate
    return round(random.uniform(0.5, 2.0), 1)


def calculate_sentiment_score(sentiment: float) -> float:
    """
    Convert sentiment polarity to a priority score.
    More negative sentiment → higher priority score.
    Sentiment range: -1 (very negative) to +1 (very positive)
    Returns a score from 0 to 3.
    """
    # Invert and scale: sentiment of -1 → score 3, sentiment of +1 → score 0
    score = (1 - sentiment) * 1.5
    return min(round(score, 2), 3.0)


def calculate_priority(text: str, category: str, sentiment: float, db=None) -> dict:
    """
    Calculate overall priority for a complaint.

    Args:
        text: The complaint text
        category: Classified category of the complaint
        sentiment: Sentiment polarity score (-1 to +1)
        db: Optional database session for frequency lookup

    Returns:
        dict with priority label, numeric score, and component breakdown
    """
    urgency = calculate_urgency_score(text)
    frequency = calculate_frequency_score(category, db)
    sentiment_score = calculate_sentiment_score(sentiment)

    # Total priority score (0 to 10)
    total = round(urgency + frequency + sentiment_score, 2)

    # Map to label
    if total >= 7:
        label = "High"
    elif total >= 4:
        label = "Medium"
    else:
        label = "Low"

    return {
        "priority": label,
        "priority_score": total,
        "breakdown": {
            "urgency": urgency,
            "frequency": frequency,
            "sentiment": sentiment_score,
        },
    }
