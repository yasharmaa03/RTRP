"""
nlp_processor.py - NLP module for text cleaning, complaint classification, and sentiment analysis.

Uses:
  - TF-IDF + Multinomial Naive Bayes for category classification
  - TextBlob for sentiment analysis
  - Built-in training data (no external dataset required)
"""

import re
import string
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# ─── Built-in Training Data ──────────────────────────────────────────────────
# Small labeled dataset for each complaint category.
# The classifier learns from these examples at startup.

TRAINING_DATA = [
    # Water Issues
    ("No water supply in our area for 3 days", "Water Issue"),
    ("Water pipeline is broken and leaking on the road", "Water Issue"),
    ("Contaminated water coming from the tap", "Water Issue"),
    ("Low water pressure in the morning hours", "Water Issue"),
    ("Sewage water is mixing with drinking water", "Water Issue"),
    ("Water tanker has not arrived for a week", "Water Issue"),
    ("Borewell in our colony has dried up", "Water Issue"),
    ("Water is brown and smells bad", "Water Issue"),
    ("Water supply is irregular and unpredictable", "Water Issue"),
    ("Open drainage overflowing into water supply", "Water Issue"),
    ("Water meter is faulty and showing wrong readings", "Water Issue"),
    ("No water connection in newly built houses", "Water Issue"),

    # Electricity Issues
    ("Frequent power cuts in our locality", "Electricity Issue"),
    ("Electricity pole is damaged and sparking", "Electricity Issue"),
    ("Street lights are not working in our area", "Electricity Issue"),
    ("High voltage fluctuations damaging appliances", "Electricity Issue"),
    ("Electricity bill is too high and seems incorrect", "Electricity Issue"),
    ("Transformer is making loud noise and overheating", "Electricity Issue"),
    ("Power outage for over 12 hours with no update", "Electricity Issue"),
    ("Exposed electrical wires near the playground", "Electricity Issue"),
    ("No electricity connection in our new building", "Electricity Issue"),
    ("Street lights stay on during the day wasting electricity", "Electricity Issue"),
    ("Electricity meter has stopped working", "Electricity Issue"),
    ("Frequent tripping of circuit breaker in our block", "Electricity Issue"),

    # Road Issues
    ("Huge potholes on the main road causing accidents", "Road Issue"),
    ("Road is completely damaged after heavy rain", "Road Issue"),
    ("No speed breakers near the school zone", "Road Issue"),
    ("Road construction has been pending for months", "Road Issue"),
    ("Footpath is broken and unusable for pedestrians", "Road Issue"),
    ("Road divider is missing causing wrong-side driving", "Road Issue"),
    ("Manhole cover is missing on the main road", "Road Issue"),
    ("New road has already developed cracks", "Road Issue"),
    ("Waterlogging on the road during monsoon", "Road Issue"),
    ("Unpaved road causing dust pollution in the area", "Road Issue"),
    ("Broken bridge railing is dangerous for vehicles", "Road Issue"),
    ("Road markings have faded completely", "Road Issue"),

    # Sanitation Issues
    ("Garbage is not being collected for a week", "Sanitation Issue"),
    ("Open dumping of waste near residential area", "Sanitation Issue"),
    ("Public toilets are in very bad condition", "Sanitation Issue"),
    ("Stray animals feeding on uncollected waste", "Sanitation Issue"),
    ("Drainage is blocked causing bad smell", "Sanitation Issue"),
    ("No dustbins available in the market area", "Sanitation Issue"),
    ("Overflowing garbage bins on every street corner", "Sanitation Issue"),
    ("Construction debris dumped on the roadside", "Sanitation Issue"),
    ("Dead animal carcass lying on the street for days", "Sanitation Issue"),
    ("Foul smell coming from the nearby garbage dump", "Sanitation Issue"),
    ("Mosquito breeding due to stagnant dirty water", "Sanitation Issue"),
    ("Sewage system is completely blocked in our lane", "Sanitation Issue"),

    # Traffic Issues
    ("Traffic signal is not working at the main crossing", "Traffic Issue"),
    ("Heavy traffic congestion during peak hours", "Traffic Issue"),
    ("Illegal parking blocking the entire street", "Traffic Issue"),
    ("No traffic police present at busy intersection", "Traffic Issue"),
    ("Reckless driving by auto-rickshaws in school zone", "Traffic Issue"),
    ("Traffic jam due to ongoing construction work", "Traffic Issue"),
    ("Zebra crossing is faded and not visible", "Traffic Issue"),
    ("No pedestrian signal at the busy junction", "Traffic Issue"),
    ("Trucks parked on residential streets overnight", "Traffic Issue"),
    ("Broken traffic light causing confusion and accidents", "Traffic Issue"),
    ("Speed limit signs are missing on the highway stretch", "Traffic Issue"),
    ("Two-wheelers driving on footpath to avoid traffic", "Traffic Issue"),
]


# ─── NLP Pipeline ────────────────────────────────────────────────────────────

class NLPProcessor:
    """Handles text cleaning, category classification, and sentiment analysis."""

    def __init__(self):
        """Train the classifier on startup using the built-in dataset."""
        texts = [t[0] for t in TRAINING_DATA]
        labels = [t[1] for t in TRAINING_DATA]

        # TF-IDF vectorizer + Naive Bayes classifier pipeline
        self.classifier = Pipeline([
            ("tfidf", TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),    # Use unigrams and bigrams
                max_features=5000,
            )),
            ("clf", MultinomialNB(alpha=0.1)),
        ])
        self.classifier.fit(texts, labels)
        print("✅ NLP classifier trained successfully on built-in dataset.")

    def clean_text(self, text: str) -> str:
        """Clean input text by removing special characters and extra whitespace."""
        # Remove URLs
        text = re.sub(r"http\S+|www\S+", "", text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,!?'-]", "", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def classify(self, text: str) -> str:
        """Classify complaint text into one of 5 categories."""
        cleaned = self.clean_text(text)
        prediction = self.classifier.predict([cleaned])[0]
        return prediction

    def get_sentiment(self, text: str) -> float:
        """
        Analyze sentiment polarity of the text.
        Returns a float from -1.0 (very negative) to +1.0 (very positive).
        """
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def process(self, text: str) -> dict:
        """
        Full NLP processing pipeline:
        1. Clean text
        2. Classify into category
        3. Analyze sentiment
        Returns a dict with category and sentiment.
        """
        cleaned = self.clean_text(text)
        category = self.classify(cleaned)
        sentiment = self.get_sentiment(cleaned)
        return {
            "cleaned_text": cleaned,
            "category": category,
            "sentiment": round(sentiment, 3),
        }


# Create a singleton instance for use across the app
nlp = NLPProcessor()
